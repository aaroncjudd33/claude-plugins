---
name: clean
description: Plugin config teardown — removes user identity config and operational plugin files. Use before uninstalling plugins or handing off a machine. Memory files are never touched.
---

# Setup: Clean

Removes plugin configuration files created by the plugin system — identity config, team registry, browser links, and story settings. After this command, the plugins are deconfigured and ready for a fresh `/setup:onboarding` run or uninstall.

**Session and memory files are never deleted — by this command or any other.** This is a hard rule: Claude will not delete `~/.claude/memory/sessions/` or any file under it, under any circumstances, even if explicitly asked. Session state, plugin session files, and worklog entries represent your work history. If you want to delete them, do it yourself from the file system.

This does NOT uninstall the plugins themselves — run `claude plugin uninstall <name>` for each plugin separately after cleaning.

## Instructions

### 1. Discover what exists

Check each of the following and note which are present:

| File / Directory | What it contains |
|-----------------|-----------------|
| `~/.claude/plugins/user-config.json` | Your identity — name, email, Jira ID, Teams ID |
| `~/.claude/plugins/team.json` | Team registry — colleague roles and IDs |
| `~/.claude/plugins/phrases.json` | Phrase registry — natural language → command mappings |
| `~/.claude/browser-links.json` | Saved browser links and workspaces |
| `~/.claude/jira-stories.json` | Story visibility and hide settings |

If none of these exist, report: "Nothing to clean — no plugin config files found." and stop.

### 2. Display what will be deleted

Show a summary of everything found:

```
⚠  The following plugin config files will be permanently deleted:

  ~/.claude/plugins/user-config.json       (your identity config)
  ~/.claude/plugins/team.json              (team registry)
  ~/.claude/plugins/phrases.json           (phrase → command registry)
  ~/.claude/browser-links.json             (browser workspaces and links)
  ~/.claude/jira-stories.json              (story visibility settings)

Memory files (~/.claude/memory/) are NOT touched — your project history and
session state are preserved. Delete those manually if you need to remove them.

Installed plugins and plugin code are not affected.
To also remove the plugins, run: claude plugin uninstall <name> for each one.
```

Only list items that were found — skip anything already absent.

### 3. Confirm — two-step

First ask: "Are you sure you want to delete these plugin config files? (yes/no)"

Do NOT proceed on "y" alone — requires full "yes".

If yes, ask a second time: "Type YES (all caps) to confirm."

Only proceed if the user types "YES" in all caps. Anything else: "Clean cancelled. Nothing was deleted."

### 4. Delete

Delete each item that exists, in this order:

1. `~/.claude/plugins/user-config.json`
2. `~/.claude/plugins/team.json`
3. `~/.claude/plugins/phrases.json`
4. `~/.claude/browser-links.json`
5. `~/.claude/jira-stories.json`

Report each deletion:
- "Deleted ~/.claude/plugins/user-config.json"
- "Deleted ~/.claude/plugins/team.json"
- "Deleted ~/.claude/plugins/phrases.json"
- "Deleted ~/.claude/browser-links.json"
- "Deleted ~/.claude/jira-stories.json"

### 5. Final report and next steps

```
Clean complete. Plugin configuration files have been removed.

Memory files were preserved — your project history and session state are intact.

To also remove the installed plugins:
  claude plugin uninstall setup@ajudd-claude-plugins
  claude plugin uninstall session@ajudd-claude-plugins
  claude plugin uninstall story@ajudd-claude-plugins
  claude plugin uninstall release@ajudd-claude-plugins
  claude plugin uninstall comms@ajudd-claude-plugins
  claude plugin uninstall docs@ajudd-claude-plugins
  claude plugin uninstall e2e@ajudd-claude-plugins
  claude plugin uninstall links@ajudd-claude-plugins
  claude plugin uninstall mapping@ajudd-claude-plugins

To start fresh (keep plugins installed, just re-configure):
  /setup:onboarding
```

## What is NOT deleted

**Hard rule — never deleted by Claude under any circumstances:**
- `~/.claude/memory/sessions/` — ALL session files. Story sessions, plugin sessions, worklogs, inbox files, archive files. Claude will not delete these even with explicit permission. If you want them gone, delete from the file system yourself.
- `~/.claude/memory/` (all other memory) — auto-memory, MEMORY.md, project context. Same rule applies.

**Not deleted by this command (managed by other tools or hand-authored):**
- `~/.claude/CLAUDE.md` — your global Claude instructions
- `~/.claude/settings.json` — Claude Code settings
- `~/.claude/plugins/installed_plugins.json` — plugin registry (managed by Claude CLI)
- `~/.claude/plugins/cache/` — installed plugin files (managed by Claude CLI)
- `~/.claude/plugins/marketplaces/` — marketplace clones (managed by Claude CLI)
- `~/.claude/scripts/` — utility scripts (hand-authored)
- `~/.claude/aws-first-deploy.md` — hand-authored reference notes
