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

Self-healing counter (acp-ajudd#66): `next` never hands back an ID that
already exists. It seeds from `max(stored-counter, highest #N already present
across the slug's inbox files) + 1`, computed and persisted atomically inside
the mint lock. The scan covers both the top-level `_inbox*.md` (archive + any
legacy/per-session files) and the per-item `_inbox/*.md` dir (the live
consolidated inbox after acp-ajudd#102). So even if a header was hand-written
without calling this script (the bug's other half), the next real mint scans the
files, sees it, and steps past it. The stored counter is still the fast path;
the file scan is the safety net that keeps it honest.

Usage:
  inbox-id.py next   --slug <slug> --handle <handle> [--peek] [--sessions-root <dir>]
  inbox-id.py get    --slug <slug>
  inbox-id.py set    --slug <slug> --value <n>
  inbox-id.py acronym --slug <slug>

`next`      prints the next ID, seeding from max(stored, file-max)+1, and
            persists the counter (--peek prints what the next ID WOULD be
            without persisting).
`get`       prints the current STORED counter for the slug (0 if none) — this
            is the raw counter, not the file-reconciled next value.
`set`       sets the counter (used by one-time migration).
`acronym`   prints just the derived acronym for the slug.
"""
import argparse
import glob
import json
import os
import re
import sys
import time

DEFAULT_SEQ_FILE = os.path.expanduser("~/.claude/config/inbox-seq.json")

# Where a slug's inbox files live, by convention (see inbox-convention.md).
# `next` scans every `_inbox*.md` here for already-issued IDs and seeds the
# counter from the true max, so a hand-written header (a mint that bypassed
# this script) can never make `next` hand back an ID that already exists.
DEFAULT_SESSIONS_ROOT = os.path.expanduser("~/.claude/memory/sessions")

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


def scan_file_max(sessions_root, slug, acr, handle):
    """Highest #N already issued for (acr, handle) across the slug's inbox files.

    Scans, under `<sessions_root>/<slug>/`:
    - every `_inbox*.md` at the top level — the retired legacy `_inbox.md` (if any),
      the single `_inbox_archive.md`, and any per-session `_inbox_<name>.md` / archive;
    - every `_inbox/*.md` — the per-item consolidated inbox (acp-ajudd#102), which is
      the live location now that `_inbox.md` is split one-file-per-item.
    Matches only headers bearing THIS acronym + handle (`<acr>-<handle>#<n>`), so
    per-user / per-slug namespacing is preserved.

    Returns the max N found, or 0 if none. Never raises — a missing dir,
    unreadable file, or malformed header degrades to "found nothing here" so
    the counter mechanism can never be wedged by the filesystem. This is the
    self-heal that makes a hand-written header (a mint that skipped this
    script) self-correcting: the next real mint sees it and steps past it.
    """
    if not (acr and handle):
        return 0
    id_re = re.compile(re.escape(acr) + "-" + re.escape(handle) + r"#(\d+)")
    best = 0
    try:
        base = os.path.join(sessions_root, slug)
        # Top-level _inbox*.md (legacy live file, archive, per-session files) PLUS the
        # per-item dir _inbox/*.md (the live consolidated inbox after acp-ajudd#102).
        paths = glob.glob(os.path.join(base, "_inbox*.md")) \
            + glob.glob(os.path.join(base, "_inbox", "*.md"))
    except OSError:
        return 0
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError):
            continue  # unreadable file — skip it, never crash the mint
        for m in id_re.finditer(text):
            try:
                n = int(m.group(1))
            except ValueError:
                continue
            if n > best:
                best = n
    return best


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
    ap.add_argument("--sessions-root", default=DEFAULT_SESSIONS_ROOT)
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

    # The next ID is seeded from the TRUE max, not the stored counter alone:
    #   n = max(stored-counter, highest #N already in the inbox files) + 1
    # so a lagging counter — or a header that was hand-written without calling
    # this script — can never cause `next` to return an ID that already exists
    # (acp-ajudd#66). --peek reports the same value without persisting.
    if args.peek:
        file_max = scan_file_max(args.sessions_root, args.slug, acr, args.handle)
        n = max(current, file_max) + 1
        print(f"{acr}-{args.handle}#{n}")
        return

    # Real mint: serialize the read-modify-write behind an exclusive lock so
    # concurrent callers can't read the same value and collide (or roll the
    # counter backward). Re-read the sequence AND re-scan the files INSIDE the
    # lock — the pre-lock `current` above may be stale by the time we hold it.
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
        file_max = scan_file_max(args.sessions_root, args.slug, acr, args.handle)
        n = max(int(seq.get(args.slug, 0)), file_max) + 1
        seq[args.slug] = n
        save_seq(args.seq_file, seq)
    finally:
        release_lock(fd, lock_path)
    print(f"{acr}-{args.handle}#{n}")


if __name__ == "__main__":
    main()
