---
name: create
description: Orchestrate a full CAB release across four phases. Reads session state and runs the next pending phase automatically. Resumes from where you left off on re-run. Each phase is also callable standalone.
argument-hint: "[BPT2-XXXX BPT2-YYYY ...]"
---

# Release: Create (Orchestrator)

Manages the full CAB release lifecycle across four phases. Each phase persists state so you can stop at any point and resume later — even across sessions or days.

| Phase | Command | What it does | When |
|-------|---------|--------------|------|
| 1 | `/release:cab-card` | Create the CAB card in Jira | Anytime — even before code is merged |
| 2 | `/release:cab-branch` | Create release branch + GitHub PR | After feature PRs are merged to develop |
| 3 | `/release:cab-link` | Populate ADF fields, link stories, register links | After PR is created |
| 4 | `/release:cab-review` | Submit for review, assign Sudhakar | When ready to deploy |

## Instructions

### 1. Load session state

Run `pwd` and extract the repo slug (last path component). Read `~/.claude/memory/sessions/<slug>/_active` to get the active session name.

If the active session name starts with `CAB-`, read `~/.claude/memory/sessions/<slug>/<name>.md` to load phase state.

Otherwise, check for any `CAB-*.md` file in `~/.claude/memory/sessions/<slug>/` that has `Phase 1 complete: yes` but later phases incomplete — this is a resumable CAB from a prior session. If one is found, confirm: "Resume [CAB-XXXX]? (Yes / Start new)"

If no CAB session state exists, treat all phases as pending and proceed to step 3 (Phase 1 will initialize the session file).

### 2. Show progress

Display current phase state:

```
CAB: <key or "not yet created">
  Phase 1 — CAB card:        [✓ done | ✗ pending]
  Phase 2 — Branch + PR:     [✓ done (release/<branch>, PR #NNN) | ✗ pending]
  Phase 3 — Fields + links:  [✓ done | ✗ pending]
  Phase 4 — Send for review: [✓ done | ✗ pending]
```

### 3. Execute next pending phase

Find the lowest-numbered incomplete phase. Read the corresponding command file and follow its instructions:

- **Phase 1 pending:** Read and follow `~/.claude/plugins/marketplaces/ajudd-claude-plugins/release/commands/cab-card.md`
- **Phase 2 pending:** Read and follow `~/.claude/plugins/marketplaces/ajudd-claude-plugins/release/commands/cab-branch.md`
- **Phase 3 pending:** Read and follow `~/.claude/plugins/marketplaces/ajudd-claude-plugins/release/commands/cab-link.md`
- **Phase 4 pending:** Read and follow `~/.claude/plugins/marketplaces/ajudd-claude-plugins/release/commands/cab-review.md`
- **All phases complete:** "All phases complete. Run `/release:deploy` when the CAB card is in Implementation status (approved)."

### 4. After each phase completes

Ask: "Continue to Phase [N+1] — [one-line description of next phase]? (Yes / Stop here)"

- **Yes:** return to step 2, refresh the progress display, and execute the next phase
- **Stop here:** exit cleanly; the session file already has the current state — re-run `/release:create` to continue later
