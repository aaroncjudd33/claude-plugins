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

On success prints the block and exits 0. On ANY error exits non-zero with nothing
on stdout, so the caller falls back to model rendering. Never raises to the shell.
"""
import argparse
import glob
import os
import sys
from datetime import datetime


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
    args = ap.parse_args()

    # Windows consoles default to cp1252; the active marker is U+2190. Force UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    root = os.path.expanduser(args.session_root)
    if not os.path.isdir(root):
        return 1  # caller falls back

    idx = parse_index(os.path.join(root, "_index.md"))
    file_names, refinement = discover_session_files(root)

    # Union of index entries and on-disk session files.
    all_names = set(idx) | set(file_names)
    index_incomplete = bool(set(file_names) - set(idx))

    active = ""
    ap_path = os.path.join(root, "_active")
    if os.path.isfile(ap_path):
        with open(ap_path, encoding="utf-8") as fh:
            active = fh.read().strip()

    handle = args.handle.lstrip("@")

    rows = []
    for name in all_names:
        meta = idx.get(name, {})
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
        st = (idx.get(name, {}).get("status") or "in-progress").strip()
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

    def fmt_line(cells, marker=""):
        parts = [cells[c].ljust(widths[c]) for c in range(len(cells))]
        line = "  " + "  ".join(parts).rstrip()
        return (line + "  ←") if marker else line

    slug = args.slug or os.path.basename(root.rstrip("/"))
    out = [f"Sessions in {slug}", ""]
    out.append("  " + "  ".join(header[c].ljust(widths[c]) for c in range(len(header))).rstrip())
    for kind, payload in printable:
        if kind == "group":
            out.append("")
            out.append("  " + payload)
        else:
            i, r = payload
            out.append(fmt_line(row_cells(i, r), marker="←" if r["active"] else ""))
    out.append("")
    out.append(f"  {summary['in-progress']} in-progress · {summary['paused']} paused · "
               f"{summary['completed']} completed")
    if index_incomplete:
        out.append("  (index missing or incomplete — type 'index' to build it)")

    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never break the shell — let the caller fall back
        sys.stderr.write(f"session-list: {exc}\n")
        sys.exit(1)
