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

4. **Get cleanup threshold** — read `_config.cleanup_threshold_days` from `~/.claude/plugins/phrases.json`. Default: 45.

5. **Display** (group by command, skip commands with no phrases). For each phrase object show its status inline based on `touched`:
   - **Stale phrase:** `touched` is absent or days since `touched` > threshold — show `⚠ stale (Xd)` or `⚠ never tracked`
   - **Recent phrase:** `touched` within threshold — show `(touched: YYYY-MM-DD)`
   - Show `last_used` separately when present: `last used: YYYY-MM-DD`
   - Mark user-added phrases with `[user]` (anything in the user registry file)

```
/story:dashboard — Show open Jira stories with current status
  - show my stories        (touched: 2026-05-11, last used: 2026-05-11)  [user]
  - story dashboard        (touched: 2026-05-11)  [user]
  - what changed in jira   ⚠ never tracked  [user]

/release:deploy — Execute a production deployment
  - deploy to prod         ⚠ stale (47d)  [user]
  - deploy it              (touched: 2026-05-10, last used: 2026-05-10)  [user]
```

   If any phrases are stale, append at the end:
   `X phrases stale (untouched [threshold]+ days) across Y commands — run /mapping:cleanup to review.`

6. **If nothing registered** — "No phrases yet. They fill in automatically as you use commands, or add one with `/mapping:add`."
