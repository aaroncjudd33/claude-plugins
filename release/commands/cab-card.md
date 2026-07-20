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

**Print progress as you go — one line per major step (acp-ajudd#146).** Before Step 1 does anything else, print `Got it — starting CAB Card (Phase 1). I'll post a ✨ line after each step.` as a plain one-line statement (no reply needed). This phase then chains several slow Jira/Teams calls in sequence; print one line immediately after each completes, before starting the next — do not batch silently until the final summary:
```
✨ Context loaded (story keys, team roster, known chats)
✨ BPT2 CAB confirmed: <key>
✨ BPT2 stories fetched: N
✨ CAB card created: <CAB-XXX>
✨ BPT2 CAB story assigned + transitioned
✨ Stories linked to CAB card
✨ CAB Teams chat resolved: <name>  ← or "skipped"
✨ Session state written
```
**This overrides the general "batch independent tool calls in parallel" habit (acp-ajudd#146 follow-up).** Each line above is a hard turn boundary — after the tool call(s) for that step resolve, your entire response for that turn is the ✨ line, then stop. Do not fold the next step's tool call into the same response just because it would be faster. An extra turn is cheaper than a silent multi-minute gap.

## Instructions

### 1. Load context

Run `pwd` and extract the repo slug (last path component).

Issue all of the following **in one parallel batch** — they have no dependencies on each other:
- Story keys from command arguments (if any)
- Memory files → active session, known story keys, BPT2 CAB key
- Current git branch (`git branch --show-current`)
- `~/.claude/plugins/team.json`
- `~/.claude/plugins/user-config.json`
- `~/.claude/browser-links.json`
- `~/.claude/plugins/known-chats.md`

Cache all results in context — later steps reference these without re-reading.

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

Call `getJiraIssue` for all BPT2 story keys (from arguments, memory, cab-prep context, or prompt) **in parallel**.

Extract: **Summary**, **Description/acceptance criteria**, **Status**, **Component/label**.

Warn if any story is not in a deployable state (Done / Ready for Deploy). Ask the user to confirm before continuing.

If no story keys are available (and none were pre-populated from a cab-prep item), prompt:
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

Use the already-loaded `team.json` to populate items 10 and 11:
- Item 10: first member with role `code-review-approver` → use `name` field
- Item 11: first member with role `qa-approver` → use `name` field

```
=== Defaults (Enter to accept all, or type numbers to change) ===

 1. CAB Impact:                 Low
 2. CAB Risk:                   Low              ← if cab-prep context available, pre-seed from cab-prep risk (low/medium/high)
 3. CAB Request Type:           Standard         ← if cab-prep context available, pre-seed from cab-prep urgency (standard → Standard, emergency → Emergency)
 4. Requires Outage Window:     No
 5. Can it be rolled back:      Yes
 6. Expenditures:               Opex
 7. Platform Component(s):      [inferred from stories/project — VO or CDK]
 8. Clone/Stage Status:         Part of This Deployment
 9. Config/Settings Changes:    None
10. Code Review Approver:       [from team.json → code-review-approver]
11. QA Approved By:             [from team.json → qa-approver]
12. Date of Code Review:        [today]
13. Date Tested in Clone/Stage: [today]
14. Change Conductor:           {USER_NAME} (from already-loaded user-config.json)
15. Dev Team:                   BP2
16. Prioritization:             P3
```

When building the `createJiraIssue` call, use the `jiraAccountId` from team.json for
items 10 and 11 — not the display name. If team.json is missing or the role has no
member, prompt the user to enter the account ID manually.

### 6. Create the CAB card

Call `createJiraIssue` with summary and all non-ADF fields (option IDs, user IDs, datetime). Project: `CAB`, Issue Type ID: `11101`. Do not include ADF fields yet — those are set in Phase 3 after the PR is known.

Store the returned CAB card key (e.g. `CAB-8994`).

Open the CAB card in the browser. Look up `prefixDefaults["cab"]` in the already-loaded `browser-links.json` to resolve the window name (default: `"Cab"` if not found):
```bash
powershell -ExecutionPolicy Bypass -File "~\.claude\scripts\Open-EdgeUrl.ps1" -Url "https://younglivingeo.atlassian.net/browse/<CAB-KEY>" -WindowName "<resolved-window-name>"
```

### 7. Assign and transition the BPT2 CAB story

If a BPT2 CAB key was identified in step 2, ensure it is properly set up as the tracking story:

1. Call `editJiraIssue` to assign it to the current user (`user.jiraAccountId` from already-loaded `user-config.json`)
2. Call `transitionJiraIssue` with transition ID `181` to move it to **Ready For Work**

Always use Ready For Work here — whether the story was just created or already existed. Do NOT move to In Progress unless the user explicitly asks.

### 8. Link stories to the CAB card

Establish all Jira issue links now — do not wait for Phase 3.

Call `createIssueLink` for all BPT2 feature stories **in parallel**:
- Type: `Deploy Location` (outward: CAB card "deploys" the BPT2 story)
- Inward issue: CAB-XXXX, Outward issue: BPT2-XXXX

If a BPT2 CAB key was identified in step 2, call `createIssueLink`:
- Type: `Relates` (CAB card relates to BPT2 CAB)
- Inward issue: CAB-XXXX, Outward issue: BPT2-ZZZZ

### 9. Create the CAB Teams chat

Using the already-loaded `team.json`, filter members with the `story-chat` role and collect their `teamsUserId` fields. Do **not** include `ajudd@youngliving.com` — the authenticated user is added automatically.

Create the chat via yl-msoffice with:
- **Topic:** `CAB-XXXX — [CAB card summary]`
- **Members:** `story-chat` role user IDs from team.json

If creation fails, stop: "CAB Teams chat could not be created. Resolve this before continuing — the chat is required for release communications."

Add the new chat to `~/.claude/plugins/known-chats.md` (Name, Chat ID, Active=yes, Members list, Topic) — file was pre-loaded in Step 1.

### 10. Write session state

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
- Teams chat created and registered
- Next: Phase 2 (release branch + PR) — run when feature PRs are merged to develop
