---
name: create-cab
description: Create a complete CAB card in Jira for a Young Living production deployment, resolve or create the deployment PR, and populate all required fields. Stops before submission — user handles Send For Review and assignee update manually.
argument-hint: "[summary] [deploy-date] [linked-story]"
---

# CAB: Create Card

Create a fully-populated CAB (Change Advisory Board) card in Jira. Uses all known field IDs and workflows from the `cab` skill so the card is complete from the start — including the deployment PR, which must exist before the card can be approved.

## Instructions

When this command is invoked:

### 1. Gather context first

Before prompting the user, silently gather as much as possible from:
- Current working directory (project type: VO vs CDK)
- Current git branch name (for Component Version(s) and linked stories)
- Memory files (active stories, branch names, linked Jira keys)
- CLAUDE.md (field IDs, defaults, team info)
- Existing PRs on the current branch (`gh pr list --state open`)

Use this context to pre-fill defaults for as many fields as possible.

### 2. Prompt with defaults — required inputs

Present these fields that need user input. If context provides a reasonable value, show it as the default. The user presses Enter to accept or types a replacement.

```
=== CAB Card Creation ===

Summary:           [inferred from branch/story, e.g. "BP2 - Virtual Office - TH Direct Deposit"]
Deploy date/time:  [none — user must provide, e.g. "tomorrow 1pm MDT"]
Linked stories:    [inferred from branch, e.g. "BPT2-6189, BPT2-6207"]
What's deploying:  [inferred from memory/story context if available]
```

Only ask for fields where no reasonable default can be inferred. If all required inputs are provided as arguments or inferable from context, skip straight to the confirmation step.

### 3. Prompt with defaults — configurable fields

Present ALL configurable fields with their defaults. The user can press Enter to accept all defaults, or type a number to override specific ones.

```
=== Defaults (Enter to accept all, or type numbers to change) ===

 1. CAB Impact:              Low
 2. CAB Risk:                Low
 3. CAB Request Type:        Standard
 4. Requires Outage Window:  No
 5. Can it be rolled back:   Yes
 6. Expenditures:            Opex
 7. Platform Component(s):   [inferred — e.g. "Virtual Office" for VO, "AWS" for CDK]
 8. Clone/Stage Status:      Part of This Deployment
 9. Config/Settings Changes:  None
10. Code Review Approver:    Heber Iraheta
11. QA Approved By:          Heber Iraheta
12. Date of Code Review:     [today's date]
13. Date Tested in Clone/Stage: [today's date]
14. Change Conductor:        Aaron Judd
15. Dev Team:                BP2
```

If the user types nothing (Enter), accept all defaults. If they type e.g. "1, 2" then prompt for just those fields with the available options.

### 4. Resolve the deployment PR

The CAB card cannot be submitted for review or approved without a PR. Resolve it now before creating the card.

Run `gh pr list --state open` to check for an existing PR on the current branch.

**If a PR is found:** display it and confirm it is the correct one for this deployment. Use it for `Component Version(s)` and `PRs Deploying`.

**If no PR exists:**

- **CDK first deploy** (master branch does not exist on remote — check with `git ls-remote --exit-code origin master`): The first deploy uses a direct push to master. No PR can be created yet. Populate `Component Version(s)` with the repository and branch. Set `PRs Deploying` to a note: "First deploy — direct push to master (no PR)". Continue.

- **All other cases:** Offer to create the PR now:

  ```
  No open PR found. Create it now? (recommended — CAB cannot be approved without a PR)
  [Y] Yes — create PR   [S] Skip — I'll add it later via /cab:update-cab
  ```

  - **Yes:** Create the PR using `gh pr create`:
    - Base: `master`
    - Head: current branch
    - Title: descriptive deploy title matching the CAB summary
    - Body: include the CAB summary, linked story keys, and a note that this PR corresponds to the CAB card being created
    - Use the returned PR number and URL for `Component Version(s)` and `PRs Deploying`

  - **Skip:** Warn the user: "The CAB card will be created, but it cannot be submitted for review without a PR. Add it via `/cab:update-cab` → Update PR / branch info before submitting." Continue with `Component Version(s)` showing repo and branch only, `PRs Deploying` left blank.

### 5. Build all field content

Using the `cab` skill field reference, construct all fields:

- **Summary**: `<TEAM> - <Project> - <Change Description>`
- **Description** (ADF): Full deployment description — what, why, phased approach if any
- **Release Notes** (`customfield_10512`, ADF): What changed from a user/business perspective
- **Deployment Plan** (`customfield_13142`, ADF): Project-specific template from `cab` skill (VO or CDK)
- **Deployment Playbook** (`customfield_13143`, ADF): Same content as Deployment Plan
- **Rollback Plan** (`customfield_13101`, ADF): Project-specific template from `cab` skill (VO or CDK)
- **Pre-Deployment Tests** (`customfield_13099`, ADF): Project-specific (VO: "Tested in env6", CDK: "Tested in dev/stage")
- **Post-Deployment Tests** (`customfield_13100`, ADF): Project-specific (VO: "Tested in Prod", CDK: "Tested in Prod")
- **Config/Settings Changes** (`customfield_13176`, ADF): As specified or "None"
- **Component Version(s)** (`customfield_13141`, ADF): Table with Repository / Branch / PR columns — use PR info from step 4
- **PRs Deploying** (`customfield_14670`, ADF): PR title + link from step 4, formatted per skill reference
- All option/user fields from the confirmed defaults above
- **Requested Deployment Date/Time** (`customfield_13137`): Convert user's local time to UTC ISO 8601

### 6. Create the issue

Call `createJiraIssue` with all fields in a single call. Project: `CAB`, Issue Type ID: `11101`.

Then immediately call `editJiraIssue` to set the description with proper markdown formatting (createJiraIssue treats description as literal text).

### 7. Link related stories

For each linked Jira story, call `createIssueLink` with `type="Deploy Location"` (outward direction: CAB "deploys" the story).

### 8. Stop — user handles submission

Do NOT call `transitionJiraIssue` for Send For Review or change the assignee. The user handles these steps manually after reviewing the card in the Jira UI.

### 9. Write session cross-references

Run `pwd` and extract the repo slug (last path component).

**Write/update the CAB session file** at `~/.claude/memory/sessions/<slug>/CAB-XXX.md`:
- Set `Related stories` to the comma-separated list of linked story keys (e.g. `BPT2-1234, BPT2-1235`)
- If the file does not exist yet, create it with the full session template (Type: cab, Branch: n/a, etc.)

**Back-link each story session file**: for each linked story key, check if `~/.claude/memory/sessions/<slug>/BPT2-XXXX.md` exists. If it does, update its `Related CAB` field to `CAB-XXX`.

Save the CAB card URL and key to the project's memory.

## Output

Report:
- CAB card URL and key
- Current status (should be Open/New)
- PR status (existing / newly created / skipped — with reminder if skipped)
- Any fields that could not be populated and why
- Next step: user submits for review once satisfied with the card
