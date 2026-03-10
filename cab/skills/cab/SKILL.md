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
| Deployment Plan | `customfield_13142` | ADF | Step-by-step deploy instructions |
| Rollback Plan | `customfield_13101` | ADF | Step-by-step rollback instructions |
| Pre-Deployment Tests | `customfield_13099` | ADF | What to verify before deploy |
| Post-Deployment Tests | `customfield_13100` | ADF | What to verify after deploy |

### Optional Fields

| Field | Custom Field ID | Type | Notes |
|-------|----------------|------|-------|
| Deployment Playbook | `customfield_13143` | ADF | Link to Confluence playbook if available |

### Do Not Use

| Field | Note |
|-------|------|
| `customfield_13156` | Internal field — not PRs Deploying. Leave null. |
| PRs Deploying | **Read-only** — auto-populated by GitHub for Jira when a PR references the CAB issue key. Cannot be set via API. |

---

## People

| Person | Role | Account ID |
|--------|------|-----------|
| Aaron Judd | Change Conductor / QA Approved By (default) | `620147d91fec260068c1097d` |
| Heber Iraheta | QA Approved By | `557058:055d4592-8fbf-4b3c-8115-0dc48da8a1b4` |
| Sudhakar Seerapu | Post-submit Assignee | `60aeba90f3fab100683274d9` |

---

## Workflow

### Step 1 — Create the issue

Use `createJiraIssue`. Populate all fields from the table above in a single call. Do not leave ADF fields empty — use "None" or "N/A" in a paragraph node if not applicable.

### Step 2 — Link related Jira stories

Use `jiraWrite` with `action=createIssueLink`, `type="Relates"` to link each related story/epic.

### Step 3 — Submit for review

Use `transitionJiraIssue` with transition ID `201` ("Send For Review"). This transition **requires** `customfield_13174` (QA Approved By) — always set to Heber Iraheta: `557058:055d4592-8fbf-4b3c-8115-0dc48da8a1b4`.

```json
{
  "transition": { "id": "201" },
  "fields": {
    "customfield_13174": { "accountId": "557058:055d4592-8fbf-4b3c-8115-0dc48da8a1b4" }
  }
}
```

### Step 4 — Update assignee to Sudhakar

Use `editJiraIssue` immediately after transition (before the issue locks):
```json
{ "assignee": { "accountId": "60aeba90f3fab100683274d9" } }
```

**Important:** The API blocks edits once the card moves past Change Review. Do this step immediately after the transition call, in the same turn.

### Step 5 — Add PRs Deploying comment (if no PR exists yet)

If the deployment PR doesn't exist yet (e.g. first deploy, master branch not created), add a comment explaining why:
- Note that the PR will be created immediately before deployment
- Reference the related Jira story

---

## Transition IDs

| Transition | ID | Notes |
|-----------|-----|-------|
| Send For Review | `201` | Requires `customfield_13174` (QA Approved By) |
| Cancel Change | `111` | |
| Mark Implementation | (auto after approval) | Card moves to Implementation after CAB approval |
| Mark Success | Look up at time of use | Set after successful prod deploy |

---

## Timezone Reference

- MST (standard, Nov–Mar): UTC-7 → add 7 hours to local time
- MDT (daylight saving, Mar–Nov): UTC-6 → add 6 hours to local time
- Example: 12:30 PM MST = 19:30 UTC = `2026-03-10T19:30:00.000+0000`
