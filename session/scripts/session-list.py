#!/usr/bin/env python3
"""Render the session:start / session:switch listing as a finished, aligned block.

Deterministic formatting that the model would otherwise generate token-by-token
is done here instead. The command runs this and echoes stdout verbatim.

Reads its own inputs (no data passed in beyond locating args):
  --session-root PATH   directory holding <name>.md, _index.md, _inbox_*.md, _active
  --slug SLUG           repo slug (for the header line)
  --handle HANDLE       current user @handle, sans '@' (for `mine` + active marker)
  --show {default,all,refinement}   which status groups to include (default: default)
  --full                show all 8 columns (adds out-count + created date)
  --status VALUE        restrict to a single status group
  --mine                restrict to sessions created or updated by --handle
  --stale-days N        in-progress sessions not updated in > N days get a ⚠ nudge (default 14)

On success prints the block and exits 0. On ANY error exits non-zero with nothing
on stdout, so the caller falls back to model rendering. Never raises to the shell.
"""
import argparse
import glob
import os
import re
import sys
from datetime import datetime

# In-progress sessions not updated in more than this many days get a ⚠ stale
# marker + a trailing /session:finish nudge. Tune here or override with --stale-days.
STALE_DAYS_DEFAULT = 14


def fmt_date(iso):
    """2026-06-09 -> 'Jun 09'. Pass through anything unparseable."""
    if not iso or iso == "—":
        return "—"
    try:
        return datetime.strptime(iso.strip(), "%Y-%m-%d").strftime("%b %d")
    except ValueError:
        return iso.strip()


def trunc_title(t):
    t = (t or "").strip() or "—"
    if t == "—":
        return "—"
    return (t[:32] + "...") if len(t) > 32 else t


def parse_index(path):
    """Return {name: dict(created_by, created_date, updated_by, updated_date, status, title)}.

    Detects 7-column (current) vs 6-column (legacy) by header column count.
    """
    rows = {}
    if not os.path.isfile(path):
        return rows
    legacy = False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if line.startswith("#"):
                # header comment — detect format from the column-name line
                if "|" in line:
                    cols = [c.strip() for c in line.lstrip("#").split("|")]
                    legacy = len(cols) == 6
                continue
            parts = [p.strip() for p in line.split("|")]
            if legacy and len(parts) >= 6:
                # name | created-by | updated-by | date | status | title
                name, cby, uby, date, status, title = parts[:6]
                rows[name] = dict(
                    created_by=ensure_at(cby), created_date=date,
                    updated_by=ensure_at(uby), updated_date=date,
                    status=status, title=title)
            elif len(parts) >= 7:
                # name | @created-by | created-date | @updated-by | updated-date | status | title
                name, cby, cdate, uby, udate, status, title = parts[:7]
                rows[name] = dict(
                    created_by=ensure_at(cby), created_date=cdate,
                    updated_by=ensure_at(uby), updated_date=udate,
                    status=status, title=title)
    return rows


def ensure_at(h):
    h = (h or "").strip()
    if h and not h.startswith("@") and h != "—":
        return "@" + h
    return h or "—"


def read_session_meta(root, name):
    """Derive an index row directly from a session <name>.md file.

    Used when _index.md is absent or is missing this row, so the listing renders
    correctly with NO committed index (acp-ajudd#49 — the index is a derived cache).
    Returns a dict shaped like a parse_index row, or {} if the file can't be read.
    """
    path = os.path.join(root, name + ".md")
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return {}
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

    def body(field):
        m = re.search(r"^\-\s*\*\*" + field + r":\*\*\s*(.+)$", text, re.MULTILINE)
        return m.group(1).strip() if m else ""

    status = (fm_status or body("Status") or "in-progress").strip()
    updated = (fm_updated or "").strip()
    return dict(
        created_by=ensure_at(body("created-by") or "—"),
        created_date=updated or "—",
        updated_by=ensure_at(body("updated-by") or "—"),
        updated_date=updated or "—",
        status=status,
        title=(body("Title") or "—"),
    )


def write_index(root, slug, meta_by_name):
    """Persist _index.md from derived/known metadata (the render cache — acp-ajudd#49).

    Guarded by the caller so a write failure never breaks the render. The index is
    gitignored in repo-based sessions; this just warms the local cache so the next
    listing is a fast index read instead of a full session-file scan.
    """
    lines = [f"# Session Index — {slug}",
             "# name | created-by | created-date | updated-by | updated-date | status | title"]
    for name in sorted(meta_by_name):
        m = meta_by_name[name]
        lines.append(" | ".join([
            name,
            ensure_at(m.get("created_by", "—")),
            (m.get("created_date") or "—"),
            ensure_at(m.get("updated_by", "—")),
            (m.get("updated_date") or "—"),
            (m.get("status") or "in-progress"),
            (m.get("title") or "—"),
        ]))
    with open(os.path.join(root, "_index.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def count_inbox(session_root, name):
    """Items in _inbox_<name>.md (per-session). Archives excluded. 0 if none."""
    p = os.path.join(session_root, f"_inbox_{name}.md")
    if not os.path.isfile(p):
        return 0
    n = 0
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("## ") or line.startswith("[20"):
                n += 1
    return n


def count_outbox(session_root, name):
    p = os.path.join(session_root, f"_outbox_{name}.md")
    if not os.path.isfile(p):
        return 0
    n = 0
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("## ") or line.startswith("[20"):
                n += 1
    return n


def discover_session_files(session_root):
    """All <name>.md sessions. Skip _-prefixed and *.approved-hash."""
    names, refinement = [], set()
    for p in glob.glob(os.path.join(session_root, "*.md")):
        base = os.path.basename(p)
        if base.startswith("_") or base.endswith(".approved-hash"):
            continue
        name = base[:-3]
        names.append(name)
        if name.startswith("refinement-"):
            refinement.add(name)
    return names, refinement


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session-root", required=True)
    ap.add_argument("--slug", default="")
    ap.add_argument("--handle", default="")
    ap.add_argument("--show", choices=["default", "all", "refinement"], default="default")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--status", default="")
    ap.add_argument("--mine", action="store_true")
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS_DEFAULT)
    ap.add_argument("--rebuild-index", action="store_true",
                    help="when _index.md is absent/incomplete, derive rows from the "
                         "session files and persist the rebuilt cache (acp-ajudd#49)")
    args = ap.parse_args()

    # Windows consoles default to cp1252; the active marker is U+2190. Force UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    root = os.path.expanduser(args.session_root)
    if not os.path.isdir(root):
        return 1  # caller falls back

    index_path = os.path.join(root, "_index.md")
    index_present = os.path.isfile(index_path)
    idx = parse_index(index_path)
    file_names, refinement = discover_session_files(root)

    # Union of index entries and on-disk session files.
    all_names = set(idx) | set(file_names)
    index_incomplete = bool(set(file_names) - set(idx))

    # The index is a derived render cache (acp-ajudd#49). For any on-disk session
    # not represented in the index, derive its row straight from the session file
    # so the listing renders correctly with NO committed index. meta_by_name is the
    # single source the rest of main() reads from.
    meta_by_name = {}
    derived_any = False
    for name in all_names:
        meta = idx.get(name)
        if not meta and name in file_names:
            meta = read_session_meta(root, name)
            if meta:
                derived_any = True
        meta_by_name[name] = meta or {}

    # Self-heal the cache: if asked to rebuild and the index was absent or missing
    # rows, persist the freshly derived index. Guarded — a write failure must never
    # break the render.
    if args.rebuild_index and (not index_present or index_incomplete) and file_names:
        try:
            slug_for_index = args.slug or os.path.basename(root.rstrip("/"))
            write_index(root, slug_for_index, {n: meta_by_name[n] for n in file_names})
            index_incomplete = False
        except Exception:
            pass

    active = ""
    ap_path = os.path.join(root, "_active")
    if os.path.isfile(ap_path):
        with open(ap_path, encoding="utf-8") as fh:
            active = fh.read().strip()

    # Heal a stale _active that points at a completed session (acp-ajudd#94). A
    # completed session can never be the active pointer -- shipping no longer
    # closes, so a session may sit shipped-but-active, but once /session:finish
    # marks it completed the pointer must not survive. Clear it during the
    # rebuild-index pass (run by session:start). Guarded and fail-safe: a stat
    # or unlink error must never break the render.
    if args.rebuild_index and active:
        active_meta = meta_by_name.get(active)
        if not active_meta and active in file_names:
            active_meta = read_session_meta(root, active)
        if active_meta and (active_meta.get("status") or "").strip() == "completed":
            try:
                os.remove(ap_path)
                active = ""
            except OSError:
                pass

    handle = args.handle.lstrip("@")

    # Stale detection: an in-progress session whose updated-date is older than the
    # threshold. Only flags in-progress (completed/paused/refinement never stale).
    # Unparseable or missing dates are treated as not-stale (never a false alarm).
    stale_days = args.stale_days
    try:
        today = datetime.now()
    except Exception:
        today = None

    def is_stale(status, updated_date):
        if today is None or status != "in-progress":
            return False
        try:
            d = datetime.strptime((updated_date or "").strip(), "%Y-%m-%d")
        except ValueError:
            return False
        return (today - d).days > stale_days

    rows = []
    for name in all_names:
        meta = meta_by_name.get(name, {})
        status = (meta.get("status") or "in-progress").strip()
        is_refine = name in refinement
        rows.append(dict(
            name=name,
            title=trunc_title(meta.get("title")),
            status=status,
            inn=count_inbox(root, name),
            out=count_outbox(root, name),
            created_by=meta.get("created_by", "—"),
            created_date=meta.get("created_date", "—"),
            updated_by=meta.get("updated_by", "—"),
            updated_date=meta.get("updated_date", "—"),
            refine=is_refine,
            active=(name == active),
            stale=is_stale(status, meta.get("updated_date", "—")),
        ))

    # Filters
    if args.mine and handle:
        rows = [r for r in rows
                if handle in (r["created_by"].lstrip("@"), r["updated_by"].lstrip("@"))]

    show_completed = args.show == "all" or args.status == "completed"
    show_refine = args.show in ("all", "refinement") or args.status == "refinement"

    def visible(r):
        if r["refine"]:
            return show_refine
        if args.status:
            return r["status"] == args.status
        if r["status"] == "completed":
            return show_completed
        return True

    rows = [r for r in rows if visible(r)]

    # Sort each group by updated_date desc, then name.
    rows.sort(key=lambda r: (r["updated_date"], r["name"]), reverse=True)

    # Group order: in-progress, paused, any other non-completed, refinement, completed.
    def group_key(s):
        order = {"in-progress": 0, "paused": 1}
        return order.get(s, 2 if s != "completed" else 9)

    groups = {}
    for r in rows:
        key = "refinement" if r["refine"] else r["status"]
        groups.setdefault(key, []).append(r)

    # Counts for the summary line (computed over the full set, not the filtered view).
    summary = {"in-progress": 0, "paused": 0, "completed": 0}
    for name in all_names:
        st = (meta_by_name.get(name, {}).get("status") or "in-progress").strip()
        if name in refinement:
            continue
        if st in summary:
            summary[st] += 1

    # Build columns.
    full = args.full
    if full:
        header = ["#", "name", "title", "status", "in", "out", "created", "last edit"]
    else:
        header = ["#", "name", "title", "status", "in", "last edit"]

    def row_cells(i, r):
        last_edit = f"{r['updated_by']} {fmt_date(r['updated_date'])}".strip()
        if full:
            created = f"{r['created_by']} {fmt_date(r['created_date'])}".strip()
            cells = [str(i), r["name"], r["title"], r["status"],
                     str(r["inn"]), str(r["out"]), created, last_edit]
        else:
            cells = [str(i), r["name"], r["title"], r["status"],
                     str(r["inn"]), last_edit]
        return cells

    # Group titles in display order.
    def group_title(key):
        return {"in-progress": "In Progress", "paused": "Paused",
                "completed": "Completed", "refinement": "Refinement"}.get(
            key, key.replace("-", " ").title())

    ordered_keys = sorted(groups, key=lambda k: (group_key(k) if k != "refinement" else 8))

    # Assemble all printable rows to compute column widths.
    printable = []  # (kind, payload)
    n = 0
    for key in ordered_keys:
        printable.append(("group", group_title(key)))
        for r in groups[key]:
            n += 1
            printable.append(("row", (n, r)))

    if n == 0:
        out = []
        slug = args.slug or os.path.basename(root.rstrip("/"))
        out.append(f"Sessions in {slug}")
        out.append("")
        out.append(f"  (no sessions to show — "
                   f"{summary['in-progress']} in-progress · {summary['paused']} paused · "
                   f"{summary['completed']} completed)")
        sys.stdout.write("\n".join(out) + "\n")
        return 0

    # Width per column across header + all data rows.
    matrix = [header]
    for kind, payload in printable:
        if kind == "row":
            i, r = payload
            matrix.append(row_cells(i, r))
    widths = [max(len(row[c]) for row in matrix) for c in range(len(header))]

    def fmt_line(cells, trailing=""):
        parts = [cells[c].ljust(widths[c]) for c in range(len(cells))]
        line = "  " + "  ".join(parts).rstrip()
        return line + trailing

    slug = args.slug or os.path.basename(root.rstrip("/"))
    out = [f"Sessions in {slug}", ""]
    out.append("  " + "  ".join(header[c].ljust(widths[c]) for c in range(len(header))).rstrip())
    for kind, payload in printable:
        if kind == "group":
            out.append("")
            out.append("  " + payload)
        else:
            i, r = payload
            trailing = ""
            if r["active"]:
                trailing += "  ←"
            if r["stale"]:
                trailing += "  ⚠ stale"
            out.append(fmt_line(row_cells(i, r), trailing))
    out.append("")
    out.append(f"  {summary['in-progress']} in-progress · {summary['paused']} paused · "
               f"{summary['completed']} completed")
    stale_shown = sum(1 for r in rows if r["stale"])
    if stale_shown:
        out.append(f"  ⚠ {stale_shown} in-progress not updated in >{stale_days}d — "
                   f"consider /session:finish")
    # Absence is normal, not an error (acp-ajudd#49): rows were derived from the
    # session files above, so the listing is correct regardless. Show the persist
    # hint only when the caller did NOT ask to self-heal the cache (--rebuild-index
    # zeroes index_incomplete on success).
    if index_incomplete and not args.rebuild_index:
        out.append("  (index cache rebuilt from session files — type 'index' to persist it)")

    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never break the shell — let the caller fall back
        sys.stderr.write(f"session-list: {exc}\n")
        sys.exit(1)
