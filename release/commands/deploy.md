---
name: deploy
description: Execute a production deployment — merge the existing PR, monitor the GitHub Actions workflow, notify when reviewer approval is needed, verify post-deploy, and close the CAB card.
argument-hint: "[cab-card-key]"
---

# CAB: Execute Deploy

Run the full production deployment sequence. The CAB card must already be in **Implementation** status (approved) and the deployment PR must already exist (created during `/release:create`). Supports both CDK services and Virtual Office deployments.

## Prerequisites

Before invoking this command, confirm:
- CAB card is in **Implementation** status (approved by Sudhakar)
- Deployment PR exists and is open (created during `/release:create`)
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

### 2a. Create deploy calendar invite

Read `~/.claude/plugins/team.json`. Collect all members with role `cab-invite` — these are the **only** attendees. Do not use story chat members, dev team members, or any other source.

Get the deploy date/time from `customfield_13137` on the CAB card (already fetched in Step 2).

Create a calendar event via yl-msoffice `create_event`:
- **Title:** `[Deploy] <CAB card summary>`
- **Start:** deploy date/time from `customfield_13137`
- **Duration:** 1 hour
- **Body:** `Production deployment for <CAB-KEY>. Stories: <BPT2-XXXX, ...>. PR: <PR URL>.`
- **Attendees:** `email` of each `cab-invite` member from team.json

Call `confirm_action` to send the invite (required when attendees are specified).

---

## CDK Service Flow

### 3a. Find the existing PR

Run `gh pr list --base master --state open` to locate the deployment PR.

**First deploy** (master branch does not exist on remote — check with `git ls-remote --exit-code origin master`):
- No PR exists — a direct push will be used
- Confirm with the user and proceed to step 4a

**PR found:** confirm it is the correct one and proceed.

**No PR found (and not first deploy):** Stop. "No open PR found targeting master. Verify the PR was created during `/release:create`, or run `/release:update` → Update PR / branch info to add it."

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
- Read `~/.claude/plugins/team.json` → list all members with role `pr-reviewer` → display their names so the user knows who to ping

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

### 3b. Find the existing PR

Run `gh pr list --base master --state open` to locate the deployment PR.

**PR found:** confirm it is the correct one and proceed.

**No PR found:** Stop. "No open PR found targeting master. Verify the PR was created during `/release:create`, or run `/release:update` → Update PR / branch info to add it."

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

### Register deploy run link

Get the deploy run ID from the completed workflow run. If you have been running `gh run watch` throughout, the run ID is already in context. Otherwise:

```bash
gh run list --limit 1 --json databaseId --jq '.[0].databaseId'
```

Derive the repo name and org from the git remote:

```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Read `~/.claude/browser-links.json`.

**Add to `links` section (if not already present):**
- `actions:<repo-name>#run-<run-id>` → `https://github.com/<org>/<repo>/actions/runs/<run-id>`, description: `<CAB-XXX> deploy run`

**Append to the CAB workspace** (if it exists in `browser-links.json`):
- `actions:<repo-name>#run-<run-id>`

**Append to each linked story workspace** (if those workspaces exist):
- `actions:<repo-name>#run-<run-id>`

Write back `~/.claude/browser-links.json`. Do not prompt the user during this step.

### Acknowledge post-deployment checks

Read `~/.claude/memory/sessions/<slug>/CAB-XXX.md` for the `Related stories` field.

For each related story key (e.g., `BPT2-6337`):
1. Read `~/.claude/memory/sessions/<slug>/<story-key>.md`
2. Extract the `Post-deployment checks:` field
3. Collect all `- [ ]` (unchecked) and `- [x]` (already acknowledged) items

If no related stories have a `Post-deployment checks:` field, skip this section silently.

If any checks exist, display them grouped by story:

```
Post-Deployment Checks

  BPT2-6337 — <story title>
    [ ] Monitor 2+ hours — confirm no AWS alert emails on 2-hour cycle
    [ ] Check CloudWatch alarm state returns to OK

  BPT2-6200 — <story title>
    [x] Verify enrollment flow end-to-end in prod (already acknowledged)
```

For each **unchecked** item, prompt: "Acknowledge? (Yes / Skip)"

- **Yes:** mark the item as `[x]` in the story's session file; rewrite the file
- **Skip:** leave unchecked — note that a follow-up story may be needed if the expected outcome is not met

After all prompts, print a summary:
```
Post-deploy checks: N acknowledged, N pending
```

If any were skipped, add a note: "Pending checks may indicate a follow-up story is needed — revisit when you've had time to verify the expected outcome."

**This step is informational — the CAB closes regardless of check status.**

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

### Archive Proposed Work pages

For each related BPT2 story, check whether a "Proposed Work" Confluence planning page exists. If found, archive it now that the story has shipped.

For each related story key:

1. Check `MEMORY.md` in the current project root for any entry containing both "Proposed Work" and the story key. If found, note the page ID or URL.

2. If not in MEMORY.md, search Confluence:
   ```
   searchConfluenceUsingCql:
     cql: 'title ~ "Proposed Work" AND text ~ "<BPT2-XXXX>"'
   ```

3. If a Proposed Work page is found, prompt:
   ```
   Found Proposed Work page for BPT2-XXXX: "<page title>"
   Archive it now that this story has shipped? (Yes / Skip)
   ```

4. **If Yes:** follow the `/docs:archive` command instructions to move the page to the Archive section under the project parent page.

5. **If no page found or Skip:** continue to the next story silently.

Skip this step entirely if no related stories have a Proposed Work page.

### Update memory

Update the CAB session file to mark the deploy complete. Clear `Related stories` only after all story transitions are resolved (or explicitly skipped).

## Output

Final report:
- Deploy status (success/failure)
- For CDK: CloudFormation stack names/statuses, Lambda function names, API Gateway URL
- For VO: Cache bust confirmation
- CAB card status
- Any follow-up actions needed
