---
name: jira
description: Jira briefing — open tickets and recently handed-off work.
---

# Setup: Jira

Fetch and display open Jira tickets assigned to you, plus recently handed-off work.

## Instructions

<!-- SYNC NOTE: These 3 JQL queries are duplicated in jira/commands/my-stories.md (section 1), setup/commands/local.md (section 3), and setup/skills/setup/SKILL.md.
     If you change them here, update all three. -->

Run three JQL queries in parallel using `searchJiraIssuesUsingJql`. Request fields: `summary, status, assignee, duedate, priority`.

**Query 1 — My tickets:**
```jql
assignee = "620147d91fec260068c1097d" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, duedate ASC
```

**Query 2 — Handed off (reassigned):**
```jql
project = BPT2 AND assignee WAS "620147d91fec260068c1097d" AND assignee != "620147d91fec260068c1097d" AND assignee is not EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

**Query 3 — Handed off (unassigned):**
```jql
project = BPT2 AND assignee WAS "620147d91fec260068c1097d" AND assignee is EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

Merge Q2 + Q3 into a single "Handed Off" section.

For Q1: group by status in this order (skip empty groups): In Progress → Ready For Test / In Review / In QA → Open / To Do / Backlog → any other. Sort by due date within each group (nulls last).

Flags:
- `DUE TODAY` if duedate = today
- `OVERDUE (YYYY-MM-DD)` if duedate < today
- No flag if duedate is null or future

**Output:**
```
JIRA (N open tickets)

  In Progress (2)
    - BPT2-6189  TH Direct Deposit Info Capture              due: 2026-03-19
    - BPT2-6207  Allyant 473 ARIA treegrid

  Ready For Test (1)
    - BPT2-6100  Some ticket                                 DUE TODAY

JIRA — Handed Off (N tickets you worked on)

  Ready For Test (1)
    - BPT2-6189  TH Direct Deposit Info Capture              → assigned to Heber
```

If no open tickets: `JIRA — No open tickets`
If no handed-off tickets: omit the Handed Off section entirely.
If Atlassian MCP is unavailable: print `JIRA — Unavailable` and stop.
