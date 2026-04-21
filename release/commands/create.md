---
name: create
description: Create a CAB card (IT Software Change in the CAB Jira project), release branch, and PR for a YL production deployment. Links BPT2 stories, populates all fields, comments the CAB card key back onto each story. Stops before Send For Review.
argument-hint: "[BPT2-XXXX BPT2-YYYY ...]"
---

# Release: Create CAB Card

Creates a **CAB card** — an IT Software Change ticket in the CAB Jira project — to authorize a production deployment.

**Terminology used in this skill:**
- **BPT2 CAB** — the BPT2 story (on the team board, prefixed `CAB -`) that tracks the deployment work and bundles the feature stories. Created via `/story:create` *before* this command.
- **BPT2 stories** — the feature/bug-fix stories being deployed (e.g. BPT2-6258, BPT2-6333).
- **CAB card** — the IT Software Change ticket in the CAB Jira project. *This is what this command creates.*

## Instructions

### 1. Gather context

Silently collect before prompting:
- Current working directory → project type (VO vs CDK)
- Current git branch → may indicate feature branches already merged
- Memory files → active story keys, branch names
- CLAUDE.md → field IDs, defaults, team info

### 2. Check for BPT2 CAB

Look in memory and conversation context for a BPT2 CAB story (a BPT2 story prefixed `CAB -` that bundles the feature stories for this release).

If not found, prompt:
```
Do you have a BPT2 CAB story for this release? (e.g. BPT2-6334)
If not, create one first with /story:create before continuing.
```

Store the BPT2 CAB key — it will be back-linked in step 10.

### 3. Fetch BPT2 stories being deployed

For each BPT2 story key (from arguments, memory, or prompt), call `getJiraIssue`.

Extract:
- **Summary** → will become a bullet in Release Notes
- **Description / acceptance criteria** → seeds CAB card Description
- **Status** → warn if any story is not in a deployable state (e.g. not Done / Ready for Deploy). Ask the user to confirm before continuing.
- **Component / label** → helps confirm Platform Component (VO vs CDK)

If no story keys are available from context or arguments, prompt:
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

### 6. Create the CAB card (minimal — to get the CAB key)

Call `createJiraIssue` with summary and all non-ADF fields (option IDs, user IDs, datetime). Do not include ADF fields yet — they are set in step 9 after the PR is known.

Project: `CAB`, Issue Type ID: `11101`.

Store the returned CAB card key (e.g. `CAB-8994`). It is used in every subsequent step.

### 7. Create the release branch

Branch name: `release/CAB-XXXX` (using the key from step 6).

**Virtual Office:**
```bash
git checkout -b release/CAB-XXXX
```
Guide the user to merge each BPT2 story's feature branch into the release branch:
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

### 8. Create the PR

```bash
gh pr create --base master --head release/CAB-XXXX
```

- **Title:** descriptive deploy title matching the CAB card summary
- **Body:** include the CAB card key (`CAB-XXXX`) so GitHub for Jira auto-links, list the BPT2 story keys, brief description of what's deploying

**CDK first deploy** (master does not exist — check with `git ls-remote --exit-code origin master`):
- Skip PR creation. Note in the card: "First deploy — direct push to master (no PR)".
- `Component Version(s)`: repository + branch only, no PR column.

Store the PR number and URL for step 9.

### 9. Populate all remaining CAB card fields

Call `editJiraIssue` to set all ADF fields now that the PR is known:

- **Description** (ADF): What is being deployed, why, any phased approach — seeded from BPT2 story descriptions
- **Release Notes** (`customfield_10512`, ADF): Bullet list of BPT2 story summaries, one per story
- **Deployment Plan** (`customfield_13142`, ADF): Project-specific template from `release` skill
- **Deployment Playbook** (`customfield_13143`, ADF): Same as Deployment Plan
- **Rollback Plan** (`customfield_13101`, ADF): Project-specific template from `release` skill
- **Pre-Deployment Tests** (`customfield_13099`, ADF): VO: "Tested in env6" / CDK: "Tested in dev/stage"
- **Post-Deployment Tests** (`customfield_13100`, ADF): "Tested in Prod"
- **Config/Settings Changes** (`customfield_13176`, ADF): As specified or "None"
- **Component Version(s)** (`customfield_13141`, ADF): Table — Repository / `release/CAB-XXXX` / PR link
- **PRs Deploying** (`customfield_14670`, ADF): `"<PR title> - Pull Request #<N> - <org>/<repo>"` with link

### 10. Link related issues

For each BPT2 story key, call `createIssueLink` with `type="Deploy Location"` (outward: CAB card "deploys" the BPT2 story).

If a BPT2 CAB key was identified in step 2, also link it with `type="Relates"`.

### 11. Comment back on BPT2 stories and BPT2 CAB

For each BPT2 story (and the BPT2 CAB if present), call `addCommentToJiraIssue`:

```
Deploying in CAB-XXXX — [CAB card summary]
Scheduled: [deploy date/time in local time]
Release branch: release/CAB-XXXX
PR: [PR title] — Pull Request #N ([link])
```

This makes the deployment visible to anyone looking at the story in Jira — QA, PM, app support.

### 12. Register links

Read `~/.claude/browser-links.json`.

**Always add to `links` section (if not already present):**
- `cab:CAB-XXX` → `https://younglivingeo.atlassian.net/browse/CAB-XXX`, description: CAB card summary
- `pr:repo-name#NNN` → PR URL, description: PR title *(skip on first-deploy where no PR was created)*

**Create `CAB-XXX` workspace** (type: `cab`) with all relevant keys:
```json
"CAB-XXX": {
  "description": "<CAB card summary>",
  "type": "cab",
  "links": ["cab:CAB-XXX", "pr:repo-name#NNN", "story:BPT2-XXXX", ...]
}
```
- Include `story:BPT2-XXXX` for each BPT2 story and the BPT2 CAB that exist in the `links` section
- Include `git:repo-name` if it exists in the `links` section
- Omit `pr:` entry on first-deploy

**Append to each BPT2 story workspace and the BPT2 CAB workspace** (if the workspace exists in `browser-links.json`):
- `cab:CAB-XXX`
- `pr:repo-name#NNN` *(skip on first-deploy)*
- `git:repo-name` if it exists in the `links` section

Write back `~/.claude/browser-links.json`. Do not prompt the user during this step.

### 13. Stop — user handles submission

Do NOT call `transitionJiraIssue` for Send For Review or update the assignee. The user reviews the CAB card in Jira and submits manually.

### 14. Write session cross-references

Run `pwd` and extract the repo slug (last path component).

**Write/update the CAB card session file** at `~/.claude/memory/sessions/<slug>/CAB-XXXX.md`:
- Type: cab
- Branch: `release/CAB-XXXX`
- Related BPT2 stories: comma-separated story keys
- Related BPT2 CAB: the BPT2 CAB key (if present)

**Back-link each BPT2 story session file and the BPT2 CAB session file**: if `~/.claude/memory/sessions/<slug>/BPT2-XXXX.md` exists, set its `Related CAB` field to `CAB-XXXX`.

## Output

Report:
- CAB card URL and key
- Release branch created and pushed
- PR created (or first-deploy note)
- BPT2 stories linked and commented
- BPT2 CAB linked and commented (if present)
- Any story status warnings from step 3
- Next step: user reviews CAB card in Jira and submits for review
