# Daily Prep Skill

Reference data and formatting rules for the morning setup routine.

---

## Atlassian Connection

- Instance: `https://younglivingeo.atlassian.net`
- Cloud ID: `9de6eb2b-2683-44e6-89ff-c622027e09b4`
- Auth: Handled by the `claude.ai` Atlassian MCP
- Aaron Judd Account ID: `620147d91fec260068c1097d`

---

## Jira

### Open Tickets Query

```jql
assignee = "620147d91fec260068c1097d" AND status not in (Done, Closed, Cancelled, Resolved) ORDER BY status ASC, duedate ASC
```

### Status Grouping Order

Display in this order (skip groups with zero tickets):
1. In Progress
2. Ready For Test / In Review / In QA
3. Open / To Do / Backlog
4. Any other statuses

### Flagging Rules

- `DUE TODAY` — duedate equals today
- `OVERDUE` — duedate is before today (show the date)
- No flag if duedate is null or in the future

---

## Confluence

### Recently Modified Pages Query

```cql
watcher = "620147d91fec260068c1097d" AND lastmodified > now("-7d") ORDER BY lastmodified DESC
```

Also search:
```cql
mention = "620147d91fec260068c1097d" AND lastmodified > now("-7d") ORDER BY lastmodified DESC
```

Deduplicate results by page ID. Show max 10 pages.

---

## Git Repos

### Scan Paths

- `C:\dev\*` — work repos
- `C:\claude\*` — personal/side projects

### What to Check

For each immediate subdirectory that contains a `.git` folder:
1. **Uncommitted changes**: `git status --porcelain` (count lines)
2. **Unpushed commits**: `git log @{u}..HEAD --oneline 2>/dev/null` (count lines; ignore if no upstream)
3. **Current branch**: `git branch --show-current`

Skip directories that are not git repos. Do not recurse into subdirectories.

---

## AWS

### SSO Login

```bash
aws sso login
```

This opens a browser for SSO authentication. Run first — CodeArtifact logins depend on it.

### CodeArtifact Logins

After SSO login succeeds, run both:

```bash
aws --profile devops codeartifact login --tool dotnet --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```

```bash
aws --profile devops codeartifact login --tool npm --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```

### Session Check

After login, verify with:
```bash
aws sts get-caller-identity
```

If this succeeds, the session is active. Parse the cached SSO token from `~/.aws/sso/cache/*.json` to report expiry time.

---

## Output Format

Plain text, no markdown rendering. Follows the user's business summary style:
- Date header at top with `===` underline
- ALL CAPS section labels with a blank line before each
- Bullet points with dashes
- Indented details under each item
- Concise — entire briefing should be readable in under 60 seconds

---

## Future Sections (Hooks)

These sections are not yet implemented. Show them as stubs at the end of the briefing:

- **OUTLOOK** — unread email summary via Microsoft 365 MCP (read_resource for inbox)
- **CALENDAR** — today's meetings via Microsoft 365 MCP (outlook_calendar_search)

When implementing these later:
- Use `mcp__claude_ai_Microsoft_365__outlook_email_search` for unread emails from today
- Use `mcp__claude_ai_Microsoft_365__outlook_calendar_search` for today's calendar
- Format: show time, title, attendees for meetings; sender + subject for emails
