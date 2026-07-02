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

DEFAULT_SEQ_FILE = os.path.expanduser("~/.claude/config/inbox-seq.json")


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
    n = current + 1
    if not args.peek:
        seq[args.slug] = n
        save_seq(args.seq_file, seq)
    print(f"{acr}-{args.handle}#{n}")


if __name__ == "__main__":
    main()
