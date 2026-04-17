---
name: release
description: Use this skill when the user needs to create, update, submit, or execute a production release at Young Living. Trigger phrases include "create a CAB card", "I need to deploy to prod", "set up a CAB for this release", "update the CAB card", "submit for review", "execute the deploy", or any mention of a CAB number (e.g. CAB-456).
---

# CAB Card Skill

This skill encodes everything needed to create, populate, and submit a CAB (Change Advisory Board) card in Jira at Young Living. All field IDs, option IDs, workflows, and quirks are documented here.

---

## Atlassian Connection

Always use these without asking — defined in global `CLAUDE.md`:

- Instance: `https://younglivingeo.atlassian.net`
- Cloud ID: `9de6eb2b-2683-44e6-89ff-c622027e09b4`
- Auth: Handled by the `claude.ai` Atlassian MCP

---

## Project / Issue Type

| Field | Value |
|-------|-------|
| Project Key | `CAB` |
| Project ID | `12765` |
| Issue Type | `IT Software Change` |
| Issue Type ID | `11101` |

---

## Field Reference

All fields that must be populated. ADF fields use `{ "type": "doc", "version": 1, "content": [...] }` format.

### Standard Fields

| Field | API Key | Type | Notes |
|-------|---------|------|-------|
| Summary | `summary` | string | Format: `<TEAM> - <Project> - <Change Description>` |
| Description | `description` | ADF | Full description: what's being deployed, why, phased approach if any |

### Custom Fields — Always Set at Creation

| Field | Custom Field ID | Type | Default / Notes |
|-------|----------------|------|-----------------|
| Release Notes | `customfield_10512` | ADF | What changed for users. Not in edit metadata but writable via API. |
| CAB Impact | `customfield_14676` | option ID | **Low: `16399`**, Medium: `16398`, High: `16397`. Default: Low. |
| CAB Risk | `customfield_13144` | option ID | Low: `13523`, Medium: `13524`, High: `13525` |
| CAB Request Type | `customfield_13159` | option ID | **Standard: `13544`**, Emergency: `13545` |
| Dev Team | `customfield_13110` | option ID | **BP2: `14429`** |
| Requested Deployment Date/Time | `customfield_13137` | datetime string | ISO 8601 UTC. MST = UTC-7, MDT = UTC-6. e.g. `2026-03-10T19:30:00.000+0000` |
| Requires Outage Window | `customfield_11624` | option ID | **No: `11754`**, Yes: `11755` |
| Can it be rolled back? | `customfield_12001` | option ID | **Yes: `12005`**, No: `12006` |
| Change Conductor | `customfield_13109` | user (accountId) | **Aaron Judd: `620147d91fec260068c1097d`** — always set |
| Platform Component(s) | `customfield_13076` | array of option IDs | Multi-select. AWS: `14916`, Virtual Office: `13243`, MainSite: `13232`, Legacy DB: `13231`, Brand Partner ACL: `18163` |
| Component Version(s) | `customfield_13141` | ADF | Table: Repository / Branch / Pull Request |
| Config/Settings Changes | `customfield_13176` | ADF | SSM params, env vars, feature flags, etc. Use "None" if not applicable. |
| Expenditures | `customfield_10902` | option ID | **Opex: `10948`**, Capex: `10949`. Default: Opex. |
| Deployment Plan | `customfield_13142` | ADF | Step-by-step deploy instructions (see project-specific templates below) |
| Deployment Playbook | `customfield_13143` | ADF | Typically same content as Deployment Plan |
| Rollback Plan | `customfield_13101` | ADF | Step-by-step rollback instructions (see project-specific templates below) |
| Pre-Deployment Tests | `customfield_13099` | ADF | What to verify before deploy |
| Post-Deployment Tests | `customfield_13100` | ADF | What to verify after deploy |
| Code Review Approver | `customfield_13612` | user (accountId) | **Heber Iraheta: `557058:055d4592-8fbf-4b3c-8115-0dc48da8a1b4`** |
| QA Approved By | `customfield_13174` | user (accountId) | **Heber Iraheta: `557058:055d4592-8fbf-4b3c-8115-0dc48da8a1b4`** — required for Send For Review transition |
| Date of Code Review | `customfield_14671` | date string | e.g. `2026-03-18` |
| Clone/Stage Status | `customfield_14664` | option ID | Not Required: `16376`, Previously Deployed: `16377`, **Part of This Deployment: `16378`** |
| Date Tested in Clone/Stage | `customfield_14665` | date string | e.g. `2026-03-18` |
| PRs Deploying | `customfield_14670` | ADF | PR title + link. Format: `"<PR title> - Pull Request #<N> - <org>/<repo>"` with link to PR URL. |

### Do Not Use

| Field | Note |
|-------|------|
| `customfield_13156` | "Platform Components" — NOT PRs Deploying. Leave null. |

---

## People

| Person | Role | Account ID |
|--------|------|-----------|
| Aaron Judd | Change Conductor / QA Approved By (default) | `620147d91fec260068c1097d` |
| Heber Iraheta | QA Approved By | `557058:055d4592-8fbf-4b3c-8115-0dc48da8a1b4` |
| Sudhakar Seerapu | Post-submit Assignee | `60aeba90f3fab100683274d9` |

---

## Workflow

### Step 1 — Fetch linked stories

Call `getJiraIssue` for each story. Extract summaries (→ Release Notes), descriptions (→ CAB Description seed), and validate status. Warn if any story is not in a deployable state.

### Step 2 — Create the Jira issue (minimal — to get the CAB key)

Call `createJiraIssue` with summary and all non-ADF fields (option IDs, user IDs, datetime) to get the CAB key immediately. ADF fields are set in step 5 after the PR is known.

### Step 3 — Create the release branch

Branch name: `release/CAB-XXXX`. For VO, merge each story's feature branch into it and confirm env6 testing before continuing. For CDK, branch from `develop` and confirm all feature PRs are merged.

Push: `git push -u origin release/CAB-XXXX`

### Step 4 — Create the PR

`gh pr create --base master --head release/CAB-XXXX`. Include the CAB key in the PR body so GitHub for Jira auto-links. Exception: CDK first deploy (no master) — skip PR, note "first deploy — direct push to master".

### Step 5 — Populate all ADF fields via editJiraIssue

Set description, Release Notes (auto-built from story summaries), deployment plan, rollback plan, pre/post-deploy tests, config changes, Component Version(s), and PRs Deploying — all in one `editJiraIssue` call.

### Step 6 — Link related Jira stories

Call `createIssueLink` with `type="Deploy Location"` for each story. This semantically means "this CAB deploys this story".

### Step 7 — Comment back on each story

Call `addCommentToJiraIssue` on each linked story with the CAB key, deploy date, release branch, and PR link. This surfaces deployment context to QA, PM, and app support without them needing to find the CAB card.

### Step 8 — Submit for review (user handles manually)

Do NOT call `transitionJiraIssue` for Send For Review or change the assignee — the user handles these steps manually. Stop after all fields are populated, stories are linked, and comments are posted.

---

## Link Registration

After creating a CAB card and PR, register all artifacts in `C:\Users\ajudd\.claude\browser-links.json`:

1. Read `browser-links.json`
2. Add CAB link: `"cab:CAB-XXX": { "url": "https://younglivingeo.atlassian.net/browse/CAB-XXX", "description": "<CAB summary>" }`
3. Add PR link: `"pr:repo-name#NNN": { "url": "<github PR url>", "description": "<PR title>" }`
4. For each linked story workspace (`BPT2-XXXX`): add `cab:CAB-XXX` and `pr:repo-name#NNN` to that workspace's `links` array
5. Write back to `browser-links.json`

During `release:deploy`, also register the Actions run:
- `"actions:repo-name#run-NNN": { "url": "<actions run url>", "description": "Deploy run for CAB-XXX" }`
- Add to the story workspace(s)

---

## Transition IDs

| Transition | ID | Notes | Used by |
|-----------|-----|-------|---------|
| Send For Review | `201` | Requires `customfield_13174` (QA Approved By) | user manually |
| Cancel Change | `111` | | user manually |
| Mark Implementation | (auto after approval) | Card moves to Implementation after CAB approval | automatic |
| Mark Success | Look up at time of use | Set after successful prod deploy | `deploy` |

---

## Project-Specific Templates

### Virtual Office (VO)

**Deployment Plan / Deployment Playbook:**
1. Merge Virtual Office PR to master
2. Build and Deploy master to prod
3. Bust Front End Cache: `https://www.youngliving.com/vo/cache/invalidate`
4. Clear NHibernate Cache: `https://www.youngliving.com/api/shopping/dev/cache/clear`
5. QA Testing and app support validation
6. Mark cards as Released
7. Close CAB

**Rollback Plan:**
1. Revert the last commit on the master branch on Virtual Office
2. Deploy previous version of Virtual Office
3. App support validation in PROD
4. Run automation tests

**Pre-Deployment Tests:** Tested in env6

**Post-Deployment Tests:** Tested in Prod

**Platform Component(s):** Virtual Office (`13243`)

### CDK Services (AWS Lambda / API Gateway)

**Deployment Plan / Deployment Playbook:**
1. Merge PR to master
2. GitHub Actions build/test job runs automatically
3. Approve prod environment gate in GitHub
4. CDK deploy executes automatically
5. Verify CloudFormation stacks show UPDATE_COMPLETE
6. Verify Lambda functions are active
7. QA Testing
8. Close CAB

**Rollback Plan:**
1. `cdk destroy` the failing stacks (or revert commit and redeploy)
2. Verify rollback via CloudFormation console
3. App support validation

**Pre-Deployment Tests:** Tested in dev/stage environments

**Post-Deployment Tests:** Tested in Prod — verify API endpoints return expected responses

**Platform Component(s):** AWS (`14916`)

---

## Timezone Reference

- MST (standard, Nov–Mar): UTC-7 → add 7 hours to local time
- MDT (daylight saving, Mar–Nov): UTC-6 → add 6 hours to local time
- Example: 12:30 PM MST = 19:30 UTC = `2026-03-10T19:30:00.000+0000`

---

## Teams Messaging

Whenever any step in this plugin posts a Teams message, apply these rules without exception:

1. **Always end with the Claude signature** — no exceptions:
   `<p><em>Posted by Claude on behalf of Aaron Judd</em></p>`
2. **Always preview before sending.** Show the full message content and wait for explicit approval before calling `send_chat_message`.
3. **Always use HTML formatting.** `send_chat_message` body supports and renders HTML.
4. **Always open with an intro paragraph** (`<p>`) before the first section.
5. **Follow the HTML guide.** Read `~/.claude/plugins/marketplaces/ajudd-claude-plugins/comms/skills/comms/references/teams-html-guide.md` before drafting any message.

Standard message template:

```html
<p><b>Message Title</b></p>
<p>&nbsp;</p>
<p>Intro — context, who this is for, why you're sending it.</p>
<p>&nbsp;</p>
<p><b>Section One</b></p>
<ul>
  <li><b>Item</b> — detail</li>
</ul>
<p>&nbsp;</p>
<p><em>Posted by Claude on behalf of Aaron Judd</em></p>
```
