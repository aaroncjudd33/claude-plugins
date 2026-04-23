---
name: update
description: Update all installed plugins from the marketplace in one command. Run whenever the plugin repo changes, then restart Claude Code.
allowed-tools: [Bash, Read]
---

# Setup: Update

Pull the latest changes from the plugin marketplace and update all installed plugins in one shot. Run this whenever Aaron pushes changes — no need to run individual update commands per plugin.

## Instructions

### 1. Read config

Read `~/.claude/plugins/user-config.json` and extract `paths.pluginMarketplaceName`. Use as `MARKETPLACE_NAME`.

### 2. Update the marketplace

Run:

```bash
claude plugin marketplace update <MARKETPLACE_NAME>
```

If this fails or produces an error, fall back to a direct git pull:

```bash
cd ~/.claude/plugins/marketplaces/<MARKETPLACE_NAME> && git pull
```

Note the result: "Marketplace updated" or "Marketplace pulled via git (fallback)".

### 3. Get the plugin list

Read `~/.claude/plugins/marketplaces/<MARKETPLACE_NAME>/.claude-plugin/marketplace.json` and extract all plugin names from the `plugins` array.

### 4. Update each plugin

For each plugin name, run:

```bash
claude plugin update <plugin-name>@<MARKETPLACE_NAME>
```

Run sequentially. If one returns "not installed" or similar, note it and continue — it's fine to have a subset of plugins installed. Only surface actual errors.

### 5. Report and prompt restart

Display a summary of what was updated:

```
Update complete.

  Marketplace:  pulled latest
  Plugins:
    ✓ story
    ✓ session
    ✓ setup
    ✓ release
    ✓ comms
    ✓ docs
    ✓ links
    ✓ e2e

Restart Claude Code to activate the changes.
```

If any plugins errored (not just "not installed"), list them separately and include the error message.
