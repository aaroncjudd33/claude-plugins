---
name: status
description: Show the 4-phase CAB release checklist for the active release — read from the local session file only, no live Jira calls.
argument-hint: "[CAB-XXXX]"
---

# /release:status [CAB-XXXX]

Read-only "where am I" view of the current CAB release, sourced entirely from the local
session file — no Jira reads. For the full orchestrator that also executes pending phases,
use `/release:create`.

## Steps

### 1. Resolve session state

Run `pwd` and extract the repo slug (last path component).

Scan `~/.claude/memory/sessions/<slug>/` for release state, using the same resolution as
`/release:create` step 1:

**a) Phase B in progress** — any `CAB-*.md` file with `Phase 1 complete: yes` but later
phases incomplete. If an argument was provided, prefer the file matching that key. Otherwise,
if more than one matches, pick the most recently updated.

**b) Phase A complete, Phase B pending** — any `.md` file with `Type: bundle` and
`Phase A complete: yes`.

**c) No state** — no matching file found.

### 2. Display

#### Case A: Phase B in progress

Read the `CAB-*.md` session file and display:

```
CAB: <key>  |  <summary>
  Phase 1 — CAB card:        [✓ done | ✗ pending]
  Phase 2 — Branch + PR:     [✓ done (release/<branch>, PR #NNN) | ✗ pending]
  Phase 3 — Fields + links:  [✓ done | ✗ pending]
  Phase 4 — Send for review: [✓ done | ✗ pending]

Next step: run /release:create to continue with the next pending phase.
```

#### Case B: Phase A complete, Phase B not started

Read the bundle session file and display:

```
Bundle: <BPT2-key>  |  <summary>
  Phase A — Bundle:    ✓ complete
  Feature stories:     BPT2-XXXX, BPT2-YYYY
  Phase B — Deploy:    ✗ pending

Next step: run /release:create to start Phase B (CAB card + deploy workflow).
```

#### Case C: No state

```
No active release found for this repo. Run /release:create to start one.
```

This command never executes a phase or writes state — it only reads and displays. Use
`/release:create` to act on what it shows.
