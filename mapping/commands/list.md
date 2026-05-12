---
allowed-tools: Read
description: Show all registered phrases for one command or all commands
---

Show the phrase registry — shipped defaults and your personal additions.

## Steps

1. **Determine scope** — if a command or plugin prefix was specified as an argument (e.g., `/mapping:list story` or `/mapping:list /story:dashboard`), filter to that. Otherwise show everything.

2. **Read config** — get `paths.pluginMarketplaceName` from `~/.claude/plugins/user-config.json`.

3. **Read both files:**
   - Shipped: `~/.claude/plugins/marketplaces/<name>/mapping/.claude-plugin/phrases.json`
   - User: `~/.claude/plugins/phrases.json`
   - Merge them. Mark user-added phrases with `[user]`.
   - Skip the `_config` key — it's not a command entry.

4. **Get cleanup threshold** — read `_config.cleanup_threshold_days` from `~/.claude/plugins/phrases.json`. Default: 14.

5. **Display** (group by command, skip commands with no phrases). For each command show its `last_used` date and flag stale entries:
   - **Stale:** no `last_used` field, OR days since `last_used` > threshold — append `⚠ never used` or `⚠ unused 30d`
   - **Recent:** used within threshold — append `(last used: YYYY-MM-DD)`

```
/story:dashboard — Show open Jira stories with current status  (last used: 2026-05-10)
  - show my stories  [user]
  - story dashboard  [user]

/release:deploy — Execute a production deployment  ⚠ never used
  - deploy to prod  [user]
  - deploy it  [user]

/session:start — Start a working session  (last used: 2026-05-12)
  - start my day  [user]
```

   If any entries are stale, append at the end:
   `X entries unused for 14+ days — run /mapping:cleanup to review them.`

6. **If nothing registered** — "No phrases yet. They fill in automatically as you use commands, or add one with `/mapping:add`."
