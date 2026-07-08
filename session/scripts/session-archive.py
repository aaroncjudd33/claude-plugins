#!/usr/bin/env python3
"""Session retention prune — archive completed sessions older than 6 months (acp-ajudd#50).

Idempotent. Moves each COMPLETED session `<name>.md` whose completion date
(frontmatter `updated:`, fallback body `- **Status:**`/`Last worked on` date, fallback
file mtime) is older than the retention window into `<session_root>/_archive/`, and drops
its row from `_index.md`. Archived files stay readable and resurfaceable by story key
(`/session:search`); they leave the default listing because `session-list.py` globs only
the `session_root` top level (not `_archive/`).

NEVER touches in-progress or paused sessions, regardless of age — an abandoned-but-unfinished
session stays put until someone finishes it.

Triggered by `/session:start` and `/session:finish` (before any commit those commands make).
For repo-based sessions `_archive/` is committed (durable, cross-machine); for local sessions
it is local — the mechanism is identical, git-tracking is contextual.

The 6-month window is HARDCODED and intentionally not configurable (acp-ajudd#50): a
configurable window would let one developer set it short and delete shared session history
others still need. Fixed keeps the shared set predictable.

Fail-safe: any error prints a note to stderr and exits 0 — retention must NEVER block or
break the start/finish/commit it is triggered from. Prints a one-line summary to stdout only
when it actually archives something; silent otherwise.
"""
import argparse
import glob
import os
import re
import shutil
import sys
from datetime import date

# HARDCODED — do NOT add a CLI flag or config key for this (acp-ajudd#50).
RETENTION_MONTHS = 6


def subtract_months(d, months):
    """Return the date `months` before `d`, clamping the day to the target month's length."""
    m = d.month - 1 - months
    y = d.year + m // 12
    m = m % 12 + 1
    leap = (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0))
    dim = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return date(y, m, min(d.day, dim))


def parse_iso(s):
    try:
        y, mo, da = (int(x) for x in s.strip().split("-")[:3])
        return date(y, mo, da)
    except (ValueError, AttributeError):
        return None


def read_status_and_date(path):
    """Return (status, completion_date) for a session file.

    status from frontmatter `status:` or body `- **Status:**` (default in-progress).
    completion_date from frontmatter `updated:`, else body/mtime fallback.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return "in-progress", None

    fm_status = fm_updated = ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        fm = text[3:end] if end != -1 else ""
        for line in fm.splitlines():
            m = re.match(r"\s*status\s*:\s*(\S+)", line)
            if m:
                fm_status = m.group(1).strip()
            m = re.match(r"\s*updated\s*:\s*(\S+)", line)
            if m:
                fm_updated = m.group(1).strip()

    body_status = ""
    m = re.search(r"^\-\s*\*\*Status:\*\*\s*(\S+)", text, re.MULTILINE)
    if m:
        body_status = m.group(1).strip()

    status = (fm_status or body_status or "in-progress").strip().lower()
    completion = parse_iso(fm_updated)
    if completion is None:
        try:
            from datetime import datetime
            completion = datetime.fromtimestamp(os.path.getmtime(path)).date()
        except Exception:
            completion = None
    return status, completion


def rewrite_index_without(index_path, archived_names):
    """Drop the rows for archived_names from _index.md, preserving header + other rows."""
    if not archived_names or not os.path.isfile(index_path):
        return
    try:
        with open(index_path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return
    kept = []
    for line in lines:
        if line.startswith("#"):
            kept.append(line)
            continue
        name = line.split("|", 1)[0].strip()
        if name in archived_names:
            continue
        kept.append(line)
    try:
        with open(index_path, "w", encoding="utf-8") as fh:
            fh.writelines(kept)
    except OSError:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session-root", required=True)
    ap.add_argument("--slug", default="")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what WOULD be archived without moving anything")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    root = os.path.expanduser(args.session_root)
    if not os.path.isdir(root):
        return 0  # nothing to prune

    try:
        today = date.today()
    except Exception:
        return 0  # can't compute age — do nothing rather than guess
    cutoff = subtract_months(today, RETENTION_MONTHS)

    archive_dir = os.path.join(root, "_archive")
    archived = []

    for p in glob.glob(os.path.join(root, "*.md")):
        base = os.path.basename(p)
        if base.startswith("_") or base.endswith(".approved-hash"):
            continue  # skip caches, stashes, inbox/backlog, and the archive itself
        name = base[:-3]
        if name.startswith("refinement-"):
            continue  # legacy refine artifacts — not real sessions
        status, completion = read_status_and_date(p)
        if status != "completed":
            continue  # NEVER archive in-progress/paused, regardless of age
        if completion is None or completion >= cutoff:
            continue  # not old enough (or undatable — leave it)
        if args.dry_run:
            archived.append(name)
            continue
        try:
            os.makedirs(archive_dir, exist_ok=True)
            dest = os.path.join(archive_dir, base)
            # Idempotent: if a same-named file is already archived, overwrite it
            # (re-archiving the same completed session is a no-op in effect).
            shutil.move(p, dest)
            archived.append(name)
        except OSError:
            pass  # skip this one; never block the whole prune

    if archived and not args.dry_run:
        rewrite_index_without(os.path.join(root, "_index.md"), set(archived))

    if archived:
        slug = args.slug or os.path.basename(root.rstrip("/"))
        verb = "would archive" if args.dry_run else "archived"
        listed = ", ".join(sorted(archived))
        sys.stdout.write(
            f"Retention: {verb} {len(archived)} completed session(s) >"
            f"{RETENTION_MONTHS}mo in {slug} → _archive/ ({listed})\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # retention must never break its trigger command
        sys.stderr.write(f"session-archive: {exc}\n")
        sys.exit(0)
