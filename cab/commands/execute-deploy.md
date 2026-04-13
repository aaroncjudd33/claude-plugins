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
- Skip to step 4a — direct push is required

If `master` already exists and `develop` has new commits:
- Use `gh pr create --base master --head develop` with:
  - Title: descriptive deploy title
  - Body: include the CAB card key (e.g. `CAB-8994`) so GitHub for Jira auto-links the PR to the CAB card's "PRs Deploying" field
  - Reference the linked Jira story

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

### 4b. Merge to master (confirm with user first)

**Always confirm with the user before this step — it triggers the live prod deploy.**

```bash
gh pr merge --merge
```

### 5b. Monitor the build/deploy

Use `gh run list` and `gh run watch` to monitor progress.

### 5c. Clone deploy (VO-specific)

After the main prod deploy succeeds, trigger a deploy to the clone workspace:

```bash
gh workflow run build-deploy-dev.yml --ref <release-branch> --field deploy_workspace=clone
```

Use `gh run list` and `gh run watch` to monitor. This must complete before closing the CAB card.

### 6b. Post-deploy cache busting (VO-specific)

After successful deploy, bust caches:
1. **Front End Cache:** `https://www.youngliving.com/vo/cache/invalidate`
2. **NHibernate Cache:** `https://www.youngliving.com/api/shopping/dev/cache/clear`

### 7b. Post-deploy verification (VO)

- QA testing in prod
- App support validation

---

## Common Final Steps

### Close the CAB card

Transition the CAB card to **Success** status using `transitionJiraIssue`.

Look up the available transitions with `getTransitionsForJiraIssue` to get the correct transition ID for Success.

### Update memory

Update the project's memory to mark the deploy complete.

## Output

Final report:
- Deploy status (success/failure)
- For CDK: CloudFormation stack names/statuses, Lambda function names, API Gateway URL
- For VO: Cache bust confirmation
- CAB card status
- Any follow-up actions needed
