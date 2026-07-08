#!/usr/bin/env python3
"""
inbox-id.py — issue stable, conflict-free inbox item IDs.

ID form:  <acronym>-<handle>#<n>   e.g.  acp-ajudd#14

- <acronym>  deterministic short code derived from the repo slug (see acronym()).
- <handle>   the authoring user's handle (namespaces the sequence per user).
- <n>        a monotonically-incrementing counter, per (user, repo).

Why this shape (see session stable-inbox-ids design):
- The counter is namespaced by USER, so two developers can never collide on the
  same number without any coordination — each increments only their own sequence.
- The counter lives LOCALLY (~/.claude/config/inbox-seq.json), never in a shared
  repo, so there is literally no shared file to merge-conflict on. On a given
  machine there is one author, so the file holds that author's per-slug counters.
- The acronym is scoped per repo, so the number reflects that person's activity
  IN that repo, and the ID reads as "who + what repo". The session lives on the
  item's provenance line, not in the ID (keeps the ID short and sayable).

Deferred (refine later): acronym collisions across two different repos, and
multi-user migration. Neither bites for local/single-user use.

Usage:
  inbox-id.py next   --slug <slug> --handle <handle> [--peek]
  inbox-id.py get    --slug <slug>
  inbox-id.py set    --slug <slug> --value <n>
  inbox-id.py acronym --slug <slug>

`next`      prints the next ID and increments the stored counter
            (--peek prints what the next ID WOULD be without incrementing).
`get`       prints the current counter for the slug (0 if none).
`set`       sets the counter (used by one-time migration).
`acronym`   prints just the derived acronym for the slug.
"""
import argparse
import json
import os
import re
import sys
import time

DEFAULT_SEQ_FILE = os.path.expanduser("~/.claude/config/inbox-seq.json")

# Locking for the read-modify-write in `next`. The critical section is a tiny
# JSON read + write (sub-millisecond), so a live holder is never contended for
# long. We bound the wait and degrade gracefully rather than ever block work.
LOCK_RETRIES = 50          # attempts before giving up
LOCK_RETRY_SLEEP = 0.05    # seconds between attempts (~2.5s worst-case wait)
LOCK_STALE_SECONDS = 10.0  # a lock older than this is a crashed run — break it


def acquire_lock(lock_path):
    """Acquire an exclusive lock via atomic O_EXCL create.

    Cross-platform (works under Git Bash on Windows — no POSIX-only fcntl).
    Returns the open fd on success, or None if the lock could not be taken
    within LOCK_RETRIES. A lock file older than LOCK_STALE_SECONDS is assumed
    to be from a crashed run and is broken so a wedged lock never stops work.
    """
    try:
        os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    except OSError:
        return None  # can't even prepare the dir — degrade, never crash
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    for _ in range(LOCK_RETRIES):
        try:
            fd = os.open(lock_path, flags)
            try:
                os.write(fd, str(os.getpid()).encode("ascii"))
            except OSError:
                pass
            return fd
        except OSError:
            # The create failed. On POSIX a held lock is FileExistsError; on
            # Windows a file open/locked by another process can instead surface
            # as PermissionError (and other transient OSErrors happen), so we
            # treat ANY create failure the same: if the lock is stale (crashed
            # holder), break it; otherwise wait briefly and retry. Catching
            # OSError broadly guarantees the lock mechanism never crashes the
            # mint — a wedged lock must degrade to the placeholder, not stop work.
            try:
                age = time.time() - os.path.getmtime(lock_path)
            except OSError:
                age = 0.0  # not present/unreadable — just retry the create
            if age > LOCK_STALE_SECONDS:
                try:
                    os.remove(lock_path)
                except OSError:
                    pass  # another process broke it first, or can't — retry
                continue
            time.sleep(LOCK_RETRY_SLEEP)
    return None


def release_lock(fd, lock_path):
    """Release a lock acquired by acquire_lock(). Best-effort, never raises."""
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        os.remove(lock_path)
    except OSError:
        pass


def acronym(slug):
    """Deterministic short code: first letter of each token in the slug.

    Tokens split on '-', '_', whitespace, and camelCase humps. Single-token
    slugs (which would yield a 1-char acronym) fall back to the first 3 chars.
    Same input always yields the same output on any machine.
    """
    parts = re.split(r"[-_\s]+", slug)
    tokens = []
    for p in parts:
        if not p:
            continue
        sub = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", p)
        tokens.extend(sub if sub else [p])
    letters = "".join(t[0] for t in tokens if t).lower()
    if len(letters) <= 1:
        return slug.lower()[:3]
    return letters


def load_seq(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {}


def save_seq(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description="Issue stable inbox item IDs.")
    ap.add_argument("command", choices=["next", "get", "set", "acronym"])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--handle", default="")
    ap.add_argument("--value", type=int, default=None)
    ap.add_argument("--peek", action="store_true")
    ap.add_argument("--seq-file", default=DEFAULT_SEQ_FILE)
    args = ap.parse_args()

    acr = acronym(args.slug)

    if args.command == "acronym":
        print(acr)
        return

    seq = load_seq(args.seq_file)
    current = int(seq.get(args.slug, 0))

    if args.command == "get":
        print(current)
        return

    if args.command == "set":
        if args.value is None:
            ap.error("set requires --value")
        seq[args.slug] = int(args.value)
        save_seq(args.seq_file, seq)
        print(seq[args.slug])
        return

    # next
    if not args.handle:
        ap.error("next requires --handle")

    # --peek never writes, so it needs no lock — report what the next ID would be.
    if args.peek:
        print(f"{acr}-{args.handle}#{current + 1}")
        return

    # Real mint: serialize the read-modify-write behind an exclusive lock so
    # concurrent callers can't read the same value and collide (or roll the
    # counter backward). Re-read the sequence INSIDE the lock — the pre-lock
    # `current` above may be stale by the time we hold it.
    lock_path = args.seq_file + ".lock"
    fd = acquire_lock(lock_path)
    if fd is None:
        # Lock could not be taken within the bounded wait. Never block work:
        # emit the same placeholder the call sites use when python is absent,
        # and note it on stderr (stdout stays a clean, usable ID).
        sys.stderr.write(
            "inbox-id: could not acquire counter lock; emitted placeholder id "
            "(reconcile the number manually)\n"
        )
        print(f"{acr}-{args.handle}#?")
        return
    try:
        seq = load_seq(args.seq_file)
        n = int(seq.get(args.slug, 0)) + 1
        seq[args.slug] = n
        save_seq(args.seq_file, seq)
    finally:
        release_lock(fd, lock_path)
    print(f"{acr}-{args.handle}#{n}")


if __name__ == "__main__":
    main()
