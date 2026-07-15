#!/usr/bin/env python3
"""Render the classic-flow "Plugin session — resume existing" display (acp-ajudd#123).

Assembles the deterministic parts of that resume path — the "Resuming <name>"
block and the trailing inbox+reviewed batch prompt — from the session file,
the history file, the consolidated inbox, and plugin.json, so the command
echoes stdout instead of having the model compose the block field-by-field on
every resume. This is the "resume block" leg of #123 (alongside the routing
block and the Step 3 inbox display, both already script-rendered by
routing-block.py / inbox-render.py).

Deliberately narrow scope: this covers ONLY the plugin/personal "resume an
existing session" display in start-plugin-classic.md (soon start-classic.md).
It does not decide anything (no hash-approval gate, no inbox disposition) —
those stay conversational, exactly like session-list.py renders the sessions
table but the model still processes the routing reply afterward.

Reads the inbox via inbox-render.py's `resume` mode as a subprocess (the
single read helper for the consolidated inbox — acp-ajudd#102); this script
does not parse `_inbox/*.md` itself.

Usage:
  resume-block.py --session-root DIR --name NAME --slug SLUG --handle HANDLE
                   [--plugin-root DIR] [--inbox-render PATH]

On success prints the resume block, then a blank line, then the inbox+
reviewed batch prompt (omitted if there's nothing to decide), and exits 0. On
any error exits non-zero with nothing on stdout, so the caller falls back to
composing the block itself. Never raises to the shell.
"""
import argparse
import os
import re
import subprocess
import sys


FIELD_RE = re.compile(r"^-\s+\*\*([^:*]+):\*\*\s*(.*)$")
SUBITEM_RE = re.compile(r"^\s+-\s+(.*)$")
TAG_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2})\s+@(\S+)\]\s*(.*)$")


def parse_session_fields(text):
    """Return {field-name: value}. A field with indented `  - ` sub-bullets
    becomes a list; otherwise the inline text after the colon is the value."""
    lines = text.splitlines()
    fields = {}
    i = 0
    while i < len(lines):
        m = FIELD_RE.match(lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1).strip()
        inline = m.group(2).strip()
        items = []
        j = i + 1
        while j < len(lines):
            im = SUBITEM_RE.match(lines[j])
            if not im:
                break
            items.append(im.group(1).strip())
            j += 1
        fields[name] = items if items else inline
        i = j
    return fields


def tag_split(item):
    """Split a `[date @handle] text` item into (date, handle, text).

    handle is '' for an untagged item (treated as "mine" by the caller, same
    as the prose rule: "item is mine if tagged … matching current user, or
    untagged").
    """
    m = TAG_RE.match(item)
    if not m:
        return "", "", item
    return m.group(1), m.group(2), m.group(3)


def split_mine_theirs(items, handle):
    mine, theirs = [], []
    for it in items or []:
        date, h, text = tag_split(it)
        if not h or h == handle:
            mine.append(it)
        else:
            theirs.append((date, h, text))
    return mine, theirs


def read_history_tail(session_root):
    """(entry_count, last_line) from _history.md, or (0, '') if absent/empty.

    Matches the documented `wc -l` + `tail -n 1` pair byte-for-byte (see
    start-impl.md Step 4 / start-plugin-classic.md's plugin-resume path) —
    raw total line count as "entry count" (it includes the `# History —`
    header and any blank spacer lines, a pre-existing quirk this script
    preserves rather than "fixes", per the behavior-unchanged acceptance
    criterion) and the literal last line, blank or not.
    """
    path = os.path.join(session_root, "_history.md")
    if not os.path.isfile(path):
        return 0, ""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return 0, ""
    lines = text.splitlines()
    if not lines:
        return 0, ""
    return len(lines), lines[-1]


def read_plugin_version(plugin_root):
    """Current version string from <plugin_root>/.claude-plugin/plugin.json, or ''."""
    if not plugin_root:
        return ""
    path = os.path.join(plugin_root, ".claude-plugin", "plugin.json")
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return ""
    m = re.search(r'"version"\s*:\s*"([^"]*)"', text)
    return m.group(1) if m else ""


def major_minor(version):
    parts = (version or "").split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else version


def run_inbox_resume(inbox_render_path, session_root, slug):
    """Invoke inbox-render.py's `resume` mode; return its stdout, or '' on failure."""
    if not inbox_render_path or not os.path.isfile(inbox_render_path):
        return ""
    py = sys.executable or "python3"
    try:
        proc = subprocess.run(
            [py, inbox_render_path, "resume", "--session-root", session_root,
             "--slug", slug, "--current-slug", slug],
            capture_output=True, text=True, encoding="utf-8", timeout=15)
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout


def build_resume_block(fields, name, handle, history_count, history_last, inbox_text):
    out = ["Resuming %s" % name]
    branch = fields.get("Branch", "") or "—"
    out.append("  Branch:      %s" % branch)

    open_items = fields.get("Open items", [])
    if isinstance(open_items, str):
        open_items = [] if open_items.lower() in ("none", "") else [open_items]
    mine, theirs = split_mine_theirs(open_items, handle)
    out.append("  Open items (mine, %d):" % len(mine))
    for it in mine:
        out.append("    - %s" % it)
    if theirs:
        out.append("  Teammate notes (%d — read-only):" % len(theirs))
        for date, h, text in theirs:
            out.append("    - [%s @%s] %s" % (date, h, text))

    if inbox_text:
        for ln in inbox_text.rstrip("\n").splitlines():
            out.append("  %s" % ln)
    else:
        out.append("  Inbox: none")

    next_steps = fields.get("Next steps", [])
    if isinstance(next_steps, str):
        next_steps = [] if next_steps.lower() in ("none", "") else [next_steps]
    ns_mine, ns_theirs = split_mine_theirs(next_steps, handle)
    out.append("  Next steps (mine, %d):" % len(ns_mine))
    for it in ns_mine:
        out.append("    - %s" % it)
    if ns_theirs:
        out.append("  Teammate next steps (%d):" % len(ns_theirs))
        for date, h, text in ns_theirs:
            out.append("    - [%s @%s] %s" % (date, h, text))

    loaded_memories = fields.get("Loaded memories", [])
    if isinstance(loaded_memories, str):
        loaded_memories = [] if loaded_memories.lower() in ("none", "") else [loaded_memories]
    if loaded_memories:
        out.append("  Loaded memories (%d):" % len(loaded_memories))
        for m in loaded_memories:
            out.append("    - %s" % m)

    commits = fields.get("Commits", [])
    if isinstance(commits, str):
        commits = [] if commits.lower() in ("none", "") else [commits]
    if commits:
        recent = commits[:3]
        out.append("  Recent commits (%d):" % len(recent))
        for c in recent:
            out.append("    - %s" % c)

    if history_count:
        out.append("  History:     %d entries — last: %s" % (history_count, history_last))
    else:
        out.append("  History:     none")

    return "\n".join(out) + "\n"


def build_batch_prompt(inbox_text, stored_version, current_version):
    """The "(1)/(2).../(3) Plugin reviewed?" batch line block, or '' if nothing to decide."""
    lines = []
    n = 0
    if inbox_text:
        for ln in inbox_text.splitlines():
            m = re.match(r"^\s*\d+\s+(?:\[\S+\]\s+)?(.+?)\s*—\s*pending\s*$", ln)
            if m:
                n += 1
                lines.append('(%d) Inbox: "%s"  ->  work / done / backlog / keep' % (n, m.group(1)))

    reviewed_line = ""
    if stored_version and current_version and major_minor(stored_version) != major_minor(current_version):
        n += 1
        reviewed_line = "(%d) Plugin reviewed? (last: v%s, current: v%s)  ->  skip / yes" % (
            n, stored_version, current_version)
    elif current_version and not stored_version:
        n += 1
        reviewed_line = "(%d) Plugin reviewed? (last: none, current: v%s)  ->  skip / yes" % (
            n, current_version)

    if reviewed_line:
        lines.append(reviewed_line)

    if not lines:
        return ""
    return "\n".join(lines) + "\n\nReply with overrides or \"go\".\n"


def main():
    ap = argparse.ArgumentParser(
        description="Render the classic-flow plugin-session resume display (acp-ajudd#123).")
    ap.add_argument("--session-root", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--handle", required=True, help="current user handle, sans '@'")
    ap.add_argument("--plugin-root", default="",
                    help="dir holding .claude-plugin/plugin.json, for the reviewed check "
                         "(omit to skip the reviewed line entirely)")
    ap.add_argument("--inbox-render", default="",
                    help="path to inbox-render.py (omit to skip the inbox block)")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    root = os.path.expanduser(args.session_root)
    session_path = os.path.join(root, args.name + ".md")
    try:
        with open(session_path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return 1

    fields = parse_session_fields(text)
    handle = args.handle.lstrip("@")
    history_count, history_last = read_history_tail(root)
    inbox_text = run_inbox_resume(os.path.expanduser(args.inbox_render), root, args.slug)

    resume_block = build_resume_block(fields, args.name, handle, history_count, history_last, inbox_text)

    stored_version = fields.get("Plugin reviewed", "")
    if isinstance(stored_version, list):
        stored_version = stored_version[0] if stored_version else ""
    current_version = read_plugin_version(os.path.expanduser(args.plugin_root)) if args.plugin_root else ""

    batch = build_batch_prompt(inbox_text, stored_version, current_version)

    sys.stdout.write(resume_block)
    if batch:
        sys.stdout.write("\n" + batch)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never break the shell — let the caller fall back
        sys.stderr.write(f"resume-block: {exc}\n")
        sys.exit(1)
