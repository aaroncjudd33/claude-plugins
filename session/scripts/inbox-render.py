#!/usr/bin/env python3
"""inbox-render.py — the single read helper for the per-item consolidated inbox (acp-ajudd#102).

The consolidated / global inbox (`_inbox.md`, plugin/personal + the story/cab/general
global inbox) is stored as **one file per item** under `_inbox/<id>.md` — mirroring how
session files already work. Two sessions touching DIFFERENT items then touch DIFFERENT
files, so the destructive read-modify-write race on the old single `_inbox.md` is
structurally impossible for the common case. (The per-session story/cab `_inbox_<name>.md`
and the single append-only `_inbox_archive.md` are a SEPARATE concern and are untouched.)

Every inbox READ goes through this helper. It does two things, in order:
  1. `ensure_inbox_migrated()` — lazy, self-healing, race-safe conversion of a legacy
     single `_inbox.md` into `_inbox/<id>.md` files. Runs on ANY inbox access (start /
     refine / dispatch / capture / finish / checkpoint / switch / in-flight / search),
     not tied to one command, so going straight to `/session:dispatch` can't skip it.
     Detect: legacy `_inbox.md` with item content AND `_inbox/` not yet populated →
     migrate; empty/absent → no-op. Split behind the same O_EXCL advisory lock
     `inbox-id.py` uses, re-checked inside the lock, idempotent — two sessions detecting
     at once → one migrates, the other no-ops. Not silent: a one-line notice on STDERR
     (like the retention prune).
  2. `render()` — concatenate `_inbox/*.md` (sorted by numeric id) into the exact
     `_inbox.md`-shaped stream the command prose already parses (`## <id> · …` headers +
     `> [type: … · status: …]` lines + bodies, `---`-separated). Printed on STDOUT.

STDOUT is pure inbox content (parse it like the old `_inbox.md`). The migration notice,
if any, is on STDERR — relay it to the user, never fold it into the parsed content.

WRITES do not go through this script — a command that creates / edits / removes ONE item
writes / edits / deletes that one `_inbox/<id>.md` file directly (see the command prose).
This helper is read + migrate only.

Usage:
  inbox-render.py render       --session-root <dir> --slug <slug>   # default; ensure + print stream
  inbox-render.py ensure       --session-root <dir> --slug <slug>   # migrate only, print notice, no stream
  inbox-render.py count        --session-root <dir> --slug <slug>   # ensure + print "work=N capture=M"
  inbox-render.py in-flight    --session-root <dir> --slug <slug>   # print [consumed -> session] rows whose session is still in-progress
  inbox-render.py pickup       --session-root <dir> --slug <slug>   # print the formatted layout-B pickup
                                                                     # list (acp-ajudd#123) — the "Inbox — code
                                                                     # work, or refine new work (N):" block the
                                                                     # plugin/personal classic flow Step 3 shows,
                                                                     # plus the trailing "Captures waiting: N" glance
  inbox-render.py resume       --session-root <dir> --slug <slug>   # print the layout-B "Inbox (N items):"
                                                                     # block (acp-ajudd#123) for the plugin-session
                                                                     # RESUME display, plus the captures-waiting
                                                                     # glance, in that order

In-flight display (acp-ajudd#99): a `[CONSUMED <date> -> session <name>]` archive entry
whose session is still in-progress is surfaced as an "in-flight" row so any role can see
what happened to an item WITHOUT another role having to narrate it (role-scoped reporting —
concurrent inbox churn is expected background state, not report-worthy). Display-only; rows
drop off when the session finishes (a `[DONE]` stamp lands, or the session leaves
in-progress). Rides this #102 read helper — it already knows the archive + session_root.

On ANY error the script exits non-zero with nothing useful on stdout, so a caller can
fall back to reading `_inbox/*.md` (or the legacy `_inbox.md`) directly. Never raises to
the shell.
"""
import argparse
import glob
import os
import re
import sys
import time
from datetime import datetime

# Locking for the migrate read-modify-write — same cross-platform O_EXCL discipline as
# inbox-id.py / finish-close.py (Git-Bash-safe, stale-break, bounded retry). Copied, not
# imported: the sibling "inbox-id.py" filename is not a legal Python module name.
LOCK_RETRIES = 50
LOCK_RETRY_SLEEP = 0.05
LOCK_STALE_SECONDS = 10.0

ITEM_DIRNAME = "_inbox"
LEGACY_FILENAME = "_inbox.md"

# An item block starts at a line beginning with "## ".
HEADER_RE = re.compile(r"^##\s+(.*)$")
# The id is the first token of the header, before " · " (legacy entries have none).
ID_RE = re.compile(r"^(\S+)\s+·")
# Numeric suffix of an id, for sort order.
NUM_RE = re.compile(r"#(\d+)")


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


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def atomic_write(path, content):
    """Write content via temp-file + os.replace (atomic on the same filesystem)."""
    tmp = path + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    os.replace(tmp, path)


def parse_items(text):
    """Split a legacy `_inbox.md` body into item blocks.

    An item starts at a `## ` header line and runs to the next `## ` (or EOF). The
    preamble before the first `## ` (the `# Inbox — <slug>` header + intro blockquote)
    is discarded — render synthesizes the header. `---` separators between entries are
    trimmed off each block. Returns a list of block strings (each starting with `## `).
    """
    lines = text.splitlines()
    blocks = []
    cur = None
    for line in lines:
        if HEADER_RE.match(line):
            if cur is not None:
                blocks.append(cur)
            cur = [line]
        elif cur is not None:
            cur.append(line)
        # lines before the first header are preamble — dropped
    if cur is not None:
        blocks.append(cur)

    out = []
    for b in blocks:
        # Trim trailing blank / `---` separator lines off the block.
        while b and (not b[-1].strip() or b[-1].strip() == "---"):
            b.pop()
        text_block = "\n".join(b).strip()
        if text_block:
            out.append(text_block)
    return out


def id_of(block):
    """Return the item's id (e.g. 'acp-ajudd#97') from its `## <id> · …` header, or None."""
    first = block.splitlines()[0] if block else ""
    m = HEADER_RE.match(first)
    if not m:
        return None
    m2 = ID_RE.match(m.group(1).strip())
    return m2.group(1) if m2 else None


def id_to_filename(item_id, block):
    """Map an item to its `_inbox/<file>.md` name.

    id present → id with '#'→'-' (e.g. 'acp-ajudd#97' → 'acp-ajudd-97.md').
    id absent (legacy) → deterministic 'legacy-<8hex>.md' from the block content, so a
    re-run maps the same block to the same name (idempotent) without needing an id.
    """
    if item_id:
        return item_id.replace("#", "-") + ".md"
    import hashlib
    h = hashlib.sha1(block.encode("utf-8")).hexdigest()[:8]
    return "legacy-%s.md" % h


def sort_key(path):
    """Sort item files by numeric id ascending; id-less files sort last, by name.

    Filenames are '<acronym>-<handle>-<n>.md' (e.g. 'acp-ajudd-97.md'), so the numeric id
    is the trailing '-<n>.md'.
    """
    base = os.path.basename(path)
    m = re.search(r"-(\d+)\.md$", base)
    if m:
        return (0, int(m.group(1)), base)
    return (1, 0, base)


def item_files(item_dir):
    """All `_inbox/*.md` item files, sorted by numeric id. Excludes lock/temp files."""
    if not os.path.isdir(item_dir):
        return []
    paths = [p for p in glob.glob(os.path.join(item_dir, "*.md"))
             if os.path.isfile(p)]
    return sorted(paths, key=sort_key)


def dir_populated(item_dir):
    return bool(item_files(item_dir))


def ensure_inbox_migrated(session_root):
    """Lazy, self-healing, race-safe migration of legacy `_inbox.md` → `_inbox/<id>.md`.

    Returns (migrated_count, notice_or_None). Never raises — a filesystem error degrades
    to "did nothing" so a read is never blocked (the render then falls back to whatever
    storage is present).
    """
    legacy = os.path.join(session_root, LEGACY_FILENAME)
    item_dir = os.path.join(session_root, ITEM_DIRNAME)
    try:
        if not os.path.isfile(legacy):
            return 0, None  # absent → no-op (fresh repo, or already migrated & retired)
        text = read_text(legacy)
    except OSError:
        return 0, None

    items = parse_items(text)
    if not items:
        # Empty legacy shell (header/intro only, no items) → retire it, no notice.
        try:
            os.remove(legacy)
        except OSError:
            pass
        return 0, None

    # Has items → migrate behind the lock (re-check inside).
    lock_path = os.path.join(session_root, "_inbox.migrate.lock")
    fd = acquire_lock(lock_path)
    if fd is None:
        # Could not lock within the bounded wait — another session may be migrating.
        # Do nothing; render falls back to the legacy file this pass. Next read retries.
        return 0, None
    try:
        # Re-read + re-check under the lock — state may have changed since the pre-lock peek.
        if not os.path.isfile(legacy):
            return 0, None
        text = read_text(legacy)
        items = parse_items(text)
        if not items:
            try:
                os.remove(legacy)
            except OSError:
                pass
            return 0, None
        try:
            os.makedirs(item_dir, exist_ok=True)
        except OSError:
            return 0, None
        written = 0
        for block in items:
            fn = id_to_filename(id_of(block), block)
            target = os.path.join(item_dir, fn)
            # Write-if-absent: never clobber a live per-item edit if the dir already
            # holds this id (handles a stray legacy re-appearance being merged in).
            if os.path.exists(target):
                continue
            try:
                atomic_write(target, block.rstrip("\n") + "\n")
                written += 1
            except OSError:
                pass
        # Retire the legacy file — its items now live under _inbox/.
        try:
            os.remove(legacy)
        except OSError:
            pass
        notice = ("Migrated inbox to per-item storage (%d item%s). "
                  "Other terminals on the prior version must restart before touching this inbox."
                  % (written, "" if written == 1 else "s"))
        return written, notice
    finally:
        release_lock(fd, lock_path)


def render(session_root, slug):
    """Return the concatenated inbox stream, `_inbox.md`-shaped, for parsing.

    Reads from `_inbox/*.md`. If the dir is empty/absent but a legacy `_inbox.md` still
    exists (e.g. a lock-contended migration deferred this pass), falls back to printing
    the legacy file verbatim, so a read is always correct.
    """
    item_dir = os.path.join(session_root, ITEM_DIRNAME)
    legacy = os.path.join(session_root, LEGACY_FILENAME)
    header = "# Inbox — %s" % slug

    files = item_files(item_dir)
    if files:
        parts = []
        for p in files:
            try:
                parts.append(read_text(p).strip())
            except OSError:
                continue
        body = "\n\n---\n\n".join(pt for pt in parts if pt)
        return header + "\n\n" + body + "\n"

    if os.path.isfile(legacy):
        try:
            return read_text(legacy)
        except OSError:
            pass
    # Nothing anywhere → an empty inbox (just the header).
    return header + "\n"


# --- In-flight display (acp-ajudd#99) ------------------------------------------
ARCHIVE_FILENAME = "_inbox_archive.md"
# Real disposition stamps are LINE-LEADING (`[CONSUMED …]` / `[DONE …]` on their own
# line), never inline prose. Anchoring to the line start (with `re.MULTILINE`) is what
# keeps an item body that merely *quotes* `[done]` / `[consumed → session]` — like this
# feature's own #99 entry — from being misread as a stamp. The arrow is a unicode → in
# live files; tolerate the ASCII "->" too. The name runs to the closing bracket.
CONSUMED_RE = re.compile(
    r"^\s*\[CONSUMED\s+\S+\s*(?:→|->)\s*session\s+(.+?)\s*\]",
    re.IGNORECASE | re.MULTILINE)
DONE_RE = re.compile(r"^\s*\[DONE\b", re.IGNORECASE | re.MULTILINE)


def _header_title(block):
    """Return the short title after the header's ' — ' (em-dash), or '' if none."""
    first = block.splitlines()[0] if block else ""
    # Split on the LAST ' — ' so a description containing an em-dash is preserved.
    if " — " in first:
        return first.rsplit(" — ", 1)[1].strip()
    if " - " in first:
        return first.rsplit(" - ", 1)[1].strip()
    return ""


def session_status_map(session_root):
    """Map session name -> status. Prefer _index.md; fall back to <name>.md frontmatter.

    The index row is `name | ... | status | title` in both the 7-col current and
    6-col legacy layouts, so status is always the second-to-last column. Never
    raises — an unreadable index yields an empty map and callers degrade gracefully.
    """
    statuses = {}
    index = os.path.join(session_root, "_index.md")
    try:
        with open(index, encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line.strip() or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 6:
                    statuses[parts[0]] = parts[-2].lower()
    except OSError:
        pass
    return statuses


def _status_of(session_root, name, cache):
    """Status of session <name>: index first, then the session file's frontmatter.

    Returns a lowercased status string, or '' when the session cannot be found
    (deleted / retention-archived → treated as no-longer-in-flight by the caller).
    """
    if name in cache:
        return cache[name]
    st = ""
    path = os.path.join(session_root, name + ".md")
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        if text.startswith("---"):
            end = text.find("\n---", 3)
            fm = text[3:end] if end != -1 else ""
            m = re.search(r"^\s*status\s*:\s*(\S+)", fm, re.MULTILINE)
            if m:
                st = m.group(1).strip().lower()
    except OSError:
        st = ""
    cache[name] = st
    return st


def in_flight_rows(session_root):
    """Rows for [consumed -> session] items whose session is still in-progress.

    Reads `_inbox_archive.md`, finds every block carrying a
    `[CONSUMED … -> session <name>]` stamp, and keeps it iff the block has NO
    `[DONE]` stamp AND session <name> is still `in-progress`. (The session-status
    check is authoritative: a legacy consumed block whose session finished long ago
    without a re-stamp still correctly drops off.) Returns a list of
    dicts(id, session, title). Never raises.
    """
    archive = os.path.join(session_root, ARCHIVE_FILENAME)
    try:
        text = read_text(archive)
    except OSError:
        return []
    cache = session_status_map(session_root)
    rows = []
    for block in parse_items(text):
        m = CONSUMED_RE.search(block)
        if not m:
            continue
        if DONE_RE.search(block):
            continue  # dropped off — a [DONE] stamp landed
        name = m.group(1).strip()
        if _status_of(session_root, name, cache) != "in-progress":
            continue  # session finished/paused/gone → no longer in-flight
        rows.append(dict(id=(id_of(block) or "—"),
                         session=name, title=_header_title(block)))
    return rows


def render_in_flight(session_root):
    """Human-readable in-flight block for the board/listing. '' when none."""
    rows = in_flight_rows(session_root)
    if not rows:
        return ""
    out = ["In-flight (%d) — consumed, session still in progress:" % len(rows)]
    idw = max(len(r["id"]) for r in rows)
    for r in rows:
        title = r["title"]
        if len(title) > 60:
            title = title[:57] + "..."
        out.append("  %s  → %s   %s" % (r["id"].ljust(idw), r["session"], title))
    return "\n".join(out) + "\n"


def count_types(session_root, slug):
    """Return (work_count, capture_count) parsed from the rendered stream.

    A capture is `> [type: capture]` (and the legacy `type: note`/`type: data` /
    `status: capture|new|unread`); everything else with a `## ` header is work.
    """
    text = render(session_root, slug)
    work = capture = 0
    blocks = parse_items(text)
    for b in blocks:
        meta = ""
        for ln in b.splitlines()[1:]:
            s = ln.strip()
            if s.startswith("> [") or s.startswith("["):
                meta = s.lower()
                break
            if s and not s.startswith(">"):
                break  # body started, no meta line
        legacy_capture_status = (
            re.search(r"status:\s*(capture|new|unread)\b", meta) is not None
            and "type: work" not in meta)
        is_capture = ("type: capture" in meta or "type: note" in meta
                      or "type: data" in meta or legacy_capture_status)
        if is_capture:
            capture += 1
        else:
            work += 1
    return work, capture


# --- Pickup list rendering (layout B, acp-ajudd#123) ----------------------------
# Formats the "Inbox — code work, or refine new work (N):" block that start-plugin-
# classic.md's Step 3 (plugin/personal) previously had the model compose by hand
# from the raw rendered stream. references/inbox-convention.md § Provenance
# Rendering (layout B) and § Inbox Model are the spec this mirrors.

# `## <id> · [date @handle] from <slug> / <session> (<type>) [spawn] — <description>`
# Every group but the description is optional (legacy entries may omit id, date/
# handle, slug/session, or type) — degrade to showing whatever is present rather
# than breaking, per the convention doc.
#
# The description is split off FIRST (on the LAST ' — '/' - ', same technique as
# this file's own _header_title()) rather than matched inline: a session/slug
# name containing a bare hyphen (e.g. 'feature-x', 'BPT2-1') is otherwise
# indistinguishable from the dash that introduces the description, and an
# inline regex greedily/non-greedily misparses it (verified against exactly
# this case while building this renderer).
PREFIX_RE = re.compile(
    r"^(?:(?P<id>\S+)\s*·\s*)?"
    r"(?:\[(?P<date>\d{4}-\d{2}-\d{2})\s+@(?P<handle>\S+)\]\s*)?"
    r"(?:from\s+(?P<slug>.+?)\s*/\s*(?P<session>.+?)\s*)?"
    r"(?:\((?P<type>[^)]+)\)\s*)?"
    r"(?P<spawn>\[spawn\]\s*)?$"
)


def parse_header(block):
    """Parse a `## <id> · …` header line into its provenance fields.

    Returns a dict with keys id, date, handle, slug, session, type, spawn (bool),
    desc — any of which may be '' (or False for spawn) when the header omits or
    doesn't match that part. Never raises; a header that doesn't match the shape
    at all degrades to desc = the text after '## '.
    """
    first = block.splitlines()[0] if block else ""
    if not first.startswith("## "):
        return dict(id="", date="", handle="", slug="", session="", type="",
                    spawn=False, desc=first)
    rest = first[3:]

    # Split off the description on the FIRST em-dash/hyphen separator (surrounded
    # by spaces, so a hyphen glued inside a name never qualifies) — the provenance
    # prefix (id/date/slug/session/type) never itself contains a spaced dash, so
    # the first one found is always the real separator; splitting on the first
    # (not last) occurrence is what correctly preserves a description that goes
    # on to contain its own em-dash.
    prefix, desc = rest, ""
    for sep in (" — ", " - "):
        if sep in rest:
            prefix, desc = rest.split(sep, 1)
            break

    m = PREFIX_RE.match(prefix.strip())
    if not m:
        return dict(id="", date="", handle="", slug="", session="", type="",
                    spawn=False, desc=desc.strip() or rest.strip())
    g = m.groupdict()
    return dict(
        id=(g.get("id") or "").strip(),
        date=(g.get("date") or "").strip(),
        handle=(g.get("handle") or "").strip(),
        slug=(g.get("slug") or "").strip(),
        session=(g.get("session") or "").strip(),
        type=(g.get("type") or "").strip(),
        spawn=bool(g.get("spawn")),
        desc=desc.strip(),
    )


def parse_type_status(block):
    """Classify an item's `> [type: … · status: …]` line (or its absence/legacy form).

    Returns (kind, status): kind in {'work', 'capture'}; status in
    {'new', 'refining', 'ready', 'in-progress', ''} — '' only for capture (no
    lifecycle). `in-progress` is the lite-pickup stage (references/
    lite-mode.md) — a `work` item being actively built without a
    session file; a session-graduated pickup never lingers in the inbox at
    all (fold-then-archive), so this status is reachable only via a lite
    pickup. Mirrors references/inbox-convention.md § Inbox Model's back-compat
    table. Never raises — anything unrecognized defaults to work/ready (the
    same default the doc gives "no line at all").
    """
    meta = ""
    for ln in block.splitlines()[1:]:
        s = ln.strip()
        if s.startswith("> [") or s.startswith("["):
            meta = s.lower()
            break
        if s and not s.startswith(">"):
            break  # body started before any metadata line — none present
    if not meta:
        return "work", "ready"

    if ("type: capture" in meta or "type: note" in meta or "type: data" in meta
            or "intent: fyi" in meta or "intent: data" in meta):
        return "capture", ""

    has_type_work = "type: work" in meta or "type: story" in meta or "intent: story" in meta

    m = re.search(r"status:\s*(new|refining|ready|in-progress|capture|unread)", meta)
    if m:
        st = m.group(1)
        if st in ("new", "refining", "ready", "in-progress"):
            # Explicit `type: work` (or legacy `type: story`) confirms a work
            # stage; a bare legacy `status: new` with no type prefix at all
            # predates the type axis and meant "unscoped capture" back then.
            # `in-progress` never predates the type axis (it's new with this
            # feature) so it always confirms work regardless of has_type_work.
            if has_type_work or st in ("refining", "ready", "in-progress"):
                return "work", st
            return "capture", ""
        # st in ("capture", "unread") — legacy raw/un-promoted stage.
        return "capture", ""

    if has_type_work:
        return "work", "ready"
    return "work", "ready"


def collect_work_items(session_root, slug):
    """Parse the rendered inbox into (work_items, capture_count).

    work_items is a list of (header_dict, status) tuples, in file order
    (== numeric id order, per item_files' sort_key). Shared by both layout-B
    renderers below (acp-ajudd#123) so the parsing lives in exactly one place.
    """
    text = render(session_root, slug)
    blocks = parse_items(text)
    work_items, capture_count = [], 0
    for b in blocks:
        kind, status = parse_type_status(b)
        if kind == "capture":
            capture_count += 1
            continue
        work_items.append((parse_header(b), status))
    return work_items, capture_count


def _provenance_line(hdr, current_slug):
    """The '     ↳ <slug> / <session> (<type>) · MM-DD' line under an entry, or '' ."""
    prov_slug = hdr["slug"]
    if prov_slug and prov_slug == current_slug:
        prov_slug = ""
    prov_bits = [b for b in (prov_slug, hdr["session"]) if b]
    prov = " / ".join(prov_bits)
    if hdr["type"]:
        prov = (prov + " (%s)" % hdr["type"]) if prov else "(%s)" % hdr["type"]
    date_bit = ""
    if hdr["date"]:
        try:
            date_bit = " · " + datetime.strptime(hdr["date"], "%Y-%m-%d").strftime("%m-%d")
        except ValueError:
            date_bit = " · " + hdr["date"]
    if not (prov or date_bit):
        return ""
    return "     ↳ %s%s" % (prov, date_bit)


def render_pickup(session_root, slug, current_slug):
    """Layout-B pickup list + captures-waiting glance (acp-ajudd#123).

    The classic flow's Step 3 plugin/personal display: "Inbox — code work, or
    refine new work (N):", `· <stage>` suffix on still-scoping work, `[spawn]`
    entries starred. `work` entries only (new/refining/ready) — captures never
    appear in the list, only in the trailing glance count. Empty work list
    prints the "Inbox: none" line instead of a header with N=0.
    """
    work_items, capture_count = collect_work_items(session_root, slug)

    out = []
    if not work_items:
        out.append("Inbox: none — scope new work with 'refine <topic>'")
    else:
        out.append("Inbox — code work, or refine new work (%d):" % len(work_items))
        for i, (hdr, status) in enumerate(work_items, 1):
            desc = hdr["desc"] or "(no description)"
            if hdr["spawn"]:
                desc = "★ [spawn] " + desc
            elif status == "in-progress":
                desc = "%s  · in-progress (lite)" % desc
            elif status in ("new", "refining"):
                desc = "%s  · %s" % (desc, status)
            id_part = ("[%s]  " % hdr["id"]) if hdr["id"] else ""
            out.append("  %d  %s%s" % (i, id_part, desc))
            prov = _provenance_line(hdr, current_slug)
            if prov:
                out.append(prov)

    if capture_count:
        out.append('Captures waiting: %d — say "check captures" to read them' % capture_count)

    return "\n".join(out) + "\n"


def render_resume_inbox(session_root, slug, current_slug):
    """Layout-B inbox block for the plugin-session RESUME display (acp-ajudd#123).

    Same data and provenance rendering as render_pickup, but the plugin/
    personal item-driven model has no in-progress marker for a SESSION
    pickup (pickup consumes immediately — references/inbox-convention.md
    § Lifecycle), so a session-graduated entry never lingers here at all;
    every listed entry is "pending" EXCEPT a `status: in-progress` item,
    which is lite active work still living in the inbox by design
    (references/lite-mode.md) and reads "in progress (lite)"
    instead. The header text also differs ("Inbox (N items):" vs the Step 3
    pickup prompt). Captures-waiting glance is NOT
    included here — the resume display shows it as a separate line only when
    non-zero, same convention, but the caller composes that line itself
    alongside the rest of the resume block's other fields.
    """
    work_items, capture_count = collect_work_items(session_root, slug)

    if not work_items:
        return "Inbox: none\n", capture_count

    out = ["Inbox (%d items):" % len(work_items)]
    for i, (hdr, status) in enumerate(work_items, 1):
        desc = hdr["desc"] or "(no description)"
        if hdr["spawn"]:
            desc = "★ [spawn] " + desc
        id_part = ("[%s]  " % hdr["id"]) if hdr["id"] else ""
        state = "in progress (lite)" if status == "in-progress" else "pending"
        out.append("  %d  %s%s — %s" % (i, id_part, desc, state))
        prov = _provenance_line(hdr, current_slug)
        if prov:
            out.append(prov)
    return "\n".join(out) + "\n", capture_count


def main():
    ap = argparse.ArgumentParser(description="Render / migrate the per-item inbox (acp-ajudd#102).")
    ap.add_argument("command", nargs="?", default="render",
                    choices=["render", "ensure", "count", "in-flight", "pickup", "resume"])
    ap.add_argument("--session-root", required=True,
                    help="dir holding _inbox/ (and any legacy _inbox.md)")
    ap.add_argument("--slug", default="", help="repo slug, for the synthesized header")
    ap.add_argument("--current-slug", default="",
                    help="pickup only: current repo slug, to drop same-repo provenance "
                         "(defaults to --slug when omitted)")
    args = ap.parse_args()

    # Windows consoles default to cp1252; item bodies carry U+2192, em-dashes, etc.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    root = os.path.expanduser(args.session_root)
    slug = args.slug or os.path.basename(root.rstrip("/\\"))

    # Every mode ensures migration first (the whole point — any access migrates).
    _, notice = ensure_inbox_migrated(root)
    if notice:
        sys.stderr.write(notice + "\n")

    if args.command == "ensure":
        # Migration already ran above; nothing on stdout.
        return 0
    if args.command == "count":
        work, capture = count_types(root, slug)
        sys.stdout.write("work=%d capture=%d\n" % (work, capture))
        return 0
    if args.command == "in-flight":
        # Display-only; nothing printed when there is nothing in flight.
        sys.stdout.write(render_in_flight(root))
        return 0
    if args.command == "pickup":
        current_slug = args.current_slug or slug
        sys.stdout.write(render_pickup(root, slug, current_slug))
        return 0
    if args.command == "resume":
        current_slug = args.current_slug or slug
        inbox_block, capture_count = render_resume_inbox(root, slug, current_slug)
        sys.stdout.write(inbox_block)
        if capture_count:
            sys.stdout.write(
                'Captures waiting: %d — say "check captures" to read them\n' % capture_count)
        return 0
    # render (default)
    sys.stdout.write(render(root, slug))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never break the shell — let the caller fall back
        sys.stderr.write("inbox-render: %s\n" % exc)
        sys.exit(1)
