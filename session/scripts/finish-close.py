#!/usr/bin/env python3
"""finish-close.py — perform the session-finish close as ONE atomic act (acp-ajudd#103).

The mechanical counterpart to inbox-id.py / session-list.py / session-archive.py.
`/session:finish` composes the *semantic* content (the history sentence, the worklog
block, the `[DONE]` note, the session-file body). This script performs ALL the
close-mechanics WRITES in one call, or exits non-zero having changed nothing.

Why this exists (acp-ajudd#94 -> #103): the close is ~5 separate writes and
"all-or-nothing" cannot be *enforced* by prose, so the model reliably did the loud
half (deploy + return block) and dropped the quiet half (the record close) — three
sessions in a row (#85, #96, #95) needed a manual dispatch tie-out. Routing the whole
close through one deterministic call makes atomicity REAL instead of aspirational
(same principle as inbox-id.py's atomic mint, applied to the finish close).

What it does — ONE call, atomic:
  1. Flip session -> completed in ALL status copies: frontmatter `status:`
     (plugin/personal), body `- **Status:**`, and the `_index.md` row.
  2. Stamp `[DONE <date> — <note>]` on the item's `_inbox_archive.md` entry
     (completion authority = coding-finish). Skipped when --item-id is empty.
  3. Remove the `_active` marker.
  4. Append the composed history entry to `_history.md`.
  5. Append the composed worklog entry to `~/.claude/memory/worklog/<date>.md`.

All-or-nothing / idempotent: every HARD precondition (session file present + has a
body Status line; _index present) is validated BEFORE any write, so a validation
failure changes nothing. The writes themselves are ensure-state operations (set
status, ensure-line-present appends, rm -f) so re-running on a partial-failure retry
converges to the same end state without duplicating anything. The shared-file writes
run under the same advisory lock primitive inbox-id.py uses.

Free text (which may contain newlines / em-dashes) is read from a JSON object on
stdin: {"history_line": "...", "worklog_entry": "...", "done_note": "..."}. Structured
identifiers are flags.

Usage:
  finish-close.py \
    --session-root <dir> --slug <slug> --name <name> --type <type> \
    --date <YYYY-MM-DD> --handle <handle> \
    [--item-id <id>] [--title <title>] \
    [--worklog-path <path>] [--sessions-root <dir>] [--dry-run]
  <<< '{"history_line": "...", "worklog_entry": "...", "done_note": "..."}'

Exit 0 on success (or a clean dry-run); non-zero if a hard precondition fails
(nothing written).
"""
import argparse
import json
import os
import re
import sys
import time

DEFAULT_SESSIONS_ROOT = os.path.expanduser("~/.claude/memory/sessions")

# Locking for the multi-file write phase — reuses inbox-id.py's proven cross-platform
# O_EXCL advisory-lock discipline (Git-Bash-safe, stale-break, bounded retry). Copied
# rather than imported because the sibling module's filename ("inbox-id.py") is not a
# legal Python module name; the two helpers are tiny and self-contained.
LOCK_RETRIES = 50
LOCK_RETRY_SLEEP = 0.05
LOCK_STALE_SECONDS = 10.0

TYPES_WITH_FRONTMATTER_STATUS = ("plugin", "personal")


def acquire_lock(lock_path):
    """Acquire an exclusive lock via atomic O_EXCL create (see inbox-id.py)."""
    try:
        os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    except OSError:
        return None
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
            try:
                age = time.time() - os.path.getmtime(lock_path)
            except OSError:
                age = 0.0
            if age > LOCK_STALE_SECONDS:
                try:
                    os.remove(lock_path)
                except OSError:
                    pass
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


class CloseError(Exception):
    """A hard precondition failed — nothing has been written; abort the whole close."""


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def atomic_write(path, content):
    """Write content to path via temp-file + os.replace (atomic on the same filesystem)."""
    tmp = path + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    os.replace(tmp, path)


# ---- content computation (pure; no writes) --------------------------------------

def compute_session_file(text, set_frontmatter):
    """Return session-file text with all status copies set to `completed`.

    - Frontmatter `status:` (only when set_frontmatter): replace if present, else insert.
    - Body `- **Status:**`: replace if present (HARD-required — a malformed body is a
      real anomaly worth surfacing, so its absence raises CloseError).
    """
    # Body status line — required.
    body_re = re.compile(r"^(\s*-\s*\*\*Status:\*\*\s*)(.*)$", re.MULTILINE)
    if not body_re.search(text):
        raise CloseError(
            "session file has no `- **Status:**` line to flip (malformed body)")
    text = body_re.sub(lambda m: m.group(1) + "completed", text, count=1)

    if not set_frontmatter:
        return text
    if not text.startswith("---"):
        raise CloseError("plugin/personal session file has no frontmatter block")
    end = text.find("\n---", 3)
    if end == -1:
        raise CloseError("plugin/personal session file frontmatter is unterminated")
    fm = text[3:end + 1]           # keep trailing newline of last fm line
    rest = text[end + 1:]          # starts at the closing "---"
    status_re = re.compile(r"^(\s*status\s*:\s*)(.*)$", re.MULTILINE)
    if status_re.search(fm):
        fm = status_re.sub(lambda m: m.group(1) + "completed", fm, count=1)
    else:
        # Insert after `type:` if present, else after `updated:`, else at end.
        anchor = re.search(r"^\s*type\s*:.*$", fm, re.MULTILINE) or \
            re.search(r"^\s*updated\s*:.*$", fm, re.MULTILINE)
        if anchor:
            fm = fm[:anchor.end()] + "\nstatus: completed" + fm[anchor.end():]
        else:
            fm = fm.rstrip("\n") + "\nstatus: completed\n"
    return "---" + fm + rest


def compute_index(text, name, handle, date, title):
    """Return _index.md text with the row for `name` set to completed.

    Preserves created-by/created-date (cols 2-3); updates updated-by/date/status; sets
    title when provided, else preserves the existing title. Appends a fresh row if the
    session has none yet.
    """
    at_handle = handle if handle.startswith("@") else "@" + handle
    lines = text.splitlines()
    out = []
    found = False
    for line in lines:
        if line.startswith("#") or not line.strip():
            out.append(line)
            continue
        cols = [c.strip() for c in line.split("|")]
        if cols and cols[0] == name:
            found = True
            created_by = cols[1] if len(cols) > 1 else at_handle
            created_date = cols[2] if len(cols) > 2 else date
            existing_title = cols[6] if len(cols) > 6 else "—"
            new_title = title if title else (existing_title or "—")
            out.append(" | ".join(
                [name, created_by, created_date, at_handle, date, "completed", new_title]))
        else:
            out.append(line)
    if not found:
        out.append(" | ".join(
            [name, at_handle, date, at_handle, date, "completed", title or "—"]))
    return "\n".join(out) + "\n"


def compute_archive_stamp(text, name, date, done_note):
    """Return (new_text, note). Stamp `[DONE <date> — <note>]` after the CONSUMED line.

    Locates the `[CONSUMED … session <name>]` line (tolerates both `->` and `→`
    arrows). Idempotent: if the enclosing entry block already carries a `[DONE …]`
    line, leaves the file unchanged. If no CONSUMED line for this session is found,
    returns the text unchanged with an explanatory note (a soft anomaly — the record
    close must not be blocked by a missing ledger entry; the note is surfaced).
    """
    consumed_re = re.compile(
        r"^.*\[CONSUMED\b[^\]]*\bsession\s+" + re.escape(name) + r"\b[^\]]*\].*$",
        re.MULTILINE)
    m = consumed_re.search(text)
    if not m:
        return text, "no [CONSUMED … session %s] line found — [DONE] NOT stamped" % name

    # Entry block = from the preceding "## " header (or file start) to the next one.
    start = text.rfind("\n## ", 0, m.start())
    start = 0 if start == -1 else start + 1
    nxt = text.find("\n## ", m.end())
    end = len(text) if nxt == -1 else nxt
    block = text[start:end]
    if re.search(r"^\s*\[DONE\b", block, re.MULTILINE):
        return text, "already stamped (idempotent no-op)"

    stamp = "[DONE %s — %s]" % (date, done_note) if done_note else "[DONE %s]" % date
    line_end = text.find("\n", m.end())
    line_end = len(text) if line_end == -1 else line_end
    new_text = text[:line_end] + "\n" + stamp + text[line_end:]
    return new_text, "stamped %s" % stamp


def compute_append(existing, entry):
    """Return (new_text, changed) ensuring `entry` is present at the end of `existing`.

    Idempotent: if the exact entry block is already present, returns unchanged. This is
    what makes a retry after a partial failure safe — appends never duplicate.
    """
    entry = entry.rstrip("\n")
    if not entry:
        return existing, False
    if entry in existing:
        return existing, False
    if existing and not existing.endswith("\n"):
        existing += "\n"
    return existing + entry + "\n", True


# ---- orchestration --------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Atomic session-finish close (acp-ajudd#103).")
    ap.add_argument("--session-root", required=True,
                    help="dir holding <name>.md, _index.md, _inbox_archive.md, _history.md")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--type", required=True,
                    help="plugin / personal / story / cab / general")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (composed by the caller)")
    ap.add_argument("--handle", required=True, help="authoring handle, e.g. ajudd")
    ap.add_argument("--item-id", default="",
                    help="inbox item id for the [DONE] stamp; empty = bare session, skip")
    ap.add_argument("--title", default="", help="_index title; empty = preserve/‘—’")
    ap.add_argument("--worklog-path", default="",
                    help="default ~/.claude/memory/worklog/<date>.md")
    ap.add_argument("--sessions-root", default=DEFAULT_SESSIONS_ROOT,
                    help="root holding <slug>/_active (always local)")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate + report what WOULD change, write nothing")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # Free text via stdin JSON (may be empty if nothing piped).
    payload = {}
    raw = ""
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
    if raw.strip():
        try:
            payload = json.loads(raw)
        except ValueError as exc:
            sys.stderr.write("finish-close: invalid JSON on stdin: %s\n" % exc)
            return 2
    history_line = (payload.get("history_line") or "").strip("\n")
    worklog_entry = (payload.get("worklog_entry") or "").rstrip("\n")
    done_note = (payload.get("done_note") or "").strip()

    root = os.path.expanduser(args.session_root)
    session_path = os.path.join(root, args.name + ".md")
    index_path = os.path.join(root, "_index.md")
    archive_path = os.path.join(root, "_inbox_archive.md")
    history_path = os.path.join(root, "_history.md")
    active_path = os.path.join(
        os.path.expanduser(args.sessions_root), args.slug, "_active")
    worklog_path = os.path.expanduser(
        args.worklog_path
        or os.path.join("~/.claude/memory/worklog", args.date + ".md"))

    set_fm = args.type.strip().lower() in TYPES_WITH_FRONTMATTER_STATUS

    # ---- PHASE 1: read + validate + compute everything (no writes) ----
    try:
        if not os.path.isfile(session_path):
            raise CloseError("session file not found: %s" % session_path)
        session_text = read_text(session_path)
        new_session = compute_session_file(session_text, set_fm)

        if not os.path.isfile(index_path):
            raise CloseError("_index.md not found: %s" % index_path)
        index_text = read_text(index_path)
        new_index = compute_index(
            index_text, args.name, args.handle, args.date, args.title.strip())

        archive_note = "skipped (no --item-id)"
        new_archive = None
        if args.item_id.strip():
            if os.path.isfile(archive_path):
                archive_text = read_text(archive_path)
                new_archive, archive_note = compute_archive_stamp(
                    archive_text, args.name, args.date, done_note)
                if new_archive == archive_text:
                    new_archive = None  # nothing to write (idempotent / not found)
            else:
                archive_note = "no _inbox_archive.md — [DONE] NOT stamped"

        history_existing = read_text(history_path) if os.path.isfile(history_path) \
            else "# History — %s\n" % args.slug
        new_history, history_changed = compute_append(history_existing, history_line)

        worklog_existing = read_text(worklog_path) if os.path.isfile(worklog_path) else ""
        new_worklog, worklog_changed = compute_append(worklog_existing, worklog_entry)
    except CloseError as exc:
        sys.stderr.write("finish-close: ABORTED (nothing written) - %s\n" % exc)
        return 1

    # ---- PHASE 2: report (dry-run) or write (locked) ----
    actions = [
        "session file: status -> completed (frontmatter%s + body)"
        % ("" if set_fm else " skipped for type " + args.type),
        "_index.md: row '%s' -> completed" % args.name,
        "_inbox_archive.md: %s" % archive_note,
        "_history.md: %s" % ("append entry" if history_changed else "unchanged (idempotent)"),
        "worklog %s: %s" % (
            os.path.basename(worklog_path),
            "append entry" if worklog_changed else "unchanged (idempotent)"),
        "_active: remove (%s)" % ("present" if os.path.exists(active_path) else "already gone"),
    ]

    if args.dry_run:
        print("finish-close DRY-RUN for %s (%s):" % (args.name, args.slug))
        for a in actions:
            print("  - " + a)
        return 0

    lock_path = index_path + ".finish-close.lock"
    fd = acquire_lock(lock_path)
    if fd is None:
        sys.stderr.write(
            "finish-close: could not acquire close lock within the bounded wait; "
            "another finish may be running. Nothing written — retry.\n")
        return 3

    written = []
    try:
        atomic_write(session_path, new_session)
        written.append("session file")
        atomic_write(index_path, new_index)
        written.append("_index.md")
        if new_archive is not None:
            atomic_write(archive_path, new_archive)
            written.append("_inbox_archive.md")
        if history_changed:
            atomic_write(history_path, new_history)
            written.append("_history.md")
        if worklog_changed:
            os.makedirs(os.path.dirname(worklog_path), exist_ok=True)
            atomic_write(worklog_path, new_worklog)
            written.append("worklog")
        # _active removal is the terminal write — rm -f semantics.
        try:
            os.remove(active_path)
        except FileNotFoundError:
            pass
        written.append("_active cleared")
    except OSError as exc:
        # A write failed mid-phase. Idempotency makes a re-run safe; tell the caller
        # what landed so the retry (or a human) knows the partial state.
        sys.stderr.write(
            "finish-close: write error after committing [%s] - %s. "
            "Re-run to converge (idempotent).\n" % (", ".join(written), exc))
        return 4
    finally:
        release_lock(fd, lock_path)

    print("finish-close: closed %s (%s) — atomic tie-out complete." % (args.name, args.slug))
    for a in actions:
        print("  - " + a)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CloseError as exc:  # defensive — should be caught in phase 1
        sys.stderr.write("finish-close: ABORTED (nothing written) - %s\n" % exc)
        sys.exit(1)
