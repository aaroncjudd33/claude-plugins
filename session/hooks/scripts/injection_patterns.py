"""
Shared injection-pattern definitions for the session plugin.

SINGLE SOURCE OF TRUTH for both:
  - session-file-guard.py   (PreToolUse Read guard on repo session/memory files)
  - injection-scan.py       (pickup-time capture scan, invoked from start-impl.md)

Do NOT fork this list into either consumer. Import from here.
ASCII-only (Windows cp1252 stdout on the fallback `python`).
"""

import re


INJECTION_PATTERNS = [
    (r"(?i)(ignore|override|forget|disregard)\s+(all\s+)?(previous|prior|earlier|above|system)\s+(instructions?|prompts?|context|directives?|rules?)", "instruction-override"),
    (r"(?i)(you\s+are\s+now|act\s+as\s+(a\s+)?(new|different)|your\s+(new\s+)?(role|instructions?|task|objective)\s+(is|are)\s+)", "persona-injection"),
    (r"(?i)<\s*(system|instructions?|prompt)\s*>", "structural-tag"),
    (r"(?i)^#{1,3}\s*(system\s+prompt|new\s+instructions?|override)\s*$", "header-override"),
    (r"(?im)^\s*\n(ignore|you must|do not follow|disregard)\s+", "mid-content-imperative"),
    (r"(?i)IMPORTANT:\s*(ignore|override|your\s+(new\s+)?instructions?)", "claude-md-override"),
]


def scan_patterns(text):
    """Return a list of 'label -> matched snippet' strings for every injection
    pattern found in text. Empty list means clean. Callers decide what to do
    with a non-empty result (block, warn, etc.)."""
    triggered = []
    for pattern, label in INJECTION_PATTERNS:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            triggered.append('[{0}] matched: "{1}"'.format(label, match.group(0).strip()))
    return triggered
