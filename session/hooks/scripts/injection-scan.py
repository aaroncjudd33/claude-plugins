#!/usr/bin/env python3
"""
Pickup-time capture injection scan (acp-ajudd#37).

Invoked from start-impl.md Item Pickup as a SIBLING to the maturity guard:
scan a picked capture's body (and any `ref:` file it points at) for injection
patterns BEFORE the body is folded into the coding session and acted on.

This is the warn-not-block half of the injection defense. It shares the
pattern list with the PreToolUse hook via injection_patterns.py - the Read
hook cannot reach captures by design (local + underscore-prefixed + not
git-tracked), so this is the only scan at the real fold-time trust boundary.

Usage:
  injection-scan.py <file> [<file> ...]   # scan each file's contents
  injection-scan.py --stdin               # scan stdin (e.g. a capture body)

Output (stdout, ASCII-only):
  clean  -> prints "CLEAN" and exits 0
  hit    -> prints "INJECTION DETECTED" + one line per match, exits 3
An unreadable file is NOT treated as a hit (can't-scan != injection): prints a
"could not read" note to stderr and continues; exits 0 if nothing else hit.
Warn-not-block: this script never blocks anything itself - the caller
(start-impl.md) surfaces a hit and asks the user to confirm the fold.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from injection_patterns import scan_patterns  # noqa: E402


def _scan_text(text, source_label):
    hits = scan_patterns(text)
    return [(source_label, h) for h in hits]


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("usage: injection-scan.py <file> [<file> ...] | --stdin\n")
        return 0  # nothing to scan -> not a hit

    all_hits = []

    if args[0] == "--stdin":
        try:
            text = sys.stdin.read()
        except Exception:
            sys.stderr.write("injection-scan: could not read stdin\n")
            return 0
        all_hits.extend(_scan_text(text, "capture body"))
    else:
        for path in args:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                sys.stderr.write("injection-scan: could not read {0} (skipped)\n".format(path))
                continue
            all_hits.extend(_scan_text(text, path))

    if all_hits:
        print("INJECTION DETECTED")
        for source_label, hit in all_hits:
            print("  {0}: {1}".format(source_label, hit))
        return 3

    print("CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
