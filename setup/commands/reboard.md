---
name: reboard
description: Wipe plugin configuration files (user-config.json and team.json) and start fresh. Run if onboarding went wrong, you're handing off a machine, or you just want a clean slate.
---

# Setup: Reboard

Deletes the locally-created plugin configuration files and returns the system to a pre-onboarding state. Does NOT touch session memory files, browser-links.json, or MEMORY.md — only the files that `/setup:onboarding` creates.

For a full wipe of all plugin-created state, use `/setup:clean`.

## Instructions

### 1. Discover what exists

Check for these files:

- `~/.claude/plugins/user-config.json`
- `~/.claude/plugins/team.json`

For each file found, note its existence. If neither file exists, report: "Nothing to reboard — plugin config files do not exist. Run /setup:onboarding to get started." and stop.

### 2. Display what will be deleted

Show the user exactly what will be removed:

```
The following plugin configuration files will be permanently deleted:

  ~/.claude/plugins/user-config.json   — your identity (name, email, Jira ID, Teams ID)
  ~/.claude/plugins/team.json          — team registry (colleague roles and IDs)

These files were created by /setup:onboarding and contain no code — only your
personal configuration. Nothing else will be touched.

After reboarding, run /setup:onboarding to configure fresh.
```

Only list files that actually exist — skip any that are already absent.

### 3. Confirm

Ask: "Delete these files and reboard? (yes/no)"

Do NOT proceed unless the user types "yes" (full word). "y" alone is not sufficient — this is a destructive action.

### 4. Delete

For each file that exists, delete it.

Report each deletion as it happens:
- "Deleted ~/.claude/plugins/user-config.json"
- "Deleted ~/.claude/plugins/team.json"

### 5. Confirm and next step

```
Reboard complete. Plugin configuration has been cleared.

Run /setup:onboarding to set up fresh.
```

## What is NOT reboarded

To be explicit — these are NOT touched by this command:

- `~/.claude/memory/` — session state, notes, MEMORY.md
- `~/.claude/browser-links.json` — saved browser links and workspaces
- `~/.claude/jira-stories.json` — story visibility settings
- Any session files under `~/.claude/memory/sessions/`
- Any files in the plugin marketplace or install cache

For a full wipe of all plugin-created state, use `/setup:clean`.
