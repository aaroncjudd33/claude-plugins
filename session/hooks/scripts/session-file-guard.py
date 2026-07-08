#!/usr/bin/env python3
"""
PreToolUse hook - session file content guard.
Scans repo session files for injection patterns before Claude reads them.
Denies the Read if detected; otherwise stays out of the way.

PURELY ADDITIVE by design. This hook matches ^Read$, so it runs on EVERY Read
in every project while the plugin is enabled. It therefore must never emit
permissionDecision:"allow" - "allow" force-approves the Read and BYPASSES any
Read permission rule the user/teammate has configured. The only decision this
guard ever puts on the wire is "deny", and only on a real injection hit. On
every other path (clean scan, skipped path, parse/read error) it emits NOTHING
and exits 0 - the canonical no-op that lets normal permission flow proceed.

Emits the documented PreToolUse permission contract (permissionDecision +
exit 0). The old {"action": ...} shape is NOT a recognized contract - it was
silently ignored, so every intended block failed open. See repo CLAUDE.md
(hook conventions) and acp-ajudd#36.

Fail-open on any parse/read error: emit nothing and exit 0 - an enforcement bug
must never wedge a normal Read, and must never force-approve one either.
ASCII-only messages (Windows cp1252 stdout on the `python` fallback).
"""

import sys
import json
import re
import os

# Import the shared injection-pattern list (single source of truth). The hook
# is invoked by file path, so cwd is not this dir - add it to sys.path first.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from injection_patterns import scan_patterns  # noqa: E402


def _deny(reason):
    """Print a PreToolUse deny decision. This is the ONLY decision the guard
    ever emits - clean/skip/error paths print nothing (see module docstring)."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def extract_scannable_sections(content):
    """Return only free-form fields: Open items, Next steps, Notes. Skip structured metadata."""
    sections = []
    in_section = False
    for line in content.splitlines():
        if re.match(r"^\- \*\*(Open items|Next steps?|Notes)\*\*", line):
            in_section = True
        elif re.match(r"^\- \*\*\w", line) and in_section:
            in_section = False
        if in_section:
            sections.append(line)
    return "\n".join(sections)


def scan_content(content):
    scannable = extract_scannable_sections(content)
    return scan_patterns(scannable)


def main():
    # Every early return below is a silent no-op (no stdout, exit 0) so normal
    # permission flow proceeds. Only a confirmed injection hit emits a decision.
    try:
        tool_input = json.loads(sys.stdin.read())
    except Exception:
        return  # fail-open: let normal flow proceed, never force-allow

    tool_name = tool_input.get("tool_name", "")
    if tool_name != "Read":
        return

    file_path = tool_input.get("tool_input", {}).get("file_path", "")
    normalized = file_path.replace("\\", "/")

    # Only scan repo session files and repo memory files (not local ~/.claude/ paths)
    is_session = "/.claude/sessions/" in normalized
    is_memory = "/.claude/memory/" in normalized
    if not (is_session or is_memory) or not normalized.endswith(".md"):
        return

    # Skip underscore-prefixed files (_active, _inbox, _history, etc.)
    basename = os.path.basename(normalized)
    if basename.startswith("_"):
        return

    # Skip local ~/.claude/ paths - only scan repo paths
    home = os.path.expanduser("~").replace("\\", "/")
    if normalized.startswith(home + "/.claude/"):
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return  # fail-open

    triggered = scan_content(content)
    if not triggered:
        return  # clean: no-op, normal permission flow proceeds

    try:
        import subprocess
        has_vscode = subprocess.run(
            ["code", "--version"], capture_output=True, timeout=2
        ).returncode == 0
    except Exception:
        has_vscode = False

    vscode_hint = (
        'To inspect: run `code "{0}"`'.format(file_path)
        if has_vscode
        else "To inspect: open {0} in a text editor".format(basename)
    )

    reason = (
        "Session file guard blocked load of {0} - potential instruction "
        "injection detected: ".format(basename)
        + " ".join(triggered)
        + ". Resolve the flagged content before this file can be loaded or hashed. "
        + vscode_hint
    )
    _deny(reason)


if __name__ == "__main__":
    main()
