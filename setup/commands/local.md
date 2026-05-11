---
name: local
description: Morning setup — AWS login, Jira briefing, Confluence activity, calendar. Start your day here.
---

# Setup: Local

Full morning setup. Gets your environment ready and shows what you have to work on today. Output each section as it completes — do not wait until the end.

## Instructions

### 0. Read User Config

Read `~/.claude/plugins/user-config.json` and extract `user.jiraAccountId` — this is `{ACCOUNT_ID}` used in all JQL and CQL queries below.

If the file does not exist or `jiraAccountId` is empty, stop and say: "Your identity is not configured. Run `/setup:onboarding` first."

### 1. Date Header

Print:
```
Morning Setup — <DayOfWeek>, <Month> <Day>, <Year>
===================================================
```

Use today's actual date.

### 2. AWS SSO + CodeArtifact

Run first — requires browser interaction. User can authenticate while the rest loads.

**Step 1 — Check SSO:**
```bash
aws sts get-caller-identity 2>/dev/null
```
- Succeeds → "SSO session active." Parse `~/.aws/sso/cache/*.json` for expiry — warn if < 2 hours.
- Fails → run `aws sso login` (blocks until browser auth finishes).

<!-- SYNC NOTE: These bash commands are duplicated in setup/commands/aws.md. If you change them here, update there too. -->
**Step 2 — CodeArtifact (both in parallel):**
```bash
aws --profile devops codeartifact login --tool dotnet --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```
```bash
aws --profile devops codeartifact login --tool npm --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```

Output:
```
AWS

  SSO: Active — expires in 11h 42m
  CodeArtifact (dotnet): Logged in
  CodeArtifact (npm): Logged in
```

### 3. Jira

<!-- SYNC NOTE: These 3 JQL queries are duplicated in story/commands/my-stories.md (section 1), setup/commands/jira.md, setup/skills/setup/SKILL.md, and this file.
     CANONICAL SOURCE: story/skills/story/SKILL.md — update there first, then sync all four. -->

Run three JQL queries in parallel (searchJiraIssuesUsingJql). Request fields: `summary, status, assignee, duedate, priority`.

**Query 1 — My tickets:**
```jql
project = BPT2 AND assignee = "{ACCOUNT_ID}" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, duedate ASC
```

**Query 2 — Handed off (reassigned):**
```jql
project = BPT2 AND assignee WAS "{ACCOUNT_ID}" AND assignee != "{ACCOUNT_ID}" AND assignee is not EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

**Query 3 — Handed off (unassigned):**
```jql
project = BPT2 AND assignee WAS "{ACCOUNT_ID}" AND assignee is EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

Merge Q2 + Q3 into a single "Handed Off" section. For Q1, group by status (In Progress → Ready For Test/In Review/In QA → Open/To Do/Backlog → other), sort by due date within each group (nulls last).

Flags: `DUE TODAY` / `OVERDUE (YYYY-MM-DD)` / no flag if null or future.

Output:
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
If no handed-off: omit Handed Off section.
If Atlassian MCP unavailable: `JIRA — Unavailable`

### 4. Confluence

<!-- SYNC NOTE: These CQL queries are duplicated in setup/commands/confluence.md. If you change them here, update there too. -->
Run two CQL searches in parallel (searchConfluenceUsingCql):
1. `watcher = "{ACCOUNT_ID}" AND lastmodified > now("-7d") ORDER BY lastmodified DESC`
2. `mention = "{ACCOUNT_ID}" AND lastmodified > now("-7d") ORDER BY lastmodified DESC`

Deduplicate by page ID. Max 10 results. Use relative dates ("today", "yesterday", "2 days ago", or the date if older).

Output:
```
CONFLUENCE (N recently modified)

  - "Page Title" in SpaceName — edited by Person, yesterday
  - "Another Page" in SpaceName — edited by Person, Mar 16
```

If no results: `CONFLUENCE — No recent activity`
If unavailable: `CONFLUENCE — Unavailable`

### 5. Calendar

<!-- SYNC NOTE: These calendar instructions are duplicated in setup/commands/calendar.md. If you change them here, update there too. -->

Detect local timezone dynamically via PowerShell: `$tz = [System.TimeZoneInfo]::Local; $now = [datetime]::Now; "$([int]$tz.GetUtcOffset($now).TotalHours)|$($tz.Id)|$($tz.IsDaylightSavingTime($now))"`. Parse `offset|tzId|isDst`. Map tzId to abbreviation (Eastern→EST/EDT, Central→CST/CDT, Mountain→MST/MDT, Pacific→PST/PDT; else `UTC±N`). Compute today 00:00 and 23:59 local → UTC using detected offset. Call `mcp__claude_ai_yl-msoffice__list_events` with `startDateTime`, `endDateTime`, `top: 20`. Filter out declined events. Sort by start time ascending.

For each event: time in 12-hour format, duration (end − start), location hint (`— Teams` if online meeting, else location name if present).

Output:
```
CALENDAR (N events)

  9:00 AM   Daily Standup                 (30 min)  — Teams
  10:30 AM  Sprint Planning               (1h)
  2:00 PM   1:1 with Heber               (1h)  — Teams
```

If no events: `CALENDAR — No events today`. If call fails: `CALENDAR — Unavailable`.

### 6. Done

Print:
```
---
Setup complete. Have a good day.
```

## Error Handling

If any section fails (MCP auth issue, network error, etc.), print the error under that section header and continue. Never let one failure block the full briefing.
