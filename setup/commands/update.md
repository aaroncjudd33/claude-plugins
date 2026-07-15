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

### 5. Re-sync the Claude output conventions block (acp-ajudd#116)

If `~/.claude/CLAUDE.md` already has the block installed (from a prior `/setup:onboarding`),
re-sync it now so content changes shipped in this update reach every dev automatically. If
the block is **not** installed, skip silently — `/setup:update` never installs it for the
first time, only `/setup:onboarding` offers that (explicit-install-only, same rule as `ccs`).

```bash
CLAUDE_MD="$HOME/.claude/CLAUDE.md"
TMPL="$HOME/.claude/plugins/marketplaces/<MARKETPLACE_NAME>/setup/scripts/output-conventions.md"
if [ -f "$CLAUDE_MD" ] && grep -qF "<!-- begin acp-output-conventions" "$CLAUDE_MD"; then
  python3 - "$TMPL" "$CLAUDE_MD" "$HOME/.claude/plugins/user-config.json" <<'PY'
import json, sys
tmpl_path, target_path, config_path = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(config_path, encoding='utf-8') as f:
        default = json.load(f).get('defaults', {}).get('verbosityDefault', 'v1')
except FileNotFoundError:
    default = 'v1'
block = open(tmpl_path, encoding='utf-8').read().replace('__VERBOSITY_DEFAULT__', default)
with open(target_path, encoding='utf-8') as f:
    content = f.read()
begin, end = '<!-- begin acp-output-conventions', '<!-- end acp-output-conventions -->'
start = content.index(begin)
stop = content.index(end, start) + len(end)
content = content[:start] + block.rstrip('\n') + content[stop:]
with open(target_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("re-synced")
PY
fi
```

Same UTF-8-safe python write as onboarding Step 6b — never PowerShell `Set-Content` /
`Get-Content -Raw` on this file (#114). Note the result in the summary: "Output conventions
block: re-synced" or "not installed — skipped" (omit the line if the file plainly doesn't
have `~/.claude/CLAUDE.md` at all).

### 6. Report and prompt restart

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

Output conventions block: re-synced

Restart Claude Code to activate the changes.
```

If any plugins errored (not just "not installed"), list them separately and include the error message.
