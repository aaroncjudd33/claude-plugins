---
name: create-cab
description: Create a complete CAB card in Jira for a Young Living production deployment, populate all required fields, submit for review, and assign to Sudhakar.
argument-hint: "[summary] [deploy-date] [linked-story]"
---

# CAB: Create Card

Create a fully-populated CAB (Change Advisory Board) card in Jira, submit it for review, and update the assignee. Uses all known field IDs and workflows from the `cab` skill so the card is complete and ready to go from the start.

## Instructions

When this command is invoked:

### 1. Collect inputs

If not provided as arguments, ask the user for:
- **Summary** — short title (will be formatted as `<TEAM> - <Project> - <Change Description>`)
- **Deploy date and time** — local time + timezone (will be converted to UTC)
- **Linked Jira story/stories** — one or more BPT2-XXXX keys
- **What is being deployed** — brief description (used for Description + Release Notes)
- **Platform Component(s)** — which AWS/platform components (default: AWS)
- **Is there a rollback plan?** — yes/no and brief description

Infer anything reasonable from project context (CLAUDE.md, memory files) without asking. Minimize questions.

### 2. Build all field content

Using the `cab` skill field reference, construct:

- **Summary**: `<TEAM> - <Project> - <Change Description>`
- **Description** (ADF): Full deployment description — what is being deployed, why, any phased approach
- **Release Notes** (`customfield_10512`, ADF): What changed from a user/business perspective
- **Deployment Plan** (`customfield_13142`, ADF): Step-by-step deploy instructions based on the project's CI/CD setup
- **Rollback Plan** (`customfield_13101`, ADF): Step-by-step rollback based on the stack type (CDK destroy, git revert, etc.)
- **Pre-Deployment Tests** (`customfield_13099`, ADF): What to verify before deploying
- **Post-Deployment Tests** (`customfield_13100`, ADF): What to verify after deploying
- **Config/Settings Changes** (`customfield_13176`, ADF): SSM params, env vars, feature flags — or "None"
- **Component Version(s)** (`customfield_13141`, ADF): Table with Repository / Branch / PR columns
- All option fields: CAB Impact (default Low), CAB Risk (default Low), CAB Request Type (default Standard), Dev Team (BP2), Requires Outage Window (default No), Can it be rolled back (default Yes)
- **Change Conductor** (`customfield_13109`): Aaron Judd — `620147d91fec260068c1097d`
- **Platform Component(s)** (`customfield_13076`): Array of option IDs per skill reference
- **Requested Deployment Date/Time** (`customfield_13137`): Convert to UTC ISO 8601

### 3. Create the issue

Call `createJiraIssue` with all fields in a single call. Project: `CAB`, Issue Type ID: `11101`.

### 4. Link related stories

For each linked Jira story, call `jiraWrite` with `action=createIssueLink`, `type="Relates"`.

### 5. Submit for review — immediately update assignee

In the same turn, back-to-back:
1. Call `transitionJiraIssue` (transition ID `201`) with `customfield_13174` set to Heber Iraheta (`557058:055d4592-8fbf-4b3c-8115-0dc48da8a1b4`)
2. Immediately call `editJiraIssue` to set assignee to Sudhakar Seerapu (`60aeba90f3fab100683274d9`)

Do both in the same message before the issue can lock.

### 6. Handle PRs Deploying

If the deployment PR does not exist yet (master branch not created, PR not opened):
- Do NOT try to set `customfield_13156` — it is not the PRs Deploying field
- Add a comment to the issue explaining the PR will be created immediately before deployment and will auto-link via GitHub for Jira once the PR references the CAB issue key

### 7. Save to memory

Save the CAB card URL and key to the project's `prod-deploy-checklist.md` or `MEMORY.md`.

## Output

Report:
- CAB card URL and key
- Status (should be "Change Review" after submission)
- Assignee (should be Sudhakar Seerapu)
- Any fields that could not be populated and why
- Next step: wait for Sudhakar to approve, then proceed with deploy
