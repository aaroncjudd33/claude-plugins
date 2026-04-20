---
name: setup
description: Use this skill when the user wants to start their day, run morning setup, log into AWS, refresh CodeArtifact credentials, check open Jira tickets, check Confluence activity, or see today's calendar. Trigger phrases include "start my day", "morning setup", "setup:local", "log into AWS", "refresh credentials", "check my Jira tickets", "what do I have today", or "show my open tickets".
---

# Setup Skill

Reference data and formatting rules for the morning setup routine.

---

## Atlassian Connection

- Instance: `https://younglivingeo.atlassian.net`
- Cloud ID: `9de6eb2b-2683-44e6-89ff-c622027e09b4`
- Auth: Handled by the `claude.ai` Atlassian MCP
- Aaron Judd Account ID: `620147d91fec260068c1097d`

---

## Jira

<!-- SYNC NOTE: These 3 JQL queries are duplicated in setup/commands/jira.md, setup/commands/local.md, story/commands/my-stories.md, and this file.
     CANONICAL SOURCE: story/skills/story/SKILL.md — update there first, then sync all four. -->

### Query 1 — Currently assigned to me

```jql
assignee = "620147d91fec260068c1097d" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, duedate ASC
```

### Query 2 — Previously assigned to me (reassigned to someone else)

```jql
project = BPT2 AND assignee WAS "620147d91fec260068c1097d" AND assignee != "620147d91fec260068c1097d" AND assignee is not EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

### Query 3 — Previously assigned to me (now unassigned)

```jql
project = BPT2 AND assignee WAS "620147d91fec260068c1097d" AND assignee is EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

### Status Grouping Order

Display in this order (skip groups with zero tickets):
1. In Progress
2. Ready For Test / In Review / In QA
3. Open / To Do / Backlog
4. Any other statuses

### Flagging Rules

- `DUE TODAY` — duedate equals today
- `OVERDUE (YYYY-MM-DD)` — duedate is before today (always show the date)
- No flag if duedate is null or in the future

---

## Confluence

### Recently Modified Pages Queries

```cql
watcher = "620147d91fec260068c1097d" AND lastmodified > now("-7d") ORDER BY lastmodified DESC
```

```cql
mention = "620147d91fec260068c1097d" AND lastmodified > now("-7d") ORDER BY lastmodified DESC
```

Deduplicate results by page ID. Show max 10 pages. Use relative dates: "today", "yesterday", "2 days ago", or the date if older.

---

## AWS

### SSO Check and Login

```bash
aws sts get-caller-identity 2>/dev/null
```

Run this first. If it fails, run `aws sso login` (opens browser, blocks until complete). Parse `~/.aws/sso/cache/*.json` for expiry — warn if < 2 hours remaining.

### CodeArtifact Logins

Run both in parallel after SSO is confirmed:

```bash
aws --profile devops codeartifact login --tool dotnet --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```

```bash
aws --profile devops codeartifact login --tool npm --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```

---

## Output Format

Plain text, no markdown rendering:
- Date header at top with `===` underline
- ALL CAPS section labels with a blank line before each
- Bullet points with dashes
- Indented details under each item
- Concise — entire briefing readable in under 60 seconds

---

## Error Handling

If any section fails (MCP auth issue, network error, etc.), print the error under that section header and continue. Never let one failure block the full briefing.

---

## Calendar

<!-- SYNC NOTE: Mirrors setup/commands/calendar.md. Update both together. -->

Tool: `mcp__claude_ai_yl-msoffice__list_events`

Date range: today 00:00–23:59 local time in UTC. Mountain Time — MDT (UTC-6) April–October, MST (UTC-7) otherwise.

Parameters: `startDateTime`, `endDateTime` (ISO 8601 UTC), `top: 20`.

Post-processing:
- Filter out events where response status is `declined`
- Sort by start time ascending
- Duration = end − start; format as `(30 min)`, `(1h)`, `(1h 30m)`
- Location hint: `— Teams` if `isOnlineMeeting` or Teams join URL present; else location name if non-empty

Output format:
```
CALENDAR (N events)

  9:00 AM   Daily Standup                 (30 min)  — Teams
  10:30 AM  Sprint Planning               (1h)
```

No events → `CALENDAR — No events today`. Failure → `CALENDAR — Unavailable`.
