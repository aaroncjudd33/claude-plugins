---
name: setup
description: Morning setup — Jira briefing, Confluence updates, git repo scan, AWS SSO + CodeArtifact login. Start your day here.
---

# Daily Prep: Setup

Run the morning setup routine. Gathers status from Jira, Confluence, and local git repos, then logs into AWS SSO and CodeArtifact. Produces a clean briefing you can read in under 60 seconds.

## Instructions

Execute all sections below in order. Output results as you go — do not wait until the end.

### 1. Date Header

Print:
```
Morning Setup — <DayOfWeek>, <Month> <Day>, <Year>
===================================================
```

Use today's actual date.

### 2. AWS SSO + CodeArtifact Login

Run this FIRST because it requires a browser interaction and the user can authenticate while the rest of the briefing loads.

**Step 1 — Check if SSO is already active:**
```bash
aws sts get-caller-identity 2>/dev/null
```

If this succeeds, skip the login and report "SSO session active." Check the token expiry from `~/.aws/sso/cache/*.json` — warn if it expires within 2 hours.

If it fails, run:
```bash
aws sso login
```

This opens a browser. Wait for it to complete (it blocks until auth finishes).

**Step 2 — CodeArtifact logins (run both in parallel if possible):**
```bash
aws --profile devops codeartifact login --tool dotnet --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```
```bash
aws --profile devops codeartifact login --tool npm --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```

**Output format:**
```
AWS

  SSO: Active — expires in 11h 42m
  CodeArtifact (dotnet): Logged in
  CodeArtifact (npm): Logged in
```

If any step fails, report the error clearly and continue with the rest of the briefing.

### 3. JIRA — Open Tickets

<!-- SYNC NOTE: These 3 JQL queries are duplicated in jira/commands/my-stories.md (section 1).
     If you change them here, update that file too. -->

Run three JQL queries in parallel using `searchJiraIssuesUsingJql`:

**Query 1 — My tickets:**
```jql
assignee = "620147d91fec260068c1097d" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, duedate ASC
```

**Query 2 — Handed off (reassigned to someone else):**
```jql
project = BPT2 AND assignee WAS "620147d91fec260068c1097d" AND assignee != "620147d91fec260068c1097d" AND assignee is not EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

**Query 3 — Handed off (now unassigned):**
```jql
project = BPT2 AND assignee WAS "620147d91fec260068c1097d" AND assignee is EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

Merge Query 2 and Query 3 results into a single "Handed Off" section for display.

For Query 1: Group results by status. Within each group, sort by due date (earliest first, nulls last).

Flag tickets:
- `DUE TODAY` if duedate = today
- `OVERDUE (YYYY-MM-DD)` if duedate < today
- Show due date normally if set and in the future

For Query 2: Group by status. Show current assignee name after each ticket with `→ assigned to <Name>`.

**Output format:**
```
JIRA (N open tickets)

  In Progress (2)
    - BPT2-6189  TH Direct Deposit Info Capture              due: 2026-03-19
    - BPT2-6207  Allyant 473 ARIA treegrid

  Ready For Test (1)
    - BPT2-6100  Some ticket                                 DUE TODAY

  Open (2)
    - BPT2-6250  Future work item
    - BPT2-6251  Another item                                OVERDUE (2026-03-15)

JIRA — Handed Off (N tickets you worked on)

  Ready For Test (1)
    - BPT2-6189  TH Direct Deposit Info Capture              → assigned to Heber

  QA In-Progress (1)
    - BPT2-6207  Allyant 473 ARIA treegrid                   → assigned to Fernando
```

If no open tickets: `JIRA — No open tickets`
If no handed-off tickets: omit the Handed Off section entirely.

### 4. CONFLUENCE — Recent Activity

Run two CQL searches using `searchConfluenceUsingCql`:

1. `watcher = "620147d91fec260068c1097d" AND lastmodified > now("-7d") ORDER BY lastmodified DESC`
2. `mention = "620147d91fec260068c1097d" AND lastmodified > now("-7d") ORDER BY lastmodified DESC`

Deduplicate by page ID. Show max 10 results.

**Output format:**
```
CONFLUENCE (N recently modified)

  - "Page Title" in SpaceName — edited by Person, yesterday
  - "Another Page" in SpaceName — edited by Person, Mar 16
```

If no results: `CONFLUENCE — No recent activity`

Use relative dates where helpful: "today", "yesterday", "2 days ago", or the date if older.

### 5. GIT — Local Repo Scan

Scan for git repos in `C:\dev\*` and `C:\claude\*` (immediate subdirectories only).

For each directory containing a `.git` folder, check for:
- **Modified files**: tracked files with changes (staged or unstaged)
- **Untracked files**: new files not yet tracked by git
- **Unpushed commits**: commits ahead of the upstream branch

**Noise filtering**: Exclude these untracked patterns from counts and reporting — they are tool artifacts, not real work:
- `^?? \.claude/`
- `^?? \.idea/`
- `^?? CLAUDE\.md`
- `^?? node_modules/`
- `^?? \.vs/`

Only show repos that have modified files, meaningful untracked files, or unpushed commits after filtering. Skip clean repos.

Use precise labels: "modified files", "untracked files", "unpushed commits" — never the vague "uncommitted changes".

**Output format:**
```
GIT (N repos need attention)

  C:\dev\virtual-office (integration/BPT2-6189-BPT2-6207)
    - 2 modified files
    - 1 unpushed commit
  C:\dev\openid-server (feature/BPT2-6170-signin-button-not-a-button)
    - 3 untracked files
```

If all repos are clean: `GIT — All repos clean`

Run all git checks in a single Bash call using a loop for efficiency.

### 6. OUTLOOK — Inbox Triage

Pull inbox emails using `list_emails` (folder: inbox, top: 50). Apply all known sender rules from memory file `project_inbox_triage.md` silently:

- **Non-Action moves** (Github, AWS, Jira, Braze, Teams, Bamboo, Docs, Training, Archive, Amplitude, etc.): mark as read first (`mail.mark_read`), then move (`mail.move`). Run in parallel batches.
- **Action moves**: leave unread, move to Action folder.

After auto-routing, if any emails remain that don't match a known sender rule, list them grouped by sender and ask the user what to do with each group:
- Move to a folder (and add a new rule)
- Leave in inbox
- Skip for now

**Output format:**
```
OUTLOOK

  Inbox: 3 emails processed
    - Github (2) → Github
    - AWS (1) → AWS
  Inbox clear.
```

If unknowns remain after auto-routing, list them after the summary and wait for user input before continuing to the next section.

If inbox is already empty: `OUTLOOK — Inbox already clear`

### 7. CALENDAR

Print:
```
CALENDAR

  Coming soon — today's meetings via Microsoft 365
```

### 8. Done

Print a closing line:
```
---
Setup complete. Have a good day.
```

## Error Handling

- If any section fails (MCP auth issue, network error, etc.), print the error under that section and continue with the rest. Never let one failure block the entire briefing.
- If Atlassian MCP is unavailable, skip Jira and Confluence sections with a note.
- If AWS CLI is not installed or configured, skip AWS section with a note.
