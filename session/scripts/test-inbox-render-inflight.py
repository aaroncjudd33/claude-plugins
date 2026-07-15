#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for inbox-render.py's in-flight display (acp-ajudd#99).

Run with a plain interpreter from anywhere:

    python test-inbox-render-inflight.py         # or python3

The in-flight display surfaces `[CONSUMED … -> session <name>]` archive entries
whose session is still in-progress, so any role can see what happened to an item
without another role narrating it (role-scoped reporting). Cases:

  LIVE        — a consumed entry whose session is in-progress → in-flight row.
  DONE        — the same entry, once a `[DONE]` stamp lands → drops off.
  FINISHED    — a consumed entry whose session is completed → NOT in-flight
                (session-status check is authoritative, even with no [DONE] stamp).
  GONE        — a consumed entry whose session file/index row is gone → NOT
                in-flight (retention-archived → dropped).
  PROSE       — an entry body that merely QUOTES `[done]` / `[consumed -> session]`
                inside backticks is NOT misread as a stamp (line-anchored match).
  ARROWS      — both the unicode → and the ASCII -> consumed arrows parse.

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
IR_PATH = os.path.join(HERE, "inbox-render.py")
_spec = importlib.util.spec_from_file_location("inbox_render", IR_PATH)
ir = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ir)

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


def session_file(root, name, status):
    write(os.path.join(root, name + ".md"),
          "---\nstatus: %s\n---\n\n# Session State — %s\n" % (status, name))


def run():
    with tempfile.TemporaryDirectory() as root:
        # --- sessions: one in-progress, one completed ---------------------
        session_file(root, "role-scoped-reporting", "in-progress")
        session_file(root, "old-shipped-thing", "completed")

        # --- archive fixtures --------------------------------------------
        archive = (
            "# Inbox Archive — testslug\n\n"
            # LIVE: consumed, session in-progress, no DONE → in-flight
            "## acp-ajudd#99 · [2026-07-14 @ajudd] from testslug / capture (plugin) — "
            "Role-scoped reporting discipline\n"
            "[CONSUMED 2026-07-15 → session role-scoped-reporting]\n"
            "> [type: work · status: ready]\n"
            "Body text — nothing quoted.\n\n"
            "---\n\n"
            # FINISHED: consumed but session completed, no DONE → NOT in-flight
            "## acp-ajudd#50 · [2026-07-08 @ajudd] from testslug / dispatch (plugin) — "
            "An older shipped item\n"
            "[CONSUMED 2026-07-08 -> session old-shipped-thing]\n"
            "> [status: ready]\n"
            "Shipped a while ago.\n\n"
            "---\n\n"
            # GONE: consumed, session missing entirely → NOT in-flight
            "## acp-ajudd#40 · [2026-06-01 @ajudd] from testslug / dispatch (plugin) — "
            "Ancient item, session retention-archived\n"
            "[CONSUMED 2026-06-01 → session long-gone-session]\n"
            "Nothing left.\n\n"
            "---\n\n"
            # PROSE: consumed+in-progress BUT the body quotes the stamps inline —
            # must NOT be treated as done, and its own consumed stamp still counts.
            "## acp-ajudd#77 · [2026-07-15 @ajudd] from testslug / capture (plugin) — "
            "Item that documents the stamps\n"
            "[CONSUMED 2026-07-15 → session role-scoped-reporting]\n"
            "This entry explains that rows drop off at `[done]` and shows a "
            "`[consumed → session X]` example inline.\n"
        )
        write(os.path.join(root, "_inbox_archive.md"), archive)

        rows = ir.in_flight_rows(root)
        by_id = {r["id"]: r for r in rows}

        section("LIVE")
        ok("acp-ajudd#99" in by_id, "consumed + in-progress session → in-flight row")
        ok(by_id.get("acp-ajudd#99", {}).get("session") == "role-scoped-reporting",
           "in-flight row names the correct session")

        section("FINISHED")
        ok("acp-ajudd#50" not in by_id,
           "consumed but session completed → NOT in-flight (status authoritative)")

        section("GONE")
        ok("acp-ajudd#40" not in by_id,
           "consumed but session gone → NOT in-flight")

        section("PROSE")
        ok("acp-ajudd#77" in by_id,
           "body quoting `[done]` inline is NOT misread as dropped-off")

        # --- DONE: add a real [DONE] stamp to #99's block → drops off -----
        stamped = archive.replace(
            "[CONSUMED 2026-07-15 → session role-scoped-reporting]\n"
            "> [type: work · status: ready]\n",
            "[CONSUMED 2026-07-15 → session role-scoped-reporting]\n"
            "[DONE 2026-07-16 → session role-scoped-reporting]\n"
            "> [type: work · status: ready]\n", 1)
        write(os.path.join(root, "_inbox_archive.md"), stamped)
        rows2 = {r["id"] for r in ir.in_flight_rows(root)}
        section("DONE")
        ok("acp-ajudd#99" not in rows2, "a line-leading [DONE] stamp drops the row off")

        section("ARROWS")
        # #50 uses ASCII '->', #99/#77 use unicode → — both parsed above (LIVE/PROSE
        # matched via →; the ASCII form is exercised by #50's consumed detection: it
        # was correctly EXCLUDED for session status, not for a parse miss). Assert the
        # regex itself matches both forms directly.
        ok(ir.CONSUMED_RE.search("[CONSUMED 2026-01-01 -> session foo]") is not None,
           "ASCII '->' consumed arrow parses")
        ok(ir.CONSUMED_RE.search("[CONSUMED 2026-01-01 → session foo]") is not None,
           "unicode '→' consumed arrow parses")

        section("EMPTY")
        with tempfile.TemporaryDirectory() as empty:
            ok(ir.render_in_flight(empty) == "",
               "no archive → empty in-flight render (display-only, silent)")


if __name__ == "__main__":
    run()
    print("\n%d passed, %d failed" % (_passed, _failed))
    sys.exit(1 if _failed else 0)
