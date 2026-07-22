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
     Reconcile-consume (acp-ajudd#115): if the item is STILL LIVE at finish
     (`_inbox/<id>.md` present — the mandatory pickup was skipped), consume it here
     first — fold-then-archive with `[CONSUMED]`, delete the live file, then stamp
     `[DONE]` — so a session can never end with its work both live-as-`ready` AND
     shipped/consumed (state-exclusivity #13). A one-line note signals it had to.
  3. Remove the `_active` marker and its `_active.dirty` close-safety sentinel
     (acp-ajudd#157 — the statusline's "unsaved" light; cleared here since the close
     just persisted everything, so nothing is pending anymore). Only when `_active`
     actually names THIS session (acp-ajudd#163) — a reconcile-style close of a
     session that isn't the current active one (session:sync) leaves another
     in-progress session's active pointer untouched.
  4. Append the composed history entry to `_history.md`.
  5. Append the composed worklog entry to `~/.claude/memory/worklog/<date>.md`.

All-or-nothing / idempotent: every HARD precondition (session file present + has a
body Status line; _index present) is validated BEFORE any write, so a validation
failure changes nothing. The writes themselves are ensure-state operations (set
status, ensure-line-present appends, rm -f) so re-running on a partial-failure retry
converges to the same end state without duplicating anything. The shared-file writes
run under the same advisory lock primitive inbox-id.py uses.

Self-verifying (acp-ajudd#107 FIX 0): the writes are sequential, so "all-or-nothing"
was still aspirational — the script could stop or skip mid-way and STILL exit 0. So
after writing, it re-reads every surface and confirms the expected end state (status
flips, _index row, _active gone, history + worklog lines, and the [DONE] stamp in the
target id's archive block) BEFORE exit 0. Any miss exits non-zero with the precise
surface — the caller (and the #97 close-safety cue, gated on exit 0) sees a real
failure, not a false success. Hardened alongside FIX 0: UTF-8-decode stdin as bytes
(Defect 1 — Git-Bash cp1252 mangled em-dash/emoji payloads); stable-key idempotency
for history/worklog (Defect 2 — reworded re-run rows no longer double-append); and
header-bounded archive-block resolution (Defect 3 — never key the [DONE] insert off
the nearest CONSUMED line, which mis-resolved stamp-before-## entries).

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


# A marker line = one of the archive's bracketed lifecycle stamps.
MARKER_RE = re.compile(r"^\s*\[(CONSUMED|DONE|DISPOSITIONED)\b")
CONSUMED_RE = re.compile(r"^\s*\[CONSUMED\b")
DONE_RE = re.compile(r"^\s*\[DONE\b")


def _id_header_re(item_id):
    """Line-regex matching the archive header `## <item_id> ·` for the exact id.

    Anchors on the id with `#` preserved and tolerates `#`/`-` at the number
    separator (the header uses `acp-ajudd#107`; a provenance value might carry the
    filename form `acp-ajudd-107`). The negative lookahead stops `#10` matching
    `#102` — never key off the nearest CONSUMED line (that mis-resolved #102 to
    #97's block; acp-ajudd#107 Defect 3).
    """
    esc = re.escape(item_id.strip()).replace(r"\#", "[#-]")
    return re.compile(r"^##\s+" + esc + r"(?![0-9A-Za-z]).*$")


def _locate_entry(lines, item_id):
    """Return (header_idx, block_start, block_end) for the entry whose header is
    `## <item_id> ·`, or None.

    The block is bounded by the header: it runs from the header line DOWN to the
    next `## ` header (or EOF), and is extended UPWARD over any contiguous marker
    lines directly above the header (the older stamp-before-`##` convention) so the
    idempotency check sees a `[DONE]` in either placement. block_start is the first
    such marker (or the header itself); block_end is exclusive.
    """
    hre = _id_header_re(item_id)
    header_idx = next((i for i, ln in enumerate(lines) if hre.match(ln)), None)
    if header_idx is None:
        return None
    block_start = header_idx
    j = header_idx - 1
    while j >= 0 and MARKER_RE.match(lines[j]):
        block_start = j
        j -= 1
    block_end = len(lines)
    for k in range(header_idx + 1, len(lines)):
        if lines[k].startswith("## "):
            block_end = k
            break
    return header_idx, block_start, block_end


def compute_archive_stamp(text, item_id, date, done_note):
    """Return (new_text, note, expect_done). Stamp `[DONE <date> — <note>]` inside the
    header-bounded block for `item_id` (acp-ajudd#107 Defect 3).

    - Locates the entry by its `## <id> ·` header — never by the nearest CONSUMED
      line (that mis-resolved a stamp-before-`##` entry to the previous entry's block
      and false-positived "already stamped", silently dropping the real [DONE]).
    - Self-heals placement for the target entry: any CONSUMED/DONE markers that sat
      ABOVE the header are moved to just below it (the new convention), keeping each
      entry's markers together.
    - Idempotent: if the block already carries a `[DONE …]` (in either placement),
      returns unchanged with expect_done=True (read-back still confirms it).
    - `expect_done` tells FIX-0 read-back whether to require a [DONE] for this id: True
      when the entry was located (stamped or already-stamped), False when no `## <id>`
      header exists (a soft anomaly — surfaced, but the close is not blocked on it).
    """
    lines = text.split("\n")
    loc = _locate_entry(lines, item_id)
    if loc is None:
        return (text,
                "no `## %s` header in archive — [DONE] NOT stamped" % item_id,
                False)
    header_idx, block_start, block_end = loc
    block = lines[block_start:block_end]
    if any(DONE_RE.match(ln) for ln in block):
        return text, "already stamped (idempotent no-op)", True

    stamp = "[DONE %s — %s]" % (date, done_note) if done_note else "[DONE %s]" % date
    # Reassemble the block with the header first, then any markers that were above it,
    # then the rest — so a stamp-before-`##` CONSUMED lands below the header.
    above = lines[block_start:header_idx]
    header = lines[header_idx]
    below = lines[header_idx + 1:block_end]
    body = [header] + above + below
    # Insert immediately after the last marker line in the body, else after the header.
    insert_idx = 1
    for k in range(1, len(body)):
        if MARKER_RE.match(body[k]):
            insert_idx = k + 1
    body.insert(insert_idx, stamp)
    new_lines = lines[:block_start] + body + lines[block_end:]
    return "\n".join(new_lines), "stamped %s" % stamp, True


def inbox_item_path(session_root, item_id):
    """Return the live inbox-item file path for `item_id`, or None if it can't be formed.

    The per-item inbox stores each entry as `_inbox/<id-with-#->->.md>` (acp-ajudd#102);
    a header/provenance id uses `#` (`acp-ajudd#115`) while the filename form uses `-`
    (`acp-ajudd-115.md`), so normalize `#`->`-` before joining.
    """
    stem = item_id.strip()
    if not stem:
        return None
    stem = stem.replace("#", "-")
    if not stem.endswith(".md"):
        stem += ".md"
    return os.path.join(session_root, "_inbox", stem)


def compute_consume_entry(item_text, date, name):
    """Return the CONSUMED-stamped archive entry for a still-live inbox item
    (acp-ajudd#115 reconcile).

    Fold-then-archive semantics (acp-ajudd#40 / #102): the entry is the live item's
    text verbatim with a `[CONSUMED <date> ...]` marker inserted immediately AFTER its
    first `## <id> ·` header line — the same placement pickup uses and the same
    header-bounded placement `compute_archive_stamp` requires (acp-ajudd#107 Defect
    3-ii). The marker records that the consume happened at finish (pickup was skipped),
    so the archive itself signals the anomaly. ASCII arrow keeps it locale-proof.
    """
    body = item_text.rstrip("\n")
    marker = ("[CONSUMED %s -> session %s (reconciled at finish; pickup was skipped)]"
              % (date, name))
    lines = body.split("\n")
    out = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if not inserted and ln.startswith("## "):
            out.append(marker)
            inserted = True
    if not inserted:
        # Defensive: item body has no `## ` header — prepend the marker so the block is
        # still locatable (never leave a consumed item unmarked).
        out = [marker] + out
    return "\n".join(out)


def normalize_consumed_placement(text):
    """Relocate every stray stamp-before-`##` marker cluster below its header.

    A contiguous run of marker lines (CONSUMED/DONE/DISPOSITIONED) sitting directly
    above a `## ` header — with no blank line between — is the older stamp-before-`##`
    convention and unambiguously belongs to that header; move it to just below the
    header, order preserved. Whole-archive, idempotent (already-correct markers have a
    blank or body line above the header, so nothing moves). This is the one-time
    migration half of acp-ajudd#107 Defect 3-ii (absorbs #100's secondary note); run
    via --migrate-archive, kept out of the hot close path.
    """
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        if MARKER_RE.match(lines[i]):
            j = i
            while j < n and MARKER_RE.match(lines[j]):
                j += 1
            if j < n and lines[j].startswith("## "):
                out.append(lines[j])           # header first
                out.extend(lines[i:j])         # then its markers
                i = j + 1
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def _key_present(existing, structural_re, name):
    """True if a structural line already names this session — a STABLE-KEY match that
    survives rewording (acp-ajudd#107 Defect 2).

    Keys off (structural line + session name), not the full rendered text, so a
    reworded second-pass `_history`/worklog line still dedups. `structural_re` anchors
    the kind of line (a `[<date> …]` history row or a `## …` worklog header); the name
    must appear as a whole token (hyphens are part of names, so they bound too).
    """
    if not name:
        return False
    name_re = re.compile(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])")
    for line in existing.splitlines():
        if structural_re.match(line) and name_re.search(line):
            return True
    return False


def compute_append(existing, entry, structural_re=None, dedup_name=None):
    """Return (new_text, changed) ensuring `entry` is present at the end of `existing`.

    Idempotent two ways: an exact-text match, OR — when structural_re/dedup_name are
    given — a stable-key match (same session named on the same kind of structural
    line), so a RE-run whose free text was reworded does not append a duplicate
    (acp-ajudd#107 Defect 2). This is what makes a retry after a partial failure safe.
    """
    entry = entry.rstrip("\n")
    if not entry:
        return existing, False
    if entry in existing:
        return existing, False
    if structural_re is not None and _key_present(existing, structural_re, dedup_name):
        return existing, False
    if existing and not existing.endswith("\n"):
        existing += "\n"
    return existing + entry + "\n", True


# ---- self-verification (FIX 0) --------------------------------------------------

def _index_row_completed(text, name):
    """True if the `_index.md` row for `name` has status column == 'completed'."""
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cols = [c.strip() for c in line.split("|")]
        if cols and cols[0] == name:
            return len(cols) > 5 and cols[5] == "completed"
    return False


def verify_close(paths, name, item_id, date, set_fm,
                 expect_history, expect_worklog, expect_done,
                 expect_item_gone=None, expect_active_cleared=True):
    """Re-read every surface and confirm the expected end state (acp-ajudd#107 FIX 0).

    Returns a list of human-readable failure strings (empty == all confirmed). The
    close is NOT actually all-or-nothing — it does N sequential writes and can stop or
    skip mid-way — so before exit 0 we prove each surface landed. Every defect (1/2/3)
    produced the same signature: the script claimed success on a partial close and only
    an external check caught it. This read-back is that check, moved in-process.
    """
    failures = []

    session_text = read_text(paths["session"]) if os.path.isfile(paths["session"]) else ""
    if not re.search(r"^\s*-\s*\*\*Status:\*\*\s*completed\b", session_text, re.MULTILINE):
        failures.append("session body `- **Status:**` not 'completed'")
    if set_fm:
        end = session_text.find("\n---", 3)
        fm = session_text[3:end + 1] if session_text.startswith("---") and end != -1 else ""
        if not re.search(r"^\s*status\s*:\s*completed\b", fm, re.MULTILINE):
            failures.append("session frontmatter `status:` not 'completed'")

    index_text = read_text(paths["index"]) if os.path.isfile(paths["index"]) else ""
    if not _index_row_completed(index_text, name):
        failures.append("_index.md row '%s' not 'completed'" % name)

    if expect_active_cleared:
        if os.path.exists(paths["active"]):
            failures.append("_active marker still present")

        if os.path.exists(paths["dirty"]):
            failures.append("_active.dirty sentinel still present")

    if expect_history:
        htext = read_text(paths["history"]) if os.path.isfile(paths["history"]) else ""
        if not _key_present(htext, re.compile(r"^\[" + re.escape(date)), name):
            failures.append("_history.md entry for '%s' not found" % name)

    if expect_worklog:
        wtext = read_text(paths["worklog"]) if os.path.isfile(paths["worklog"]) else ""
        if not _key_present(wtext, re.compile(r"^##\s"), name):
            failures.append("worklog entry for '%s' not found" % name)

    if expect_done:
        atext = read_text(paths["archive"]) if os.path.isfile(paths["archive"]) else ""
        loc = _locate_entry(atext.split("\n"), item_id)
        if loc is None:
            failures.append("archive entry '%s' not found on read-back" % item_id)
        else:
            _, bstart, bend = loc
            if not any(DONE_RE.match(ln) for ln in atext.split("\n")[bstart:bend]):
                failures.append("[DONE] stamp not present in '%s' archive block" % item_id)

    # Reconcile read-back (acp-ajudd#115): if the item was still live at finish, the
    # close consumed it — the live `_inbox/<id>.md` MUST be gone (state-exclusivity #13).
    if expect_item_gone and os.path.exists(expect_item_gone):
        failures.append(
            "live inbox item still present after reconcile: %s" % expect_item_gone)

    return failures


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
    ap.add_argument("--migrate-archive", action="store_true",
                    help="one-time: normalize stray stamp-before-## CONSUMED lines in "
                         "_inbox_archive.md below their header, then exit (acp-ajudd#107)")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # --- one-time archive placement migration (acp-ajudd#107 Defect 3-ii) ---
    if args.migrate_archive:
        archive_path = os.path.join(os.path.expanduser(args.session_root),
                                    "_inbox_archive.md")
        if not os.path.isfile(archive_path):
            print("finish-close --migrate-archive: no _inbox_archive.md, nothing to do.")
            return 0
        before = read_text(archive_path)
        after = normalize_consumed_placement(before)
        if after == before:
            print("finish-close --migrate-archive: already normalized (no-op).")
            return 0
        if args.dry_run:
            print("finish-close --migrate-archive DRY-RUN: %d line(s) would be relocated."
                  % sum(1 for a, b in zip(before.split("\n"), after.split("\n")) if a != b))
            return 0
        atomic_write(archive_path, after)
        print("finish-close --migrate-archive: normalized CONSUMED placement in %s."
              % archive_path)
        return 0

    # Free text via stdin JSON (may be empty if nothing piped). Read stdin as BYTES and
    # decode UTF-8 explicitly (acp-ajudd#107 Defect 1): Git-Bash's locale defaults to
    # cp1252, so the text layer would mangle an em-dash/emoji in the payload into a lone
    # surrogate and leave a partial close. Bytes->utf-8 is locale-proof.
    payload = {}
    raw = ""
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.buffer.read().decode("utf-8")
        except (AttributeError, UnicodeDecodeError):
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
    dirty_path = os.path.join(os.path.dirname(active_path), "_active.dirty")
    worklog_path = os.path.expanduser(
        args.worklog_path
        or os.path.join("~/.claude/memory/worklog", args.date + ".md"))

    set_fm = args.type.strip().lower() in TYPES_WITH_FRONTMATTER_STATUS

    # `_active` names at most one session per slug at a time (single-active-session
    # invariant). Every caller until acp-ajudd#163 was that one active session closing
    # itself, so blind removal was always correct. A reconcile-style caller (session:sync)
    # can close a session that is NOT the currently active one — e.g. a different
    # in-progress session is live right now while this one is being tidied up after an
    # out-of-band Jira close. Only clear `_active`/`_active.dirty` when they actually name
    # THIS session (or are already absent); otherwise leave them untouched and don't
    # require their absence at verify time.
    active_text = None
    if os.path.isfile(active_path):
        try:
            active_text = read_text(active_path).strip()
        except OSError:
            active_text = None
    clear_active = (active_text is None) or (active_text == args.name)

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
        expect_done = False
        reconciled = False
        live_item_path = None
        if args.item_id.strip():
            item_id = args.item_id.strip()
            live_item_path = inbox_item_path(root, item_id)
            archive_existing = read_text(archive_path) if os.path.isfile(archive_path) else None
            if live_item_path and os.path.isfile(live_item_path):
                # RECONCILE (acp-ajudd#115): the item is STILL LIVE at finish — the
                # mandatory pickup (`/session:start code #X`, which consumes it) was
                # skipped. Consume it now as part of this atomic close so a session can
                # NEVER end with its work both live-as-`ready` AND shipped (#13). The
                # live file is deleted in PHASE 2 (under the same lock).
                reconciled = True
                already_archived = (
                    archive_existing is not None
                    and _locate_entry(archive_existing.split("\n"), item_id) is not None)
                if already_archived:
                    # Odd double-state (live copy AND an archive entry). Don't append a
                    # duplicate — just ensure [DONE] on the existing block; the live copy
                    # is still deleted below.
                    new_archive, stamp_note, expect_done = compute_archive_stamp(
                        archive_existing, item_id, args.date, done_note)
                    archive_note = ("item was still live but ALREADY archived (duplicate) "
                                    "— removing live copy; %s" % stamp_note)
                else:
                    live_text = read_text(live_item_path)
                    consumed_entry = compute_consume_entry(live_text, args.date, args.name)
                    base = (archive_existing if archive_existing is not None
                            else "# Inbox Archive — %s\n" % args.slug)
                    combined = base.rstrip("\n") + "\n\n" + consumed_entry + "\n"
                    new_archive, stamp_note, expect_done = compute_archive_stamp(
                        combined, item_id, args.date, done_note)
                    archive_note = ("RECONCILED — item was still live (pickup skipped); "
                                    "consumed (fold-then-archive) + %s" % stamp_note)
            elif archive_existing is not None:
                new_archive, archive_note, expect_done = compute_archive_stamp(
                    archive_existing, item_id, args.date, done_note)
                if new_archive == archive_existing:
                    new_archive = None  # nothing to write (idempotent / not found)
            else:
                archive_note = "no _inbox_archive.md — [DONE] NOT stamped"

        history_existing = read_text(history_path) if os.path.isfile(history_path) \
            else "# History — %s\n" % args.slug
        new_history, history_changed = compute_append(
            history_existing, history_line,
            re.compile(r"^\[" + re.escape(args.date)), args.name)

        worklog_existing = read_text(worklog_path) if os.path.isfile(worklog_path) else ""
        new_worklog, worklog_changed = compute_append(
            worklog_existing, worklog_entry, re.compile(r"^##\s"), args.name)
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
    ]
    if clear_active:
        actions.append("_active: remove (%s)" % (
            "present" if os.path.exists(active_path) else "already gone"))
        actions.append("_active.dirty: remove (%s)" % (
            "present" if os.path.exists(dirty_path) else "already gone"))
    else:
        actions.append(
            "_active: left alone (names a different session: %s)" % active_text)
    if reconciled:
        actions.insert(3, "_inbox/<id>.md: consume live item (reconcile — pickup was skipped)")

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
        if reconciled and live_item_path and os.path.isfile(live_item_path):
            # Terminal half of the reconcile (acp-ajudd#115): the CONSUMED copy is now in
            # the archive (recovery net), so remove the live item — completing
            # fold-then-archive and restoring state-exclusivity (#13).
            os.remove(live_item_path)
            written.append("live inbox item consumed (reconcile)")
        if history_changed:
            atomic_write(history_path, new_history)
            written.append("_history.md")
        if worklog_changed:
            os.makedirs(os.path.dirname(worklog_path), exist_ok=True)
            atomic_write(worklog_path, new_worklog)
            written.append("worklog")
        # _active removal is the terminal write — rm -f semantics. Only when it names
        # THIS session (acp-ajudd#163) — a sync-style close of a non-active session must
        # never stomp another in-progress session's active pointer.
        if clear_active:
            try:
                os.remove(active_path)
            except FileNotFoundError:
                pass
            written.append("_active cleared")
            # Close-safety sentinel (acp-ajudd#157) clears in the same atomic write —
            # the close just persisted everything, so nothing is pending anymore.
            try:
                os.remove(dirty_path)
            except FileNotFoundError:
                pass
            written.append("_active.dirty cleared")
        else:
            written.append("_active left alone (belongs to a different session)")
    except OSError as exc:
        # A write failed mid-phase. Idempotency makes a re-run safe; tell the caller
        # what landed so the retry (or a human) knows the partial state.
        sys.stderr.write(
            "finish-close: write error after committing [%s] - %s. "
            "Re-run to converge (idempotent).\n" % (", ".join(written), exc))
        release_lock(fd, lock_path)
        return 4

    # ---- PHASE 3: self-verify BEFORE reporting success (acp-ajudd#107 FIX 0) ----
    # Re-read every surface and confirm the expected end state. Done while still
    # holding the lock so a concurrent writer can't race the read-back. Any miss is a
    # REAL partial close — exit non-zero with the precise surface so the caller (and
    # the #97 close-safety cue, gated on exit 0) sees a failure, not a false success.
    paths = {
        "session": session_path, "index": index_path, "active": active_path,
        "history": history_path, "worklog": worklog_path, "archive": archive_path,
        "dirty": dirty_path,
    }
    try:
        failures = verify_close(
            paths, args.name, args.item_id.strip(), args.date, set_fm,
            expect_history=bool(history_line), expect_worklog=bool(worklog_entry),
            expect_done=expect_done,
            expect_item_gone=(live_item_path if reconciled else None),
            expect_active_cleared=clear_active)
    finally:
        release_lock(fd, lock_path)

    if failures:
        sys.stderr.write(
            "finish-close: read-back FAILED — close is NOT confirmed (wrote [%s]).\n"
            % ", ".join(written))
        for f in failures:
            sys.stderr.write("  - surface not confirmed: %s\n" % f)
        sys.stderr.write("Re-run to converge (idempotent); do NOT hand-edit surfaces.\n")
        return 5

    print("finish-close: closed %s (%s) — atomic tie-out complete + self-verified."
          % (args.name, args.slug))
    for a in actions:
        print("  - " + a)
    if reconciled:
        # The one-line reconcile note (acp-ajudd#115): signals the mandatory pickup was
        # skipped and the close had to consume the item itself. ASCII-only.
        print("  ! RECONCILED: inbox item %s was STILL LIVE at finish — the mandatory "
              "pickup (/session:start code %s) was skipped. Consumed it now "
              "(fold-then-archive); state-exclusivity (#13) restored."
              % (args.item_id.strip(), args.item_id.strip()))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CloseError as exc:  # defensive — should be caught in phase 1
        sys.stderr.write("finish-close: ABORTED (nothing written) - %s\n" % exc)
        sys.exit(1)
