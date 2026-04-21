---
name: cab-card
description: Phase 1 — Create the CAB card (IT Software Change in Jira). Can be run before code is merged. Prompts for story keys, deploy date, and defaults, then creates the card and initializes the release session file.
argument-hint: "[BPT2-XXXX BPT2-YYYY ...]"
---

# Release: CAB Card (Phase 1)

Creates the CAB card in Jira and initializes the release session file. This phase can run before any code is merged — you only need to know which stories are bundling.

**Terminology:**
- **BPT2 CAB** — BPT2 story prefixed `CAB -` that bundles the feature stories (created via `/story:create`)
- **BPT2 stories** — feature/bug-fix stories being deployed
- **CAB card** — IT Software Change in the CAB Jira project (what this phase creates)

## Instructions

### 1. Load context

Run `pwd` and extract the repo slug (last path component).

Silently collect:
- Story keys from command arguments (if any)
- Memory files → active session, known story keys, BPT2 CAB key
- Current git branch

### 2. Check for BPT2 CAB

Look in memory and conversation context for a BPT2 CAB story (a BPT2 story prefixed `CAB -` that bundles feature stories for this release).

If not found, prompt:
```
Do you have a BPT2 CAB story for this release? (e.g. BPT2-6334)
If not, create one first with /story:create (summary: "CAB - <description>").
Press Enter to skip if deploying without a BPT2 CAB.
```

Store the BPT2 CAB key if provided.

### 3. Fetch BPT2 stories

For each BPT2 story key (from arguments, memory, or prompt), call `getJiraIssue`.

Extract: **Summary**, **Description/acceptance criteria**, **Status**, **Component/label**.

Warn if any story is not in a deployable state (Done / Ready for Deploy). Ask the user to confirm before continuing.

If no story keys are available, prompt:
```
Which BPT2 stories are being deployed? (e.g. BPT2-6258 BPT2-6333)
```

### 4. Prompt required inputs

Present with pre-seeded defaults from story data. User presses Enter to accept or types a replacement.

```
=== CAB Card Creation ===

Summary:           [inferred — e.g. "BP2 - Gen Leadership Bonus - Shopify Enrollment + Alarm Fix"]
Deploy date/time:  [none — user must provide, e.g. "Friday 1pm MDT"]
What's deploying:  [seeded from story summaries — confirm or refine]
```

### 5. Prompt configurable defaults

```
=== Defaults (Enter to accept all, or type numbers to change) ===

 1. CAB Impact:                 Low
 2. CAB Risk:                   Low
 3. CAB Request Type:           Standard
 4. Requires Outage Window:     No
 5. Can it be rolled back:      Yes
 6. Expenditures:               Opex
 7. Platform Component(s):      [inferred from stories/project — VO or CDK]
 8. Clone/Stage Status:         Part of This Deployment
 9. Config/Settings Changes:    None
10. Code Review Approver:       Heber Iraheta
11. QA Approved By:             Heber Iraheta
12. Date of Code Review:        [today]
13. Date Tested in Clone/Stage: [today]
14. Change Conductor:           Aaron Judd
15. Dev Team:                   BP2
16. Prioritization:             P3
```

### 6. Create the CAB card

Call `createJiraIssue` with summary and all non-ADF fields (option IDs, user IDs, datetime). Project: `CAB`, Issue Type ID: `11101`. Do not include ADF fields yet — those are set in Phase 3 after the PR is known.

Store the returned CAB card key (e.g. `CAB-8994`).

Open the CAB card in the browser:
```bash
powershell -ExecutionPolicy Bypass -File "C:\Users\ajudd\.claude\scripts\Open-EdgeUrl.ps1" -Url "https://younglivingeo.atlassian.net/browse/<CAB-KEY>" -WindowName "Jira"
```

### 7. Link stories to the CAB card

Establish all Jira issue links now — do not wait for Phase 3.

For each BPT2 feature story, call `createIssueLink`:
- Type: `Deploy Location` (outward: CAB card "deploys" the BPT2 story)
- Inward issue: CAB-XXXX, Outward issue: BPT2-XXXX

If a BPT2 CAB key was identified in step 2, call `createIssueLink`:
- Type: `Relates` (CAB card relates to BPT2 CAB)
- Inward issue: CAB-XXXX, Outward issue: BPT2-ZZZZ

### 8. Write session state

Write `~/.claude/memory/sessions/<slug>/CAB-XXXX.md`:

```
---
updated: [today]
---
# Session State — CAB-XXXX

- **Type:** cab
- **Teams chat:** CAB-XXXX — [summary]
- **Branch:** (pending Phase 2)
- **Related BPT2 stories:** BPT2-XXXX, BPT2-YYYY
- **Related BPT2 CAB:** BPT2-ZZZZ (or "none")
- **PR number:** (pending Phase 2)
- **PR URL:** (pending Phase 2)
- **Phase 1 complete:** yes
- **Phase 2 complete:** no
- **Phase 3 complete:** no
- **Phase 4 complete:** no
```

**Back-link story sessions:** for each BPT2 story key (and the BPT2 CAB key if present), if `~/.claude/memory/sessions/<slug>/BPT2-XXXX.md` exists, set its `Related CAB` field to `CAB-XXXX`.

## Output

Report:
- CAB card key and Jira URL
- BPT2 stories collected
- BPT2 CAB back-linked (if present)
- Any story status warnings
- Next: Phase 2 (release branch + PR) — run when feature PRs are merged to develop
