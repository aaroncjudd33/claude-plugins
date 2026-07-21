#!/usr/bin/env python3
"""Bulk-copy local project memory files into the repo, without per-file model Read+Write.

Used by /session:migrate Step 11b (acp-ajudd#146 follow-up 2). The prior version of
that step did a per-file Read then a full-content Write for every memory file being
migrated — the same anti-pattern already fixed for session files (Step 6) and
inbox/backlog files (Step 8), just missed here. On a 60-file memory dir that meant
60 full-file regenerations as model output, the dominant cost of a 1h+ migrate run,
and it was NOT skipped by --vetted (that flag only skips the PII scan and the
labeling walkthrough, not this copy).

This script does the mechanical part — copy + attribution-frontmatter insert — in
one process call. Only files with no existing `<repo-dir>/<filename>` are copied.
The attribution insert is a fixed 4-line block, computed from file mtime, placed
right before the frontmatter's closing `---` — no content judgment needed, so it
never has to touch the model.

Prints one summary line to stdout: `J added, K skipped` plus one `added: <name>`
line per newly-copied file (consumed by the caller to know which files still need
Step 11b 2a's labeling walkthrough and Step 11b 3's MEMORY.md regen).
"""
import argparse
import glob
import os
import sys
from datetime import date


def mtime_date(path):
    try:
        return date.fromtimestamp(os.path.getmtime(path)).isoformat()
    except OSError:
        return date.today().isoformat()


def insert_attribution(text, handle, when):
    """Insert created-by/created-date/updated-by/updated-date before the frontmatter's closing ---."""
    if not text.startswith("---"):
        return text  # no frontmatter — leave content untouched, nothing to attribute
    close = text.find("\n---", 3)
    if close == -1:
        return text  # malformed frontmatter — leave as-is rather than guess
    attribution = (
        f'created-by: "@{handle}"\n'
        f'created-date: "{when}"\n'
        f'updated-by: "@{handle}"\n'
        f'updated-date: "{when}"\n'
    )
    return text[:close + 1] + attribution + text[close + 1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-dir", required=True)
    ap.add_argument("--repo-dir", required=True)
    ap.add_argument("--handle", required=True)
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    local_dir = os.path.expanduser(args.local_dir)
    repo_dir = args.repo_dir
    if not os.path.isdir(local_dir):
        sys.stdout.write("0 added, 0 skipped\n")
        return 0

    os.makedirs(repo_dir, exist_ok=True)

    added, skipped = [], []
    for path in sorted(glob.glob(os.path.join(local_dir, "*.md"))):
        base = os.path.basename(path)
        if base in ("MEMORY.md", ".migrated-to-repo"):
            continue
        dest = os.path.join(repo_dir, base)
        if os.path.exists(dest):
            skipped.append(base)
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            sys.stderr.write(f"memory-copy: could not read {path}: {exc}\n")
            continue
        when = mtime_date(path)
        text = insert_attribution(text, args.handle, when)
        try:
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as exc:
            sys.stderr.write(f"memory-copy: could not write {dest}: {exc}\n")
            continue
        added.append(base)

    sys.stdout.write(f"{len(added)} added, {len(skipped)} skipped\n")
    for name in added:
        sys.stdout.write(f"added: {name}\n")
    for name in skipped:
        sys.stdout.write(f"skipped: {name}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # copy must never wedge the migrate command
        sys.stderr.write(f"memory-copy: {exc}\n")
        sys.exit(0)
