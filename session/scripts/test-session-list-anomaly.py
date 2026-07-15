#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for session-list.py's #13 state-exclusivity scan (acp-ajudd#99).

Run with a plain interpreter from anywhere:

    python test-session-list-anomaly.py         # or python3

State-exclusivity (acp-ajudd#13): a piece of work is EITHER a live `work` entry OR
a consumed session — never both. The read-time scan warns when an id is present
BOTH live (`_inbox/<id>.md`) AND in `_inbox_archive.md` stamped `[CONSUMED]`/`[DONE]`
— a resurfaced or duplicated id. Warn-only, never auto-fix. Cases:

  CLEAN       — a live id that is NOT archived → no warning (the normal case).
  ANOMALY     — an id live AND archived-consumed → one warning naming that id.
  DONE-DUP    — an id live AND archived with a [DONE] stamp → also flagged.
  PROSE       — an archive block that merely quotes `[consumed]`/`[done]` inline
                (not a line-leading stamp) does NOT arm the archived set, so a
                same-id live file is NOT falsely flagged.
  UNSTAMPED   — an archived block with NO consumed/done stamp does not count as
                "consumed", so a same-id live file is NOT flagged.

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


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def live_item(root, item_id, extra=""):
    fn = item_id.replace("#", "-") + ".md"
    write(os.path.join(root, "_inbox", fn),
          "## %s · [2026-07-15 @ajudd] from testslug / refine (plugin) — an item\n"
          "> [type: work · status: ready]\n%s" % (item_id, extra))


def run():
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "_inbox"))

        # Live items: #10 clean, #20 anomaly, #30 done-dup, #40 prose, #50 unstamped
        for iid in ("acp-ajudd#10", "acp-ajudd#20", "acp-ajudd#30",
                    "acp-ajudd#40", "acp-ajudd#50"):
            live_item(root, iid)

        archive = (
            "# Inbox Archive — testslug\n\n"
            # #20 — line-leading CONSUMED stamp → armed
            "## acp-ajudd#20 · [2026-07-14 @ajudd] from testslug / dispatch (plugin) — dup\n"
            "[CONSUMED 2026-07-15 → session some-session]\n"
            "Body.\n\n---\n\n"
            # #30 — line-leading DONE stamp → armed
            "## acp-ajudd#30 · [2026-07-13 @ajudd] from testslug / dispatch (plugin) — donedup\n"
            "[DONE 2026-07-14 → session other-session]\n"
            "Body.\n\n---\n\n"
            # #40 — only PROSE mentions of the stamps, none line-leading → NOT armed
            "## acp-ajudd#40 · [2026-07-12 @ajudd] from testslug / capture (plugin) — prose\n"
            "This explains `[consumed → session x]` and `[done]` inline only.\n\n---\n\n"
            # #50 — archived but with NO consumed/done stamp → NOT armed
            "## acp-ajudd#50 · [2026-07-11 @ajudd] from testslug / refine (plugin) — unstamped\n"
            "Just an archived note, never consumed.\n"
        )
        write(os.path.join(root, "_inbox_archive.md"), archive)

        warnings = sl.scan_state_exclusivity(root)
        blob = "\n".join(warnings)

        section("CLEAN")
        ok("acp-ajudd#10" not in blob, "live-only id raises no warning")

        section("ANOMALY")
        ok("acp-ajudd#20" in blob, "live + archived-CONSUMED id is flagged")
        ok(sum("acp-ajudd#20" in w for w in warnings) == 1,
           "flagged exactly once")

        section("DONE-DUP")
        ok("acp-ajudd#30" in blob, "live + archived-DONE id is flagged")

        section("PROSE")
        ok("acp-ajudd#40" not in blob,
           "inline-quoted stamps do not arm the archived set (line-anchored)")

        section("UNSTAMPED")
        ok("acp-ajudd#50" not in blob,
           "archived-but-never-consumed id is not flagged")


if __name__ == "__main__":
    run()
    print("\n%d passed, %d failed" % (_passed, _failed))
    sys.exit(1 if _failed else 0)
