#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for resume-block.py (acp-ajudd#123).

Run with a plain interpreter from anywhere:

    python test-resume-block.py         # or python3

Covers the field-parsing and disposition-gating logic behind the classic
flow's plugin-session resume display:

  FIELDS    — scalar vs list session fields parse correctly.
  MINE      — an untagged item, and one tagged with the current handle, both
              count as "mine"; a different handle's tag counts as teammate.
  NONE      — a literal "none" field value parses as an empty list, not a
              single bogus item.
  REVIEWED  — the "(N) Plugin reviewed?" line appears only when stored and
              current MAJOR.MINOR differ, and is omitted when they match.
  NO-BATCH  — no pending inbox items and no version drift -> empty batch
              block (nothing to decide).

Exit status: 0 if every case passes, 1 otherwise (CI-friendly).
"""
import importlib.util
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
RB_PATH = os.path.join(HERE, "resume-block.py")
_spec = importlib.util.spec_from_file_location("resume_block", RB_PATH)
rb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rb)

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


SAMPLE = """---
updated: 2026-07-15
type: plugin
status: in-progress
---

# Session State — sample-session

- **Type:** plugin
- **Name:** sample-session
- **updated-by:** @ajudd
- **created-by:** @ajudd
- **Teams chat:** Plugin — Aaron Work
- **Scope:** session/
- **Status:** in-progress
- **Branch:** master
- **Last worked on:** 2026-07-15
- **Open items:**
  - [2026-07-15 @ajudd] mine, tagged
  - untagged item, also mine
  - [2026-07-14 @nivi] teammate's item
- **Next steps:** none
- **Plugin reviewed:** 2.9.0
"""


def run():
    fields = rb.parse_session_fields(SAMPLE)

    section("FIELDS")
    ok(fields.get("Branch") == "master", "scalar field parses (Branch)")
    ok(fields.get("Status") == "in-progress", "scalar field parses (Status)")
    ok(isinstance(fields.get("Open items"), list) and len(fields["Open items"]) == 3,
       "list field parses with all sub-items (got %r)" % fields.get("Open items"))

    section("MINE")
    mine, theirs = rb.split_mine_theirs(fields["Open items"], "ajudd")
    ok(len(mine) == 2, "tagged-as-me + untagged both count as mine (got %d)" % len(mine))
    ok(len(theirs) == 1 and theirs[0][1] == "nivi",
       "a different handle's tag counts as teammate (got %r)" % (theirs,))

    section("NONE")
    ok(fields.get("Next steps") == "none",
       "a literal 'none' value stays a scalar string, not a list")
    ns_mine, ns_theirs = rb.split_mine_theirs([], "ajudd")
    ok(ns_mine == [] and ns_theirs == [], "empty list splits to empty/empty, no crash")

    section("REVIEWED")
    batch_diff = rb.build_batch_prompt("", "2.9.0", "2.11.0")
    ok("Plugin reviewed? (last: v2.9.0, current: v2.11.0)" in batch_diff,
       "differing MAJOR.MINOR surfaces the reviewed line (got %r)" % batch_diff)

    batch_same = rb.build_batch_prompt("", "2.11.0", "2.11.0")
    ok("Plugin reviewed?" not in batch_same,
       "matching MAJOR.MINOR omits the reviewed line (got %r)" % batch_same)

    batch_patch_only = rb.build_batch_prompt("", "2.11.0", "2.11.5")
    ok("Plugin reviewed?" not in batch_patch_only,
       "a PATCH-only version bump does not trigger the reviewed line (got %r)" % batch_patch_only)

    section("NO-BATCH")
    ok(rb.build_batch_prompt("", "2.11.0", "2.11.0") == "",
       "no pending inbox items and no version drift -> empty batch block")


if __name__ == "__main__":
    run()
    print("\n%d passed, %d failed" % (_passed, _failed))
    sys.exit(1 if _failed else 0)
