---
name: create
description: Orchestrate a full CAB release across four phases. Reads session state and runs the next pending phase automatically. Resumes from where you left off on re-run. Supports Phase A (bundle only) and Phase B (full deploy). Each phase is also callable standalone.
argument-hint: "[BPT2-XXXX BPT2-YYYY ...]"
---

# Release: Create (Orchestrator)

Manages the CAB release lifecycle. Supports two phases that happen at different times:

| Phase | What it does | When |
|-------|--------------|------|
| **A — Bundle** | Create BPT2 tracking story + link feature stories. No branch, no CAB card. | Any time — mid-sprint while stories are still in review |
| **B — Deploy** | Full 4-phase orchestrator: CAB card → release branch → ADF fields → submit for review | When ready to ship |

Each phase persists state so you can stop and resume across sessions or days.

## Phase B Sub-Phases

| Sub-Phase | Command | What it does | When |
|-----------|---------|--------------|------|
| 1 | `/release:cab-card` | Create the CAB card in Jira | Anytime — even before code is merged |
| 2 | `/release:cab-branch` | Create release branch + GitHub PR | After feature PRs are merged to develop |
| 3 | `/release:cab-link` | Populate ADF fields, link stories, register links | After PR is created |
| 4 | `/release:cab-review` | Submit for review, assign Sudhakar | When ready to deploy |

## Instructions

### 1. Load session state

Run `pwd` and extract the repo slug (last path component).

Scan `~/.claude/memory/sessions/<slug>/` for existing release state, in priority order:

**a) Phase B in progress** — any `CAB-*.md` file with `Phase 1 complete: yes` but later phases incomplete. If more than one, pick the most recently updated.

**b) Phase A complete, Phase B pending** — any `.md` file in that directory with `Type: bundle` and `Phase A complete: yes`. If more than one, pick the most recently updated.

**c) No state** — no matching file found. Fresh start.

### 2. Show state and proceed

#### Case A: Phase B in progress

Read the `CAB-*.md` session file. Display current phase state:

```
CAB: <key>  |  <summary>
  Phase 1 — CAB card:        [✓ done | ✗ pending]
  Phase 2 — Branch + PR:     [✓ done (release/<branch>, PR #NNN) | ✗ pending]
  Phase 3 — Fields + links:  [✓ done | ✗ pending]
  Phase 4 — Send for review: [✓ done | ✗ pending]
```

Find the lowest-numbered incomplete sub-phase and execute it (Step 4 below).

#### Case B: Phase A complete, Phase B not yet started

Read the bundle session file. Display:

```
Bundle: <BPT2-key>  |  <summary>
  Phase A — Bundle:    ✓ complete
  Feature stories:     BPT2-XXXX, BPT2-YYYY
  Phase B — Deploy:    ✗ pending
```

Ask: "Start Phase B — create CAB card and begin deploy workflow? (Yes / Stop)"

- **Yes:** proceed to Step 4 with Phase B Phase 1 pending. Pass the bundle story key (`Related BPT2 CAB`) and feature story keys into context so cab-card.md can auto-populate them.
- **Stop:** exit cleanly.

#### Case C: No state — fresh start

If story keys were passed as arguments, use them. Otherwise prompt:
```
Which BPT2 stories are being deployed? (e.g. BPT2-6258 BPT2-6333)
```

Then ask:
```
Release mode:
  [A] Bundle only — create BPT2 tracking story and link stories (no CAB card or branch yet)
  [B] Full release — CAB card, release branch, ADF fields, submit for review
```

- **[A]:** proceed to Phase A flow (Step 3)
- **[B]:** proceed to Phase B Phase 1 (Step 4)

### 3. Phase A flow — Bundle only

#### 3a. Fetch feature stories

For each BPT2 story key, call `getJiraIssue`. Extract summary and status. Warn if any story is not in a deployable state and ask for confirmation before continuing.

#### 3b. Identify or create the BPT2 tracking story

Check if a BPT2 CAB tracking story already exists (a BPT2 story with summary like `CAB - <description>` that bundles these feature stories). The user may have one, or may want to create one.

Prompt:
```
BPT2 tracking story (e.g. BPT2-6334)?
Enter key if it already exists, or press Enter to be prompted to create one.
```

If the user provides a key: call `getJiraIssue` to fetch and confirm.

If not provided: tell the user to create one with `/story:create` using summary `"CAB - <description>"`, then re-run `/release:create` with the new key.

#### 3c. Link feature stories to the tracking story

For each feature story, call `createIssueLink`:
- Type: `Relates`
- Inward issue: BPT2-XXXX (tracking story), Outward issue: BPT2-YYYY (feature story)

#### 3d. Write bundle session file

Write `~/.claude/memory/sessions/<slug>/<bundle-story-key>.md` (e.g. `BPT2-6334.md`):

```
---
updated: [today]
---
# Session State — <bundle-story-key>

- **Type:** bundle
- **Bundle story:** <bundle-story-key>
- **Bundle story summary:** <summary from getJiraIssue>
- **Feature stories:** BPT2-XXXX, BPT2-YYYY
- **Phase A complete:** yes
- **Teams chat:** none
- **Branch:** n/a
- **Last worked on:** Bundled <feature-story-keys> under <bundle-story-key>; ready for Phase B when deployment window is set
- **Open items:** Phase B pending — run /release:create to start CAB card + deploy workflow
- **Next step:** Run /release:create when ready to ship
```

Write `~/.claude/memory/sessions/<slug>/_active` with the bundle story key (e.g. `BPT2-6334`, no `.md`).

#### 3e. Done — Phase A complete

Report:
- Bundle story key + Jira URL
- Feature stories linked
- Next: run `/release:create` when ready to ship; Phase A state will be detected automatically and Phase B will start from there

### 4. Phase B sub-phase execution

Find the lowest-numbered incomplete sub-phase. Read the corresponding command file and follow its instructions:

- **Phase 1 pending:** Read and follow `~/.claude/plugins/marketplaces/ajudd-claude-plugins/release/commands/cab-card.md`
  - If arriving from Phase A (Case B above): pass the bundle story key as the BPT2 CAB key (step 2 of cab-card.md), and the feature story keys as the story list (step 3 of cab-card.md) — no need to re-prompt for these.
- **Phase 2 pending:** Read and follow `~/.claude/plugins/marketplaces/ajudd-claude-plugins/release/commands/cab-branch.md`
- **Phase 3 pending:** Read and follow `~/.claude/plugins/marketplaces/ajudd-claude-plugins/release/commands/cab-link.md`
- **Phase 4 pending:** Read and follow `~/.claude/plugins/marketplaces/ajudd-claude-plugins/release/commands/cab-review.md`
- **All phases complete:** "All phases complete. Run `/release:deploy` when the CAB card is in Implementation status (approved)."

### 5. After each Phase B sub-phase completes

Ask: "Continue to Phase [N+1] — [one-line description of next phase]? (Yes / Stop here)"

- **Yes:** return to step 2, refresh the progress display, and execute the next sub-phase
- **Stop here:** exit cleanly; the session file already has the current state — re-run `/release:create` to continue later
