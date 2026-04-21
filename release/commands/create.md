---
name: create
description: Create a CAB card, release branch, and PR for a YL production deployment. Links stories, populates all fields, comments the CAB key back onto each story. Stops before Send For Review.
argument-hint: "[BPT2-XXXX BPT2-YYYY ...]"
---

# CAB: Create Card

Create a fully-populated CAB (Change Advisory Board) card in Jira. Stories feed into the CAB — their summaries become Release Notes, their context seeds the Description. The CAB key is created first so the release branch can be named after it (`release/CAB-XXXX`). The PR comes from that branch. When done, the CAB key and deploy date are commented back onto each story.

## Instructions

### 1. Gather context

Silently collect before prompting:
- Current working directory → project type (VO vs CDK)
- Current git branch → may indicate feature branches already merged
- Memory files → active story keys, branch names
- CLAUDE.md → field IDs, defaults, team info

### 2. Fetch linked stories

For each story key (from arguments, memory, or prompt), call `getJiraIssue`.

Extract:
- **Summary** → will become a bullet in Release Notes
- **Description / acceptance criteria** → seeds CAB Description
- **Status** → warn if any story is not in a deployable state (e.g. not Done / Ready for Deploy). Ask the user to confirm before continuing.
- **Component / label** → helps confirm Platform Component (VO vs CDK)

If no story keys are available from context or arguments, prompt:
```
Which stories are in this release? (e.g. BPT2-6189 BPT2-6207)
```

### 3. Prompt required inputs

Present with pre-seeded defaults from story data. User presses Enter to accept or types a replacement.

```
=== CAB Card Creation ===

Summary:           [inferred — e.g. "BP2 - Virtual Office - TH Direct Deposit"]
Deploy date/time:  [none — user must provide, e.g. "Friday 1pm MDT"]
What's deploying:  [seeded from story summaries — confirm or refine]
```

### 4. Prompt configurable defaults

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

### 5. Create the Jira issue (minimal — to get the CAB key)

Call `createJiraIssue` with summary and all non-ADF fields (option IDs, user IDs, datetime). Do not include ADF fields yet — they are set in step 8 after the PR is known.

Project: `CAB`, Issue Type ID: `11101`.

Store the returned CAB key (e.g. `CAB-8994`). It is used in every subsequent step.

### 6. Create the release branch

Branch name: `release/CAB-XXXX` (using the key from step 5).

**Virtual Office:**
```bash
git checkout -b release/CAB-XXXX
```
Guide the user to merge each story's feature branch into the release branch:
```bash
git merge feature/BPT2-XXXX
git merge feature/BPT2-YYYY
```
Resolve any merge conflicts before continuing.

Confirm: "Has this release branch been deployed to env6 and tested? [Y/N]"
- If No: stop. "Deploy `release/CAB-XXXX` to env6, complete QA testing, then return to continue."

**CDK:**
```bash
git checkout -b release/CAB-XXXX develop
```
Confirm: "Are all feature PRs merged into `develop` and tests passing? [Y/N]"
- If No: stop. "Merge outstanding feature PRs into `develop` first."

Push the release branch:
```bash
git push -u origin release/CAB-XXXX
```

### 7. Create the PR

```bash
gh pr create --base master --head release/CAB-XXXX
```

- **Title:** descriptive deploy title matching the CAB summary
- **Body:** include the CAB key (`CAB-XXXX`) so GitHub for Jira auto-links, list the linked story keys, brief description of what's deploying

**CDK first deploy** (master does not exist — check with `git ls-remote --exit-code origin master`):
- Skip PR creation. Note in the card: "First deploy — direct push to master (no PR)".
- `Component Version(s)`: repository + branch only, no PR column.

Store the PR number and URL for step 8.

### 8. Populate all remaining CAB fields

Call `editJiraIssue` to set all ADF fields now that the PR is known:

- **Description** (ADF): What is being deployed, why, any phased approach — seeded from story descriptions
- **Release Notes** (`customfield_10512`, ADF): Bullet list of story summaries, one per story
- **Deployment Plan** (`customfield_13142`, ADF): Project-specific template from `release` skill
- **Deployment Playbook** (`customfield_13143`, ADF): Same as Deployment Plan
- **Rollback Plan** (`customfield_13101`, ADF): Project-specific template from `release` skill
- **Pre-Deployment Tests** (`customfield_13099`, ADF): VO: "Tested in env6" / CDK: "Tested in dev/stage"
- **Post-Deployment Tests** (`customfield_13100`, ADF): "Tested in Prod"
- **Config/Settings Changes** (`customfield_13176`, ADF): As specified or "None"
- **Component Version(s)** (`customfield_13141`, ADF): Table — Repository / `release/CAB-XXXX` / PR link
- **PRs Deploying** (`customfield_14670`, ADF): `"<PR title> - Pull Request #<N> - <org>/<repo>"` with link

### 9. Link related stories

For each story key, call `createIssueLink` with `type="Deploy Location"` (outward: CAB "deploys" the story).

### 10. Comment back on each story

For each linked story, call `addCommentToJiraIssue`:

```
Deploying in CAB-XXXX — [CAB summary]
Scheduled: [deploy date/time in local time]
Release branch: release/CAB-XXXX
PR: [PR title] — Pull Request #N ([link])
```

This makes the deployment visible to anyone looking at the story in Jira — QA, PM, app support.

### 11. Register links

Read `~/.claude/browser-links.json`.

**Always add to `links` section (if not already present):**
- `cab:CAB-XXX` → `https://younglivingeo.atlassian.net/browse/CAB-XXX`, description: CAB summary
- `pr:repo-name#NNN` → PR URL, description: PR title *(skip on first-deploy where no PR was created)*

**Create `CAB-XXX` workspace** (type: `cab`) with all relevant keys:
```json
"CAB-XXX": {
  "description": "<CAB summary>",
  "type": "cab",
  "links": ["cab:CAB-XXX", "pr:repo-name#NNN", "story:BPT2-XXXX", ...]
}
```
- Include `story:BPT2-XXXX` for each linked story that exists in the `links` section
- Include `git:repo-name` if it exists in the `links` section
- Omit `pr:` entry on first-deploy

**Append to each linked story workspace** (if the workspace exists in `browser-links.json`):
- `cab:CAB-XXX`
- `pr:repo-name#NNN` *(skip on first-deploy)*
- `git:repo-name` if it exists in the `links` section

Write back `~/.claude/browser-links.json`. Do not prompt the user during this step.

### 12. Stop — user handles submission

Do NOT call `transitionJiraIssue` for Send For Review or update the assignee. The user reviews the card in Jira and submits manually.

### 13. Write session cross-references

Run `pwd` and extract the repo slug (last path component).

**Write/update the CAB session file** at `~/.claude/memory/sessions/<slug>/CAB-XXXX.md`:
- Type: cab
- Branch: `release/CAB-XXXX`
- Related stories: comma-separated story keys

**Back-link each story session file**: if `~/.claude/memory/sessions/<slug>/BPT2-XXXX.md` exists, set its `Related CAB` field to `CAB-XXXX`.

## Output

Report:
- CAB card URL and key
- Release branch created and pushed
- PR created (or first-deploy note)
- Stories linked and commented
- Any story status warnings from step 2
- Next step: user reviews card in Jira and submits for review
