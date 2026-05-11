---
allowed-tools: Read
description: Show all registered phrases — shipped defaults and user additions — for one plugin or all plugins
---

Show the phrase registry. Displays both plugin-shipped defaults and user-local additions.

## Steps

1. **Determine scope** — if the user specified a plugin name as an argument (e.g., `/mapping:list story`), filter to that plugin. Otherwise show all installed plugins.

2. **Read config** — get `paths.pluginMarketplaceName` from `~/.claude/plugins/user-config.json`.

3. **Read marketplace.json** — `~/.claude/plugins/marketplaces/<name>/.claude-plugin/marketplace.json` → list of plugins. Filter if scoped.

4. **For each plugin in scope:**
   - Read `~/.claude/plugins/marketplaces/<name>/<plugin>/.claude-plugin/phrases.json` → shipped defaults
   - Read `~/.claude/plugins/phrases/<plugin>.json` → user additions
   - Merge: user additions override shipped defaults for the same command key; additional phrases from user file are appended

5. **Display** (skip plugins with no phrases at all):

```
story
  /story:dashboard — Show open Jira stories with current status
    - show my stories
    - what's going on with my tickets
    - check my tickets  [user]

  /story:create — Create a new Jira story
    - create a story
    - file a ticket

mapping
  /mapping:add — Register a phrase to a command
    - add a phrase
    - remember that for next time
```

Mark user-local phrases with `[user]`. Shipped defaults have no marker.

6. **If no phrases found** — "No phrases registered yet. Run `/mapping:add` to add one, or use a command and I'll offer to add the phrase when I can't recognize it."
