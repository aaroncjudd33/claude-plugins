---
name: execute-deploy
description: Execute a production deployment — create the PR, push to master, monitor the GitHub Actions workflow, notify when reviewer approval is needed, verify post-deploy, and close the CAB card.
argument-hint: "[cab-card-key]"
---

# CAB: Execute Deploy

Run the full production deployment sequence. This command handles everything from creating the PR to closing the CAB card. Supports both CDK services and Virtual Office deployments.

## Prerequisites

Before invoking this command, confirm:
- CAB card is in **Implementation** status (approved by Sudhakar)
- For CDK: All SSM parameters exist in the prod AWS account
- For CDK: `develop` branch is up to date and tests are passing
- For VO: Integration branch is deployed and tested in env6

## Instructions

### 0. Identify the CAB card

Run `pwd` and extract the repo slug (last path component).

If a CAB key is provided as an argument, use it. Otherwise read `~/.claude/memory/sessions/<slug>/_active` to get the active session name, then read that session file for the CAB key.

If neither is available, prompt: "Which CAB card? (e.g. CAB-456)"

Store the CAB key — it is used throughout all steps below.

### 1. Detect project type

Determine whether this is a **CDK service** or **Virtual Office** deploy based on the current working directory and project context. This determines which flow to follow below.

### 2. Confirm readiness

Check the CAB card status using `getJiraIssue`. If not in Implementation, stop and report the current status.

Confirm with the user before proceeding past this point.

---

## CDK Service Flow

### 3a. Create the develop → master PR

If `master` branch does not yet exist on the remote:
- A PR cannot be created (branches are identical)
- Skip steps 3a-1 and go directly to step 4a — direct push is required, no PR link to write back

If `master` already exists and `develop` has new commits:
- Use `gh pr create --base master --head develop` with:
  - Title: descriptive deploy title
  - Body: include the CAB card key (e.g. `CAB-8994`) so GitHub for Jira auto-links the PR to the CAB card's "PRs Deploying" field
  - Reference the linked Jira story

### 3a-1. Update CAB card with PR link

After the PR is created, call `editJiraIssue` to write the PR back into the CAB card:
- `customfield_14670` (PRs Deploying): PR title + link, formatted as `"<title> - Pull Request #<N> - <org>/<repo>"`
- `customfield_13141` (Component Version(s)): ADF table with Repository / Branch / Pull Request columns

### 4a. Push to master (confirm with user first)

**Always confirm with the user before this step — it triggers the live prod deploy.**

For first deploy (master does not exist):
```bash
git push origin develop:master
```

For subsequent deploys (PR exists):
```bash
gh pr merge --merge
```

### 5a. Monitor build/test job

Use `gh run list` and `gh run watch` to monitor progress. Report status updates.

Expected duration: 8–12 minutes (longer if Oracle Docker container startup is needed).

If tests fail, report the failure details and stop. Do not proceed to deploy.

### 6a. Notify when prod gate is waiting

When the build/test job passes, the prod environment gate activates. At this point:
- Notify the user that a reviewer needs to approve in GitHub
- The required reviewers are set on the `prod` environment in GitHub repo settings
- The user needs to ping a team member (Maikol, Fernando, or Angela) to approve

Wait for approval before continuing.

### 7a. Monitor the CDK deploy job

Once approved, watch the deploy job. Report completion or failure.

### 8a. Post-deploy verification (CDK)

Check that the deployment succeeded:
- CloudFormation stacks show `CREATE_COMPLETE` (or `UPDATE_COMPLETE`)
- Lambda functions exist and are active
- DynamoDB table exists (if applicable)
- API Gateway endpoint is reachable (HTTP 200 or 403, not 5xx)

Use AWS CLI via `aws cloudformation describe-stacks` and `aws lambda list-functions` with the prod profile.

---

## Virtual Office Flow

### 3b. Create the integration → master PR

- Use `gh pr create --base master --head <integration-branch>` with:
  - Title: descriptive deploy title
  - Body: include the CAB card key so GitHub for Jira auto-links
  - Reference the linked Jira stories

### 3b-1. Update CAB card with PR link

After the PR is created, call `editJiraIssue` to write the PR back into the CAB card:
- `customfield_14670` (PRs Deploying): PR title + link, formatted as `"<title> - Pull Request #<N> - <org>/<repo>"`
- `customfield_13141` (Component Version(s)): ADF table with Repository / Branch / Pull Request columns

### 4b. Merge to master (confirm with user first)

**Always confirm with the user before this step — it triggers the live prod deploy.**

```bash
gh pr merge --merge
```

### 5b. Monitor the build/deploy

Use `gh run list` and `gh run watch` to monitor progress.

### 6b. Post-deploy cache busting (VO-specific)

Immediately after the prod deploy succeeds, bust caches so QA is testing with fresh content:
1. **Front End Cache:** `https://www.youngliving.com/vo/cache/invalidate`
2. **NHibernate Cache:** `https://www.youngliving.com/api/shopping/dev/cache/clear`

### 7b. Clone deploy (VO-specific)

After cache busting, prompt the user to trigger the clone workspace deploy:

```bash
gh workflow run build-deploy-dev.yml --ref <release-branch> --field deploy_workspace=clone
```

Use `gh run list` and `gh run watch` to monitor.

**Important:** The user may defer this step if there are concerns during QA testing. If deferred, note that **the CAB card cannot be closed until the clone deploy has been completed**. Remind the user before attempting to close the CAB.

### 8b. Post-deploy verification (VO)

- QA testing in prod
- App support validation

---

## Common Final Steps

### Close the CAB card

Before closing, verify the clone deploy (step 7b) has been completed. If it was deferred, do not close the CAB — remind the user it must be done first.

Transition the CAB card to **Success** status using `transitionJiraIssue`.

Look up the available transitions with `getTransitionsForJiraIssue` to get the correct transition ID for Success.

### Transition related stories

Run `pwd` and extract the repo slug (last path component).

Read `~/.claude/memory/sessions/<slug>/CAB-XXX.md` and check `Related stories`.

For each story key listed, prompt: "Transition BPT2-XXXX to Done?"
- If yes: call `getTransitionsForJiraIssue` to find the Done transition ID, then `transitionJiraIssue`
- After transitioning, update that story's session file (`BPT2-XXXX.md`) to set `Related CAB` to `none`

### Update memory

Update the CAB session file to mark the deploy complete. Clear `Related stories` only after all story transitions are resolved (or explicitly skipped).

## Output

Final report:
- Deploy status (success/failure)
- For CDK: CloudFormation stack names/statuses, Lambda function names, API Gateway URL
- For VO: Cache bust confirmation
- CAB card status
- Any follow-up actions needed
