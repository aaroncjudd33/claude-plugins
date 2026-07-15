#!/usr/bin/env python3
"""Render the session:start classic-flow routing block (acp-ajudd#123).

The "Refine / Code" + "Coordinate" + "Search by" text at the end of Step 3 is
100% static per zone — it never varies with data — yet the classic flow
previously had the model reproduce it verbatim on every session:start. That is
the single most repeated fixed cost in the flow. This script prints the exact
same text as a lookup table; the command runs it and echoes stdout verbatim,
the same pattern session-list.py and inbox-render.py already established.

Usage:
  routing-block.py --zone {plugin,personal,work,general}

On success prints the block and exits 0. On any error (bad zone, etc.) exits
non-zero with nothing on stdout, so the caller falls back to writing the block
itself. Never raises to the shell.
"""
import argparse
import sys

SEARCH_BY = """\
  Search by:
    mine             — show only your sessions
    all              — include completed sessions
    full             — show all columns (adds out count + created date)
    status <value>   — filter by in-progress / paused / completed
    <text>           — search name or title, or describe a filter (e.g. "has inbox", "updated by nivi")"""

# Plugin and personal are byte-identical (start-plugin-classic.md documents this
# duplication directly — both zones are item-driven the same way).
PLUGIN_PERSONAL_BLOCK = """\
  Refine / Code:
    refine [target]   — scope work → a `work` entry (planning, sessionless; never a session file)
                        bare = new work · refine <n|id> = edit an existing entry
    code <n|id|name>  — open a coding session (the file decides):
                        a `work` entry (by list <n> / [id]) graduates into a fresh session ·
                        an in-progress session (by name, or its table #) resumes

  Coordinate (advanced):
    dispatch          — assume the dispatch role: read the inbox, sequence/bundle ready work,
                        hand notes to coding sessions (sessionless; runs /session:dispatch)
    capture           — assume the capture role: bank a raw idea (with an optional viability
                        sniff) as a `capture`-type entry for refine to triage
                        (sessionless; runs /session:capture)"""

WORK_BLOCK = """\
  Refine / Code:
    refine [target]     — scope a Jira story (Gathering Requirements; planning, sessionless)
                          bare = list your in-refinement stories · refine BPT2-XXXX = reopen one
    code <n|KEY>        — open a coding session (the file decides):
                          a story KEY graduates (→ In Progress) or resumes its session ·
                          <n> resumes an in-progress session by table row
    code cab BPT2-XXXX… — open a new CAB coding session for those stories"""

GENERAL_BLOCK = """\
  Refine / Code:
    refine [topic]   — scope work verbally (a general repo has no system of record; planning, sessionless)
    code [name]      — open a coding session (the file decides):
                       a name with no session yet → new kickoff · an existing session → resume"""

ZONE_BLOCKS = {
    "plugin": PLUGIN_PERSONAL_BLOCK,
    "personal": PLUGIN_PERSONAL_BLOCK,
    "work": WORK_BLOCK,
    "story": WORK_BLOCK,
    "cab": WORK_BLOCK,
    "general": GENERAL_BLOCK,
}


def main():
    ap = argparse.ArgumentParser(description="Print the classic-flow routing block for a zone.")
    ap.add_argument("--zone", required=True, choices=sorted(set(ZONE_BLOCKS)))
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    block = ZONE_BLOCKS.get(args.zone)
    if not block:
        return 1
    sys.stdout.write(block + "\n\n" + SEARCH_BY + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never break the shell — let the caller fall back
        sys.stderr.write(f"routing-block: {exc}\n")
        sys.exit(1)
