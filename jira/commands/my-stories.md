---
name: my-stories
description: List open Jira stories assigned to me or previously assigned to me, with status, assignee, and due dates.
---

# Jira: My Stories

Show all open/active Jira stories that are mine or were recently mine.

## Instructions

### 1. Run JQL Queries

Use `searchJiraIssuesUsingJql` on cloud ID `9de6eb2b-2683-44e6-89ff-c622027e09b4`. Run both queries in parallel.

**Query 1 — Currently assigned to me:**
```jql
assignee = "620147d91fec260068c1097d" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated, "Approved for Release") ORDER BY status ASC, duedate ASC
```

**Query 2 — Previously assigned to me (handed off):**
```jql
assignee WAS "620147d91fec260068c1097d" AND assignee != "620147d91fec260068c1097d" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated, "Approved for Release") ORDER BY status ASC, updated DESC
```

Request fields: `summary, status, assignee, duedate, priority`

### 2. Format Output

Print a clean, scannable list grouped by status. Use this format:

```
My Jira Stories
===============

ASSIGNED TO ME
  <STATUS>
    <KEY> — <Summary>
      Assignee: <name>  |  Due: <date or "none">  |  Priority: <priority>

HANDED OFF (was mine)
  <STATUS>
    <KEY> — <Summary>
      Assignee: <name>  |  Due: <date or "none">  |  Priority: <priority>
```

### 3. Flagging Rules

- `OVERDUE (<date>)` if duedate is before today
- `DUE TODAY` if duedate is today
- Show due date normally if set and in the future
- Show "none" if no due date

### 4. Summary Line

At the bottom, print a one-line count:
```
Total: <N> assigned to me, <N> handed off
```
