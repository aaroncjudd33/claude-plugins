---
name: confluence
description: Confluence activity — pages you watch or are mentioned in, modified in the last 7 days.
---

# Setup: Confluence

Show recently modified Confluence pages you're watching or mentioned in.

## Instructions

### Read User Config

Read `~/.claude/plugins/user-config.json` and extract `user.jiraAccountId` — this is `{ACCOUNT_ID}` used in the CQL queries below.

If the file does not exist or `jiraAccountId` is empty, stop and say: "Your identity is not configured. Run `/setup:onboarding` first."

Run two CQL searches in parallel using `searchConfluenceUsingCql`:

1. `watcher = "{ACCOUNT_ID}" AND lastmodified > now("-7d") ORDER BY lastmodified DESC`
2. `mention = "{ACCOUNT_ID}" AND lastmodified > now("-7d") ORDER BY lastmodified DESC`

Deduplicate by page ID. Show max 10 results, most recent first.

Use relative dates: "today", "yesterday", "2 days ago", or the date if older.

**Output:**
```
CONFLUENCE (N recently modified)

  - "Page Title" in SpaceName — edited by Person, yesterday
  - "Another Page" in SpaceName — edited by Person, Mar 16
```

If no results: `CONFLUENCE — No recent activity`
If Atlassian MCP is unavailable: `CONFLUENCE — Unavailable`
