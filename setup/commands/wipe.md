---
name: wipe
description: Plugin config teardown — removes user identity config and operational plugin files. Use before uninstalling plugins or handing off a machine. Memory files are never touched.
---

# Setup: Wipe

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

### 4a. Remove the `ccs` launcher from shell profiles (offer separately)

The `ccs` repo launcher (installed by `/setup:onboarding`) lives as a marked block inside
your shell profiles, not as a config file — so it needs its own removal. Check for it:

```bash
for f in "$HOME/.bashrc" "$HOME/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1" "$HOME/Documents/PowerShell/Microsoft.PowerShell_profile.ps1"; do
  [ -f "$f" ] && grep -qF "# >>> ccs launcher" "$f" && echo "$f"
done
```

If any profile contains the block, offer (do not remove silently — these are hand-authored files):
"Also remove the `ccs` launcher from <profile(s)>? (yes/no)"

On **yes**, strip the block between (and including) the sentinels from each profile:
```bash
awk '/# >>> ccs launcher/{skip=1} !skip{print} /# <<< ccs launcher/{skip=0}' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
```
Report each: "Removed the ccs launcher from <profile>." On **no**, leave the profiles untouched.
The profiles themselves are never deleted — only the marked block is removed.

### 4b. Remove the Claude output conventions block (offer separately, acp-ajudd#116)

Same rationale as 4a — this lives as a marked block inside `~/.claude/CLAUDE.md`, a
hand-authored file, not a config file this command otherwise touches. Check for it:

```bash
CLAUDE_MD="$HOME/.claude/CLAUDE.md"
[ -f "$CLAUDE_MD" ] && grep -qF "<!-- begin acp-output-conventions" "$CLAUDE_MD" && echo "$CLAUDE_MD"
```

If present, offer (do not remove silently):
"Also remove the Claude output conventions block from ~/.claude/CLAUDE.md? (yes/no)"

On **yes**, strip the block between (and including) the markers — python, not sed or
PowerShell `Set-Content` (#114), so the block's non-ASCII characters don't corrupt the rest
of the file on the way out:
```bash
python3 - "$CLAUDE_MD" <<'PY'
import sys
path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    content = f.read()
begin, end = '<!-- begin acp-output-conventions', '<!-- end acp-output-conventions -->'
if begin in content:
    start = content.index(begin)
    stop = content.index(end, start) + len(end)
    content = content[:start] + content[stop:]
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
PY
```
Report: "Removed the Claude output conventions block from ~/.claude/CLAUDE.md." On **no**,
leave the file untouched. The file itself is never deleted — only the marked block.

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
