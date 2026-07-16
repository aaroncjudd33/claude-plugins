#!/usr/bin/env python3
"""Render the ENTIRE session:start work-zone panel as ONE echoed block (acp-ajudd#132).

Why one script: the work-zone start panel drifted run-to-run (compact In Progress
one run, detailed the next, from the *same* instruction) because the model
assembled it from several script outputs plus generated framing/headers — it had
latitude and used it. This renders the whole panel deterministically so the
command just runs it and echoes stdout verbatim: zero latitude, no drift.

Panel (approved layout, acp-ajudd#130/#132):

    <slug>  ·  work repo  ·  branch: <branch>

    Quick start — type a verb + a target
    ────────────────────────────────────
        refine <n|KEY>   scope / plan a story           (sessionless)
        code   <n|KEY>   open or resume a session       (story or CAB)
        cab    <KEYS>    start a NEW CAB from story keys
        ›  resume anything below by its #   —   e.g.  2  →  CAB-9240

    In Progress   ·   4 active · 7 completed · ⚠ 4 stale (>14d)
    ──────────────────────────────────────────────────────────
        1   BPT2-6479   VO: Bring Claude session & memory…   @ajudd  Jun 10  ⚠
        …

    Advanced  (functionality still being refined)
    ─────────────────────────────────────────────
        inbox    1 item(s)   view the consolidated inbox
        memory   59 notes    search repo memory
        search               find a session, inbox item, or note

    You're on BPT2-6499's branch (completed)   →   code BPT2-6499

Reuses session-list.py's parsing helpers (same dir) so the In Progress rows are
identical to the standalone `sessions` full list. On ANY error, exits non-zero
with nothing on stdout so the caller falls back to model rendering. Never raises.

Usage:
  start-panel.py --session-root PATH --slug SLUG --handle HANDLE
                 [--current-branch REF] [--repo-root PATH] [--limit N]
"""
import argparse
import glob
import importlib.util
import os
import re
import sys
from datetime import datetime


def _load_sibling(filename):
    """Import a hyphen-named sibling script as a module (reuse its helpers)."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, filename)
    spec = importlib.util.spec_from_file_location(
        filename.replace("-", "_").replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TITLE_W = 34


def rule(text):
    """A header line + an underline rule the same visible width."""
    return text + "\n" + ("─" * len(text))


def _count_work_sections(text):
    """Count `work` items (new/refining/ready) in an inbox text blob.

    Handles both per-item files (one `## ` section) and a legacy single
    `_inbox.md` (many sections). Mirrors inbox-render's pickup rule: type==work
    (or absent) AND status in new/refining/ready; capture-type excluded. Tolerates
    the legacy `> [status: …]` form.
    """
    n = 0
    for sec in re.split(r"(?m)^##\s+", text)[1:]:
        m = re.search(r">\s*\[type:\s*([^·\]]+?)\s*·\s*status:\s*([^\]]+?)\s*\]", sec)
        if m:
            typ, sta = m.group(1).strip(), m.group(2).strip()
        else:
            typ, sta = "work", "ready"
            m2 = re.search(r">\s*\[status:\s*([^\]]+?)\s*\]", sec)
            if m2:
                sta = m2.group(1).strip()
                typ = "capture" if sta == "capture" else "work"
        if typ == "work" and sta in ("new", "refining", "ready"):
            n += 1
    return n


def count_inbox_work(session_root):
    """Count consolidated-inbox `work` items — per-item `_inbox/*.md` or legacy `_inbox.md`.

    This is the plugin/personal item-driven inbox model. Story/cab/general repos
    don't use this directory at all (see count_inbox_per_session below) — for them
    this always correctly returns 0, it is not a mismeasurement.
    """
    files = sorted(glob.glob(os.path.join(session_root, "_inbox", "*.md")))
    if files:
        total = 0
        for p in files:
            try:
                with open(p, encoding="utf-8") as fh:
                    total += _count_work_sections(fh.read())
            except OSError:
                continue
        return total
    legacy = os.path.join(session_root, "_inbox.md")
    if os.path.isfile(legacy):
        try:
            with open(legacy, encoding="utf-8") as fh:
                return _count_work_sections(fh.read())
        except OSError:
            return 0
    return 0


def count_inbox_per_session(session_root, sl, names):
    """Sum of story/cab/general per-session inbox files (`_inbox_<name>.md`).

    acp-ajudd#135 iteration 1: the work-zone panel previously only called
    count_inbox_work() above, which reads the plugin/personal `_inbox/` dir — a
    directory story/cab repos never have. So a work repo's real per-session inbox
    content (`_inbox_BPT2-6377.md` etc.) was silently never counted, and the
    Advanced inbox line came out 0 and got hidden even when work was pending.
    Reuses session-list.py's own count_inbox(), which already computes this
    correctly for the full `sessions` listing's per-row `in` column.
    """
    return sum(sl.count_inbox(session_root, name) for name in names)


def count_memory(repo_root):
    """Count repo-memory entries (`- [` lines) in <repo>/.claude/memory/MEMORY.md."""
    if not repo_root:
        return 0
    p = os.path.join(repo_root, ".claude", "memory", "MEMORY.md")
    if not os.path.isfile(p):
        return 0
    n = 0
    try:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("- ["):
                    n += 1
    except OSError:
        return 0
    return n


def build_inprogress(sl, root, handle, stale_days):
    """Return (rows, summary) using session-list's exact parsers for consistency.

    rows: in-progress only, most-recent first, each dict(name,title,updated_by,
    updated_date,stale). summary: dict(active,paused,completed,stale).
    """
    idx = sl.parse_index(os.path.join(root, "_index.md"))
    file_names, refinement = sl.discover_session_files(root)
    all_names = set(idx) | set(file_names)

    # The session FILE is the live source of truth for who/when/status/title
    # (this is what `session-list --rebuild-index` derives, and what showed the
    # correct @handle in the detailed listing). Start from the file, then fill
    # any gaps ("—"/empty) from the index cache. Falls back to pure index when
    # there's no file (index-only rows).
    meta_by_name = {}
    for name in all_names:
        file_meta = sl.read_session_meta(root, name) if name in file_names else {}
        meta = dict(idx.get(name) or {})
        for k, v in (file_meta or {}).items():
            if v and v not in ("—", ""):
                meta[k] = v
        meta_by_name[name] = meta

    try:
        today = datetime.now()
    except Exception:
        today = None

    def is_stale(status, ud):
        if today is None or status != "in-progress":
            return False
        try:
            d = datetime.strptime((ud or "").strip(), "%Y-%m-%d")
        except ValueError:
            return False
        return (today - d).days > stale_days

    rows = []
    summary = {"active": 0, "paused": 0, "completed": 0, "stale": 0}
    for name in all_names:
        if name in refinement:
            continue
        meta = meta_by_name[name]
        status = (meta.get("status") or "in-progress").strip()
        if status == "in-progress":
            summary["active"] += 1
        elif status == "paused":
            summary["paused"] += 1
        elif status == "completed":
            summary["completed"] += 1
        if status != "in-progress":
            continue
        stale = is_stale(status, meta.get("updated_date"))
        if stale:
            summary["stale"] += 1
        # "Who": prefer updated-by; when the (often older) file/index lacks it,
        # fall back to the creator so the column isn't a bare dash.
        who = (meta.get("updated_by") or "—").strip()
        if who in ("", "—"):
            who = (meta.get("created_by") or "—").strip()
        rows.append(dict(
            name=name,
            title=(meta.get("title") or "—"),
            updated_by=who,
            updated_date=meta.get("updated_date", "—"),
            stale=stale,
        ))

    rows.sort(key=lambda r: (r["updated_date"], r["name"]), reverse=True)
    return rows, summary, meta_by_name, all_names


def main():
    ap = argparse.ArgumentParser(description="Render the whole work-zone start panel.")
    ap.add_argument("--session-root", required=True)
    ap.add_argument("--slug", default="")
    ap.add_argument("--handle", default="")
    ap.add_argument("--current-branch", default="")
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--limit", type=int, default=5)
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    root = os.path.expanduser(args.session_root)
    slug = args.slug or os.path.basename(root.rstrip("/")) or "sessions"
    branch = (args.current_branch or "").strip()

    sl = _load_sibling("session-list.py")
    stale_days = getattr(sl, "STALE_DAYS_DEFAULT", 14)

    rows, summary, meta_by_name, all_names = build_inprogress(sl, root, args.handle, stale_days)

    overflow = 0
    if args.limit and len(rows) > args.limit:
        overflow = len(rows) - args.limit
        rows = rows[:args.limit]

    inbox_n = count_inbox_work(root) + count_inbox_per_session(root, sl, all_names)
    mem_n = count_memory(args.repo_root)

    out = []

    # Header line.
    head = f"{slug}  ·  work repo"
    if branch:
        head += f"  ·  branch: {branch}"
    out.append(head)
    out.append("")

    # Quick start (verbs).
    out.append(rule("Quick start — type a verb + a target"))
    out.append("    refine <n|KEY>   scope / plan a story           (sessionless)")
    out.append("    code   <n|KEY>   open or resume a session       (story or CAB)")
    out.append("    cab    <KEYS>    start a NEW CAB from story keys")
    # Example hint — prefer a CAB row so the "resume a CAB by #" point lands.
    ex_i = ex_name = None
    for i, r in enumerate(rows, 1):
        if r["name"].upper().startswith("CAB-"):
            ex_i, ex_name = i, r["name"]
            break
    if ex_name is None and rows:
        ex_i, ex_name = 1, rows[0]["name"]
    if ex_name:
        out.append(f"    ›  resume anything below by its #   —   e.g.  {ex_i}  →  {ex_name}")
    out.append("")

    # In Progress (detailed, capped) with the summary folded into the header.
    bits = [f"{summary['active']} active"]
    if summary["paused"]:
        bits.append(f"{summary['paused']} paused")
    bits.append(f"{summary['completed']} completed")
    if summary["stale"]:
        bits.append(f"⚠ {summary['stale']} stale (>{stale_days}d)")
    out.append(rule("In Progress   ·   " + " · ".join(bits)))
    if rows:
        name_w = max(len(r["name"]) for r in rows)
        for i, r in enumerate(rows, 1):
            title = r["title"].strip() if r["title"].strip() not in ("", "—") else "(untitled)"
            if len(title) > TITLE_W:
                title = title[:TITLE_W - 1] + "…"
            date = sl.fmt_date(r["updated_date"])
            who = r["updated_by"]
            last = f"{who}  {date}".strip() if who not in ("—", "") else date
            mark = "  ⚠" if r["stale"] else ""
            out.append(f"    {i}   {r['name'].ljust(name_w)}   {title.ljust(TITLE_W)}   {last}{mark}".rstrip())
        if overflow:
            out.append(f"    … +{overflow} more — type 'sessions' for the full list")
    else:
        out.append("    (none in progress — start with a verb above)")
    out.append("")

    # Advanced (parked — acp-ajudd#131). Aligned columns: label · count · desc.
    # acp-ajudd#135: a menu line is never hidden because its count is 0 — the line's
    # presence tells the user the capability exists here. A 0 renders as "0", it is
    # not omitted. Only a genuine zone/project-type difference may drop a section.
    out.append(rule("Advanced  (functionality still being refined)"))
    adv = [
        ("inbox", f"{inbox_n} item(s)", "view pending items across session inboxes"),
        ("memory", f"{mem_n} notes", "search repo memory"),
        ("search", "", "find a session, inbox item, or note"),
    ]
    for label, cnt, desc in adv:
        out.append(f"    {label:<8}{cnt:<11}{desc}".rstrip())

    # Branch note — deterministic: extract a key from the branch and offer to
    # code it, but ONLY when that session isn't already shown in the list above
    # (no point pointing at a row the user can already see and number).
    m = re.search(r"(BPT2-\d+|CAB-\d+)", branch, re.I)
    if m:
        key = m.group(1).upper()
        if key not in {r["name"].upper() for r in rows}:
            kmeta = meta_by_name.get(key)
            status = (kmeta.get("status") or "").strip() if kmeta else ""
            suffix = f" ({status})" if status else ""
            out.append("")
            out.append(f"You're on {key}'s branch{suffix}   →   code {key}")

    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never break the shell — let the caller fall back
        sys.stderr.write(f"start-panel: {exc}\n")
        sys.exit(1)
