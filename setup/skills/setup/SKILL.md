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

<!-- SYNC NOTE: Query 1 is duplicated in setup/commands/jira.md, setup/commands/local.md, and jira/commands/my-stories.md.
     If you change it here, update all three. -->

### Open Tickets Query (Query 1 — My tickets)

```jql
assignee = "620147d91fec260068c1097d" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, duedate ASC
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

## Future — Calendar

When implementing `setup:calendar`:
- Use `mcp__claude_ai_Microsoft_365__outlook_calendar_search` for today's calendar
- Format: show time, title, attendees
