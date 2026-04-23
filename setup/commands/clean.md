---
name: clean
description: Full teardown — removes ALL local state created by the plugin system. Use before uninstalling plugins or handing off a machine. This cannot be undone.
---

# Setup: Clean

Removes all local files created by the plugin system — identity config, team registry, session memory, browser links, story settings, and the auto-memory system. After this command, the machine is as if the plugins were never configured.

This does NOT uninstall the plugins themselves — run `claude plugin uninstall <name>` for each plugin separately after cleaning.

## Instructions

### 1. Discover what exists

Check each of the following and note which are present:

| File / Directory | What it contains |
|-----------------|-----------------|
| `~/.claude/plugins/user-config.json` | Your identity — name, email, Jira ID, Teams ID |
| `~/.claude/plugins/team.json` | Team registry — colleague roles and IDs |
| `~/.claude/browser-links.json` | Saved browser links and workspaces |
| `~/.claude/jira-stories.json` | Story visibility and hide settings |
| `~/.claude/memory/sessions/` | All session state files for every project |
| `~/.claude/memory/*.md` | Auto-memory files (user profile, feedback, project notes) |
| `~/.claude/memory/MEMORY.md` | Memory index |

If none of these exist, report: "Nothing to clean — no plugin-created files found." and stop.

### 2. Display what will be deleted

Show a summary of everything found:

```
⚠  The following will be permanently deleted:

  ~/.claude/plugins/user-config.json       (your identity config)
  ~/.claude/plugins/team.json              (team registry)
  ~/.claude/browser-links.json             (browser workspaces and links)
  ~/.claude/jira-stories.json              (story visibility settings)
  ~/.claude/memory/sessions/               (ALL session state — X files)
  ~/.claude/memory/*.md                    (auto-memory files — X files)
  ~/.claude/memory/MEMORY.md              (memory index)

This cannot be undone. Installed plugins and plugin code are not affected.
To also remove the plugins, run: claude plugin uninstall <name> for each one.
```

Only list items that were found — skip anything already absent. For directories, include the file count if easily determinable.

### 3. Confirm — two-step

First ask: "Are you sure you want to delete all of this? (yes/no)"

Do NOT proceed on "y" alone — requires full "yes".

If yes, ask a second time: "This will delete session memory and auto-memory that cannot be recovered. Type YES (all caps) to confirm."

Only proceed if the user types "YES" in all caps. Anything else: "Clean cancelled. Nothing was deleted."

### 4. Delete

Delete each item that exists, in this order:

1. `~/.claude/plugins/user-config.json`
2. `~/.claude/plugins/team.json`
3. `~/.claude/browser-links.json`
4. `~/.claude/jira-stories.json`
5. All files under `~/.claude/memory/sessions/` (and the directory itself if empty after)
6. All `*.md` files directly under `~/.claude/memory/` (including MEMORY.md)

Report each deletion:
- "Deleted ~/.claude/plugins/user-config.json"
- "Deleted ~/.claude/plugins/team.json"
- "Deleted ~/.claude/browser-links.json"
- "Deleted ~/.claude/jira-stories.json"
- "Deleted ~/.claude/memory/sessions/ (X files)"
- "Deleted ~/.claude/memory/ memory files (X files)"

### 5. Final report and next steps

```
Clean complete. All plugin-created local state has been removed.

To also remove the installed plugins:
  claude plugin uninstall setup@ajudd-claude-plugins
  claude plugin uninstall session@ajudd-claude-plugins
  claude plugin uninstall story@ajudd-claude-plugins
  claude plugin uninstall release@ajudd-claude-plugins
  claude plugin uninstall comms@ajudd-claude-plugins
  claude plugin uninstall docs@ajudd-claude-plugins
  claude plugin uninstall e2e@ajudd-claude-plugins
  claude plugin uninstall links@ajudd-claude-plugins

To start fresh (keep plugins installed, just re-configure):
  /setup:onboarding
```

## What is NOT deleted

- `~/.claude/CLAUDE.md` — your global Claude instructions (hand-authored, not plugin-created)
- `~/.claude/settings.json` — Claude Code settings
- `~/.claude/plugins/installed_plugins.json` — plugin registry (managed by Claude CLI)
- `~/.claude/plugins/cache/` — installed plugin files (managed by Claude CLI)
- `~/.claude/plugins/marketplaces/` — marketplace clones (managed by Claude CLI)
- `~/.claude/scripts/` — utility scripts (hand-authored)
- `~/.claude/aws-first-deploy.md` — hand-authored reference notes
