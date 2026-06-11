#!/usr/bin/env python3
"""
Git pre-commit hook — session file content guard.
Scans staged .claude/sessions/*.md and .claude/memory/*.md files for injection patterns.
Exit 1 blocks the commit; exit 0 allows it.

Install via session:migrate — written into .git/hooks/pre-commit.
"""

import sys
import re
import os
import subprocess


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


def get_staged_session_files():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True
    )
    files = []
    for line in result.stdout.splitlines():
        normalized = line.replace("\\", "/")
        is_session = "/.claude/sessions/" in normalized or normalized.startswith(".claude/sessions/")
        is_memory = "/.claude/memory/" in normalized or normalized.startswith(".claude/memory/")
        if (is_session or is_memory) and normalized.endswith(".md"):
            basename = os.path.basename(normalized)
            if not basename.startswith("_"):
                files.append(line)
    return files


def get_staged_content(path):
    result = subprocess.run(
        ["git", "show", f":{path}"],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else ""


def scan_file(path):
    content = get_staged_content(path)
    if not content:
        return []
    scannable = extract_scannable_sections(content)
    triggered = []
    for pattern, label in INJECTION_PATTERNS:
        match = re.search(pattern, scannable, re.MULTILINE)
        if match:
            triggered.append(f'  [{label}] matched: "{match.group(0).strip()}"')
    return triggered


def main():
    files = get_staged_session_files()
    if not files:
        sys.exit(0)

    blocked = []
    for path in files:
        hits = scan_file(path)
        if hits:
            blocked.append((path, hits))

    if blocked:
        print("\nSession file commit guard — commit blocked.")
        print("Potential instruction injection detected in staged files:\n")
        for path, hits in blocked:
            print(f"  {path}")
            for hit in hits:
                print(hit)
        print("\nResolve the flagged content before committing.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
