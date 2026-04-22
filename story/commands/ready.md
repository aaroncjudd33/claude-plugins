---
name: ready
description: Team-scope view of all unassigned BPT2 stories in "Ready For Work" status. Grouped by feature area and repo. Shows what's available to pick up, with diff output highlighting new and picked-up stories since last run.
---

# Story: Ready For Work

Show all unassigned BPT2 stories in "Ready For Work" status. Grouped by feature area and repo. Diff output shows what changed since the last run.

## Cache

File: `~/.claude/jira-ready-cache.json`

Schema:
```json
{
  "lastRun": "YYYY-MM-DD",
  "stories": {
    "BPT2-XXXX": {
      "summary": "...",
      "status": "Ready For Work",
      "priority": "Medium",
      "repo": "repo-name",
      "featureArea": "Infrastructure / Dependencies",
      "description": "<first 500 chars>",
      "assignee": null,
      "firstSeen": "YYYY-MM-DD",
      "lastSeen": "YYYY-MM-DD"
    }
  }
}
```

Read it at startup. If it does not exist, start with `{ "lastRun": null, "stories": {} }`.

## Instructions

### 1. Query Jira

Use `searchJiraIssuesUsingJql` on cloud ID `9de6eb2b-2683-44e6-89ff-c622027e09b4`.

```jql
project = BPT2 AND status = "Ready For Work" AND assignee is EMPTY ORDER BY priority ASC, created DESC
```

Request fields: `summary, status, assignee, priority, description`

### 2. Diff Against Cache

Compare results against cached stories:

- **New** — key appears in results but not in cache → fetch full description via `getJiraIssue`, extract repo and featureArea, add to cache with `firstSeen` and `lastSeen` = today
- **Picked up or moved** — key appears in cache but not in results → mark for removal, collect for diff display
- **Unchanged** — appears in both → update `lastSeen` = today, skip description fetch

For new stories, run `getJiraIssue` in parallel batches of 10.

### 3. Categorize New Stories

**Repo extraction** (apply to new stories only):
- If summary starts with `[bracket-prefix]` — use that (e.g. `[gen-leadership-bonus]` → `gen-leadership-bonus`)
- Otherwise scan description for GitHub URLs, service names, or repo references
- Fallback: `"unknown"`

**Feature area** (derive from summary + description keywords):

| Keywords | Feature Area |
|----------|-------------|
| CDK, Dockerfile, net6, net7, net8, Node upgrade, Dependabot, upgrade, migrate, bump | Infrastructure / Dependencies |
| Enrollment, vo-enrollment, E², Tax ID, Razzle | Enrollment |
| Payout, Direct Deposit, PayQuicker, Commissions, commission | Payout Preferences |
| Search, OpenSearch, Algolia, index, Digital Library | Search |
| EventBridge, SQS, Lambda, DynamoDB, event-driven | Event Infrastructure |
| Glassbox, GTM, tag, analytics | Analytics / Tag Removal |
| CAB, release, deploy | Release / CAB |
| SPIKE, Investigate, POC, proof of concept | Spike / Research |
| Notes, VOT, downline, decommission | Downline / Notes |
| Shopify, GLB, Brand Partner, enrollment | Brand Partner |
| Fallback | Uncategorized |

### 4. Write Cache

Update `lastRun` to today. Remove picked-up/moved stories. Write `~/.claude/jira-ready-cache.json`.

### 5. Display

```
BPT2 — Ready For Work
=====================
Last updated: <date>  |  <N> stories available

CHANGES SINCE LAST RUN
  + BPT2-XXXX  [new]      Summary here
  - BPT2-XXXX  [picked up]  Summary here
(omit this section entirely if no changes, or if this is the first run)

<Feature Area> (<N>)
  <repo-name>
    BPT2-XXXX — Summary  [Priority]  <tag>

<Feature Area> (<N>)
  <repo-name>
    BPT2-XXXX — Summary  [Priority]

...

Uncategorized (<N>)
  unknown
    BPT2-XXXX — Summary  [Priority]
(omit this section if empty)

---
Total: <N> stories ready for work across <M> repos
```

**Tags** (append inline after priority):
- `[new]` — `firstSeen` = today
- `[stale?]` — `firstSeen` more than 14 days before today
- No tag otherwise

**Sorting within each group:** priority order (Critical → High → Medium → Low), then by key descending.

**First run:** Omit the CHANGES section. Print a note at the top: `(First run — no previous data to compare against)`
