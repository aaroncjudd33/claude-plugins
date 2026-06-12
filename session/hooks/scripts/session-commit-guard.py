#!/usr/bin/env python3
"""
Git pre-commit hook — session file content guard.
Scans staged .claude/sessions/*.md and .claude/memory/*.md files for:
  1. Secrets / credentials / PII — full content of ALL staged files (including _-prefixed).
  2. Injection patterns — free-form sections of non-_-prefixed session files.
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

# Secrets / credentials / PII. Scanned against the FULL content of every staged
# session/memory file — including _-prefixed (history, context, inbox), which are
# the highest-risk for stranded credentials and PII.
SECRET_PATTERNS = [
    # user/password@host:port — DB connection strings (e.g. Oracle cmsuser/PASS@host:1521)
    (r"[A-Za-z0-9_.-]+/[^@\s:/]{5,}@[\w.-]+:\d{2,5}", "db-connection-credentials"),
    (r"(?i)\b(password|passwd|pwd)\b\s*[:=]\s*\S{4,}", "password-assignment"),
    (r"(?i)\b(secret|token|api[_-]?key|access[_-]?key)\b\s*[:=]\s*[\"']?[A-Za-z0-9/+_.-]{12,}", "secret-token-assignment"),
    (r"\bAKIA[0-9A-Z]{16}\b", "aws-access-key-id"),
    (r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}", "jwt-token"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----", "private-key"),
    # Known PII field names that should never land in a shared repo
    (r"(?i)\b(fedtaxnum|ssn|social[_-]?security|tax[_-]?id|nationalid)\b\s*[:=]?\s*\w", "pii-identity-field"),
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
    """All staged .claude/sessions/ and .claude/memory/ .md files, including _-prefixed."""
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
            files.append(line)
    return files


def get_staged_content(path):
    result = subprocess.run(
        ["git", "show", f":{path}"],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else ""


def _redact(fragment):
    fragment = fragment.strip()
    return fragment if len(fragment) <= 48 else fragment[:48] + "…"


def scan_secrets(content):
    """Scan FULL content for credentials/PII. Applies to every staged file."""
    triggered = []
    for pattern, label in SECRET_PATTERNS:
        match = re.search(pattern, content)
        if match:
            triggered.append(f'  [secret:{label}] matched: "{_redact(match.group(0))}"')
    return triggered


def scan_injection(content):
    """Scan only free-form sections for injection. Applies to non-_ session files."""
    scannable = extract_scannable_sections(content)
    triggered = []
    for pattern, label in INJECTION_PATTERNS:
        match = re.search(pattern, scannable, re.MULTILINE)
        if match:
            triggered.append(f'  [inject:{label}] matched: "{match.group(0).strip()}"')
    return triggered


def main():
    files = get_staged_session_files()
    if not files:
        sys.exit(0)

    blocked = []
    for path in files:
        content = get_staged_content(path)
        if not content:
            continue
        hits = scan_secrets(content)  # secrets: every file, full content
        if not os.path.basename(path.replace("\\", "/")).startswith("_"):
            hits += scan_injection(content)  # injection: non-_ files, sections only
        if hits:
            blocked.append((path, hits))

    if blocked:
        print("\nSession file commit guard — commit blocked.")
        print("Secrets, PII, or instruction injection detected in staged files:\n")
        for path, hits in blocked:
            print(f"  {path}")
            for hit in hits:
                print(hit)
        print("\nResolve the flagged content before committing.")
        print("Credentials/PII should never be git-tracked — exclude the file or scrub the values.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
