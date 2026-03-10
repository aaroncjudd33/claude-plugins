---
name: execute-deploy
description: Execute a production deployment — create the PR, push to master, monitor the GitHub Actions workflow, notify when reviewer approval is needed, verify post-deploy, and close the CAB card.
argument-hint: "[cab-card-key]"
---

# CAB: Execute Deploy

Run the full production deployment sequence for a YL CDK service. This command handles everything from creating the PR to closing the CAB card.

## Prerequisites

Before invoking this command, confirm:
- All SSM parameters exist in the prod AWS account
- CAB card is in **Implementation** status (approved by Sudhakar)
- `develop` branch is up to date and tests are passing

## Instructions

### 1. Confirm readiness

Check the CAB card status using `getJiraIssue`. If not in Implementation, stop and report the current status.

Confirm with the user before proceeding past this point.

### 2. Create the develop → master PR

If `master` branch does not yet exist on the remote:
- A PR cannot be created (branches are identical)
- Skip to step 3 — direct push is required

If `master` already exists and `develop` has new commits:
- Use `gh pr create --base master --head develop` with:
  - Title: descriptive deploy title
  - Body: include the CAB card key (e.g. `CAB-8994`) so GitHub for Jira auto-links the PR to the CAB card's "PRs Deploying" field
  - Reference the linked Jira story

### 3. Push to master (confirm with user first)

**Always confirm with the user before this step — it triggers the live prod deploy.**

For first deploy (master does not exist):
```bash
git push origin develop:master
```

For subsequent deploys (PR exists):
```bash
gh pr merge --merge
```

### 4. Monitor build/test job

Use `gh run list` and `gh run watch` to monitor progress. Report status updates.

Expected duration: 8–12 minutes (longer if Oracle Docker container startup is needed).

If tests fail, report the failure details and stop. Do not proceed to deploy.

### 5. Notify when prod gate is waiting

When the build/test job passes, the prod environment gate activates. At this point:
- Notify the user that a reviewer needs to approve in GitHub
- The required reviewers are set on the `prod` environment in GitHub repo settings
- The user needs to ping a team member (Maikol, Fernando, or Angela) to approve

Wait for approval before continuing.

### 6. Monitor the CDK deploy job

Once approved, watch the deploy job. Report completion or failure.

### 7. Post-deploy verification

Check that the deployment succeeded:
- Both CloudFormation stacks show `CREATE_COMPLETE` (or `UPDATE_COMPLETE`)
- Both Lambda functions exist and are active
- DynamoDB table exists
- API Gateway endpoint is reachable (HTTP 200 or 403, not 5xx)

Use AWS CLI via `aws cloudformation describe-stacks` and `aws lambda list-functions` with the prod profile.

### 8. Close the CAB card

Transition the CAB card to **Success** status using `transitionJiraIssue`.

Look up the available transitions with `getTransitionsForJiraIssue` to get the correct transition ID for Success.

### 9. Update memory

Update the project's `prod-deploy-checklist.md` to mark the deploy complete.

## Output

Final report:
- Deploy status (success/failure)
- CloudFormation stack names and statuses
- Lambda function names
- API Gateway URL (prod)
- CAB card status
- Any follow-up actions needed (e.g. configure Braze webhook with prod API GW URL)
