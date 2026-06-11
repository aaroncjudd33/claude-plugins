#!/usr/bin/env python3
"""
PreToolUse hook — session file content guard.
Scans repo session files for injection patterns before Claude reads them.
Blocks if detected; allows through otherwise.
"""

import sys
import json
import re
import os


INJECTION_PATTERNS = [
    (r"(?i)(ignore|override|forget|disregard)\s+(all\s+)?(previous|prior|earlier|above|system)\s+(instructions?|prompts?|context|directives?|rules?)", "instruction-override"),
    (r"(?i)(you\s+are\s+now|act\s+as\s+(a\s+)?(new|different)|your\s+(new\s+)?(role|instructions?|task|objective)\s+(is|are)\s+)", "persona-injection"),
    (r"(?i)<\s*(system|instructions?|prompt)\s*>", "structural-tag"),
    (r"(?i)^#{1,3}\s*(system\s+prompt|new\s+instructions?|override)\s*$", "header-override"),
    (r"(?im)^\s*\n(ignore|you must|do not follow|disregard)\s+", "mid-content-imperative"),
    (r"(?i)IMPORTANT:\s*(ignore|override|your\s+(new\s+)?instructions?)", "claude-md-override"),
]


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
    triggered = []
    for pattern, label in INJECTION_PATTERNS:
        match = re.search(pattern, scannable, re.MULTILINE)
        if match:
            triggered.append(f'  [{label}] matched: "{match.group(0).strip()}"')
    return triggered


def main():
    try:
        tool_input = json.loads(sys.stdin.read())
    except Exception:
        print(json.dumps({"action": "allow"}))
        return

    tool_name = tool_input.get("tool_name", "")
    if tool_name != "Read":
        print(json.dumps({"action": "allow"}))
        return

    file_path = tool_input.get("tool_input", {}).get("file_path", "")
    normalized = file_path.replace("\\", "/")

    # Only scan repo session files and repo memory files (not local ~/.claude/ paths)
    is_session = "/.claude/sessions/" in normalized
    is_memory = "/.claude/memory/" in normalized
    if not (is_session or is_memory) or not normalized.endswith(".md"):
        print(json.dumps({"action": "allow"}))
        return

    # Skip underscore-prefixed files (_active, _inbox, _history, etc.)
    basename = os.path.basename(normalized)
    if basename.startswith("_"):
        print(json.dumps({"action": "allow"}))
        return

    # Skip local ~/.claude/ paths — only scan repo paths
    home = os.path.expanduser("~").replace("\\", "/")
    if normalized.startswith(home + "/.claude/"):
        print(json.dumps({"action": "allow"}))
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        print(json.dumps({"action": "allow"}))
        return

    triggered = scan_content(content)

    if triggered:
        try:
            import subprocess
            has_vscode = subprocess.run(
                ["code", "--version"], capture_output=True, timeout=2
            ).returncode == 0
        except Exception:
            has_vscode = False

        vscode_hint = (
            f'\n\nTo inspect: run `code "{file_path}"`'
            if has_vscode
            else f"\n\nTo inspect: open {basename} in a text editor"
        )

        msg = (
            f"Session file guard — load blocked: {basename}\n"
            f"Potential instruction injection detected:\n"
            + "\n".join(triggered)
            + "\n\nResolve the flagged content before this file can be loaded or hashed."
            + vscode_hint
        )
        print(json.dumps({"action": "block", "message": msg}))
        return

    print(json.dumps({"action": "allow"}))


if __name__ == "__main__":
    main()
