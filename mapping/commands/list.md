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

4. **Display** (group by command, skip commands with no phrases):

```
/story:dashboard — Show open Jira stories with current status
  - show my stories
  - what's going on with my tickets
  - updated status  [user]

/story:create — Create a new Jira story
  - create a story
  - file a ticket

/session:start — Start a working session
  - start my day  [user]
```

5. **If nothing registered** — "No phrases yet. They fill in automatically as you use commands, or add one with `/mapping:add`."
