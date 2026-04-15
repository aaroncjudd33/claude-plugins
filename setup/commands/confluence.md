---
name: confluence
description: Confluence activity — pages you watch or are mentioned in, modified in the last 7 days.
---

# Setup: Confluence

Show recently modified Confluence pages you're watching or mentioned in.

## Instructions

Run two CQL searches in parallel using `searchConfluenceUsingCql`:

1. `watcher = "620147d91fec260068c1097d" AND lastmodified > now("-7d") ORDER BY lastmodified DESC`
2. `mention = "620147d91fec260068c1097d" AND lastmodified > now("-7d") ORDER BY lastmodified DESC`

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
