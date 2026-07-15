#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for session-list.py's encoding-health guard (acp-ajudd#114).

Run with a plain interpreter from anywhere:

    python test-session-list-encoding.py         # or python3

Guards the detect-and-warn guard #114 added: PS 5.1 `Get-Content -Raw` /
`Set-Content -Encoding UTF8` round-trips a UTF-8 session/inbox file through
cp1252, double-encoding every non-ASCII glyph and adding a BOM. The guard
auto-strips a lone BOM (safe, idempotent) and flags mojibake for MANUAL repair
(never auto-reversed). Cases:

  BOM        — a UTF-8 BOM is stripped, remaining bytes preserved verbatim,
               one notice emitted; a second pass is a silent no-op (idempotent).
  MOJIBAKE   — a genuinely mojibaked file is flagged AND left byte-for-byte
               unchanged (no auto-reverse — the #114 hard rule).
  CLEAN      — real UTF-8 glyphs (dot / em-dash / arrow) survive untouched and
               raise no warning (no false positive on correct content).
  DOC        — a file that only *quotes* the markers inside backticks (this very
               feature's own documentation) is NOT flagged (_strip_code_spans).
  INBOX      — per-item _inbox/*.md files are in scope, not just root *.md.

Exit status: 0 if every case passes, 1 otherwise (CI-friendly).
"""
import importlib.util
import os
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DOT = "·"     # U+00B7 -> mojibakes to "Â·"
DASH = "—"    # U+2014 -> mojibakes to "â€”"
ARROW = "→"   # U+2192 -> mojibakes to "â†”"
BOM = b"\xef\xbb\xbf"

HERE = os.path.dirname(os.path.abspath(__file__))
SL_PATH = os.path.join(HERE, "session-list.py")

_spec = importlib.util.spec_from_file_location("session_list", SL_PATH)
sl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sl)

_passed = 0
_failed = 0


def ok(cond, label):
    global _passed, _failed
    if cond:
        _passed += 1
        print("  PASS  " + label)
    else:
        _failed += 1
        print("  FAIL  " + label)


def section(title):
    print("\n== %s ==" % title)


def mojibake(text):
    """Reproduce the exact PS 5.1 corruption: UTF-8 bytes misread as cp1252,
    then re-encoded as UTF-8 (a single uniform round-trip)."""
    return text.encode("utf-8").decode("cp1252").encode("utf-8")


def run():
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "_inbox"))

        # --- fixtures -----------------------------------------------------
        clean_body = ("## acp-ajudd#1 %s [2026-07-15 @ajudd] %s title %s done\n"
                      "Body %s with %s and %s\n" % (DOT, DASH, ARROW, DOT, DASH, ARROW))
        clean = os.path.join(root, "clean.md")
        with open(clean, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(clean_body)
        clean_bytes = open(clean, "rb").read()

        bommed = os.path.join(root, "bommed.md")
        with open(bommed, "wb") as fh:
            fh.write(BOM + clean_body.encode("utf-8"))

        doc = os.path.join(root, "doc.md")
        with open(doc, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# note\nWe detect markers (`Â`, `â€`, "
                     "`â†`, `Ã`) and glyphs `%s`/`%s`/`%s`.\n"
                     % (DOT, DASH, ARROW))

        moji = os.path.join(root, "_inbox", "acp-ajudd-999.md")
        with open(moji, "wb") as fh:
            fh.write(mojibake(clean_body))
        moji_bytes = open(moji, "rb").read()

        # --- first scan ---------------------------------------------------
        notices, warnings = sl.scan_encoding_health(root)
        nrel = "\n".join(notices)
        wrel = "\n".join(warnings)

        section("BOM")
        ok(any("bommed.md" in n for n in notices), "BOM file produces a notice")
        ok(not open(bommed, "rb").read().startswith(BOM), "BOM stripped from file")
        ok(open(bommed, "rb").read() == clean_body.encode("utf-8"),
           "post-strip bytes identical to the BOM-less original")

        section("CLEAN")
        ok("clean.md" not in wrel and "clean.md" not in nrel,
           "clean UTF-8 glyphs raise no warning/notice")
        ok(open(clean, "rb").read() == clean_bytes, "clean file left untouched")

        section("DOC")
        ok("doc.md" not in wrel, "backtick-quoted markers are NOT flagged")

        section("MOJIBAKE")
        ok(any("acp-ajudd-999.md" in w for w in warnings),
           "mojibaked inbox item is flagged")
        ok(open(moji, "rb").read() == moji_bytes,
           "mojibaked file left byte-identical (no auto-reverse)")

        section("INBOX scope")
        ok(any("_inbox" in w and "999" in w for w in warnings),
           "per-item _inbox/*.md files are scanned")

        # --- idempotency --------------------------------------------------
        notices2, warnings2 = sl.scan_encoding_health(root)
        section("IDEMPOTENT")
        ok(not any("bommed.md" in n for n in notices2),
           "second pass emits no BOM notice (already stripped)")
        ok(any("acp-ajudd-999.md" in w for w in warnings2),
           "mojibake still flagged on re-scan (persists until manual repair)")


if __name__ == "__main__":
    run()
    print("\n%d passed, %d failed" % (_passed, _failed))
    sys.exit(1 if _failed else 0)
