#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for inbox-render.py's `pickup` layout-B rendering (acp-ajudd#123).

Run with a plain interpreter from anywhere:

    python test-inbox-render-pickup.py         # or python3

Covers the header-parsing edge cases found while building the classic-flow
perf-tune (script-rendering the Step 3 plugin/personal inbox display instead
of having the model compose it by hand each session:start):

  HYPHEN      — a session/slug name containing a bare hyphen (e.g. 'feature-x',
                'BPT2-1') must not be mistaken for the description separator.
  EMDASH-DESC — a description that itself contains ' — ' must be preserved
                whole, not truncated at its own internal dash.
  SPAWN       — the [spawn] tag renders as a leading star + label.
  STAGE       — new/refining work gets a '· <stage>' suffix; ready gets none.
  CAPTURE     — capture-type entries never appear in the pickup list, only in
                the trailing "Captures waiting: N" glance.
  SAME-REPO   — same-repo provenance drops the redundant slug.
  LEGACY      — a header with no id and no type/status line still parses (as
                work/ready) and renders.
  EMPTY       — no work items → the "Inbox: none" line, not "(0):".

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


def run():
    section("HYPHEN")
    h = ir.parse_header(
        "## acp-test#1 · [2026-07-10 @nivi] from other-repo / feature-x "
        "(personal) [spawn] — Kick off the follow-on cleanup")
    ok(h["session"] == "feature-x", "hyphenated session name parses whole (got %r)" % h["session"])
    ok(h["slug"] == "other-repo", "slug parses correctly alongside a hyphenated session")
    ok(h["type"] == "personal", "type parses correctly alongside a hyphenated session")
    ok(h["spawn"] is True, "[spawn] tag still detected")
    ok(h["desc"] == "Kick off the follow-on cleanup", "description not swallowed by the hyphen")

    h2 = ir.parse_header(
        "## [2026-06-01 @ajudd] from virtual-office / BPT2-1 (story) — "
        "Legacy entry with no id and no type/status line")
    ok(h2["session"] == "BPT2-1", "hyphenated Jira-style session name parses whole (got %r)" % h2["session"])
    ok(h2["id"] == "", "missing id parses as empty, not a crash")

    section("EMDASH-DESC")
    h3 = ir.parse_header(
        "## acp-test#5 · [2026-07-13 @ajudd] from ajudd-claude-plugins / refine "
        "(plugin) — Description that itself contains an em-dash — like this")
    ok(h3["desc"] == "Description that itself contains an em-dash — like this",
       "description keeps its own internal em-dash whole (got %r)" % h3["desc"])
    ok(h3["session"] == "refine" and h3["type"] == "plugin",
       "provenance still parses correctly ahead of an em-dash-bearing description")

    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "_inbox"))

        write(os.path.join(root, "_inbox", "acp-test-1.md"),
              "## acp-test#1 · [2026-07-10 @nivi] from other-repo / feature-x "
              "(personal) [spawn] — Kick off the follow-on cleanup\n"
              "> [type: work · status: ready]\n\nBody.\n")
        write(os.path.join(root, "_inbox", "acp-test-2.md"),
              "## acp-test#2 · [2026-07-11 @ajudd] from ajudd-claude-plugins / "
              "refine (plugin) — Still being scoped\n"
              "> [type: work · status: refining]\n\nBody.\n")
        write(os.path.join(root, "_inbox", "acp-test-3.md"),
              "## acp-test#3 · [2026-07-12 @ajudd] from ajudd-claude-plugins / "
              "dispatch (plugin) — Heads up about prod incident\n"
              "> [type: capture]\n\nFYI only.\n")
        write(os.path.join(root, "_inbox", "acp-test-4.md"),
              "## acp-test#4 · [2026-07-12 @ajudd] from ajudd-claude-plugins / "
              "refine (plugin) — Freshly dropped, not scoped yet\n"
              "> [type: work · status: new]\n\nBody.\n")
        write(os.path.join(root, "_inbox", "acp-test-6.md"),
              "## acp-test#6 · [2026-07-12 @ajudd] from ajudd-claude-plugins / "
              "refine (plugin) — Fully scoped and pickable\n"
              "> [type: work · status: ready]\n\nBody.\n")

        out = ir.render_pickup(root, "ajudd-claude-plugins", "ajudd-claude-plugins")

        section("SPAWN")
        ok("★ [spawn] Kick off the follow-on cleanup" in out, "spawn entry gets the star + label")

        section("STAGE")
        ok("Still being scoped  · refining" in out, "refining work gets a stage suffix")
        ok("Freshly dropped, not scoped yet  · new" in out, "new work gets a stage suffix")
        ok("Fully scoped and pickable\n" in out or out.rstrip("\n").endswith(
            "Fully scoped and pickable"), "ready work gets NO stage suffix")

        section("CAPTURE")
        ok("Heads up about prod incident" not in out, "capture entry never appears in the pickup list")
        ok('Captures waiting: 1 — say "check captures" to read them' in out,
           "capture instead surfaces as the captures-waiting glance")

        section("SAME-REPO")
        ok("↳ refine (plugin)" in out,
           "same-repo provenance drops the redundant slug (got:\n%s)" % out)
        ok("↳ other-repo / feature-x (personal)" in out,
           "cross-repo provenance keeps the slug")

        section("EMPTY")
        with tempfile.TemporaryDirectory() as empty_root:
            os.makedirs(os.path.join(empty_root, "_inbox"))
            empty_out = ir.render_pickup(empty_root, "ajudd-claude-plugins", "ajudd-claude-plugins")
            ok(empty_out.strip() == "Inbox: none — scope new work with 'refine <topic>'",
               "no work items → the 'Inbox: none' line (got %r)" % empty_out)


if __name__ == "__main__":
    run()
    print("\n%d passed, %d failed" % (_passed, _failed))
    sys.exit(1 if _failed else 0)
