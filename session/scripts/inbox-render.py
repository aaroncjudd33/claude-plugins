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
        notice = ("Migrated inbox to per-item storage (%d item%s)."
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


def main():
    ap = argparse.ArgumentParser(description="Render / migrate the per-item inbox (acp-ajudd#102).")
    ap.add_argument("command", nargs="?", default="render",
                    choices=["render", "ensure", "count"])
    ap.add_argument("--session-root", required=True,
                    help="dir holding _inbox/ (and any legacy _inbox.md)")
    ap.add_argument("--slug", default="", help="repo slug, for the synthesized header")
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
    # render (default)
    sys.stdout.write(render(root, slug))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never break the shell — let the caller fall back
        sys.stderr.write("inbox-render: %s\n" % exc)
        sys.exit(1)
