---
name: my-stories
description: List open Jira stories assigned to me or previously assigned to me, with status, assignee, and due dates. Supports hide/unhide and change detection.
---

# Jira: My Stories

Show all open/active Jira stories that are mine or were recently mine.

## Arguments

Parse the user's arguments (everything after `/jira:my-stories`):

- **No args** — default view (hidden stories excluded)
- **`-all`** — show all stories including hidden, mark hidden ones with `[HIDDEN]`
- **`hide <KEY>` or `hide <NUMBER>`** — hide a story. If just a number like `6190`, expand to `BPT2-6190`. If no `-r "reason"` flag provided, ask the user: "Add a reason? (or press enter to skip)"
- **`unhide <KEY>` or `unhide <NUMBER>`** — unhide a story
- **`-r "reason"`** — used with `hide` to set the reason inline without prompting

### Hide/Unhide Flow

If the command is `hide` or `unhide`:

1. Read the registry file at `~/.claude/jira-stories.json`
2. For `hide`: set `hidden: true`, `hideReason` to the provided reason (or null), `hiddenDate` to today's date
3. For `unhide`: set `hidden: false`, `hideReason: null`, `hiddenDate: null`
4. Write the updated registry file
5. Confirm: "BPT2-XXXX hidden." or "BPT2-XXXX unhidden."
6. **Stop here** — do not run the JQL queries or display the story list

## Instructions (for default and -all)

### 1. Load Registry

Read `~/.claude/jira-stories.json`. If it doesn't exist, start with an empty object `{}`.

### 2. Run JQL Queries

<!-- SYNC NOTE: These 3 JQL queries are duplicated in daily-prep/commands/setup.md (section 3).
     If you change them here, update that file too. -->

Use `searchJiraIssuesUsingJql` on cloud ID `9de6eb2b-2683-44e6-89ff-c622027e09b4`. Run all three queries in parallel.

**Query 1 — Currently assigned to me:**
```jql
assignee = "620147d91fec260068c1097d" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, duedate ASC
```

**Query 2 — Previously assigned to me (reassigned to someone else):**
```jql
project = BPT2 AND assignee WAS "620147d91fec260068c1097d" AND assignee != "620147d91fec260068c1097d" AND assignee is not EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

**Query 3 — Previously assigned to me (now unassigned):**
```jql
project = BPT2 AND assignee WAS "620147d91fec260068c1097d" AND assignee is EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

Request fields: `summary, status, assignee, duedate, priority`

Merge Query 2 and Query 3 results into a single "HANDED OFF" group for display.

### 3. Update Registry & Detect Changes

For each story returned by the queries:

1. **Auto-populate**: If the story key doesn't exist in the registry, add it with defaults (`hidden: false`, current status/assignee, `lastSeen: today`, empty tags, null notes)
2. **Detect changes**: Compare current status and assignee against `lastStatus` and `lastAssignee` in the registry. Collect changes for display.
3. **Auto-unhide**: If a story is marked `hidden: true` BUT it appears in Query 1 (currently assigned to me), automatically set `hidden: false` and `hideReason: null`. Add to changes list: "auto-unhidden (reassigned to you)"
4. **Update**: Set `lastStatus`, `lastAssignee`, and `lastSeen` to current values

Write the updated registry back to `~/.claude/jira-stories.json`.

### 4. Filter

- **Default (no `-all`)**: Exclude stories where `hidden: true`
- **`-all`**: Include everything, append `[HIDDEN]` tag to hidden stories

### 5. Format Output

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

### 6. Changes Section

If any status or assignee changes were detected (comparing registry `lastStatus`/`lastAssignee` to current), print a CHANGES section before the summary line:

```
CHANGES SINCE LAST RUN
  BPT2-6190: Blocked -> In Progress
  BPT2-6222: assignee changed (Aaron Judd -> unassigned)
  BPT2-6190: auto-unhidden (reassigned to you)
```

If no changes, omit this section entirely.

### 7. Flagging Rules

- `OVERDUE (<date>)` if duedate is before today
- `DUE TODAY` if duedate is today
- Show due date normally if set and in the future
- Show "none" if no due date

### 8. Summary Line

At the bottom, print a one-line count:
```
Total: <N> assigned to me, <N> handed off
```

If stories are hidden (and not using `-all`), append: `, <N> hidden (use -all to show)`
