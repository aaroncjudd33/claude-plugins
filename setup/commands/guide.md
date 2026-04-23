---
name: guide
description: Capability reference for all installed plugins. Run alone for an overview, or /setup:guide <plugin-name> for a deep dive on a specific plugin.
allowed-tools: [Read, Glob]
---

# Setup: Guide

Show what the installed plugins can do and how to use them. Reads directly from plugin source files so the reference is always accurate and reflects the current version.

## Instructions

### 1. Determine mode

Check whether the user provided a plugin name after the command (e.g. `/setup:guide story`).

- **No argument** → run **overview mode** (step 3)
- **Plugin name provided** → run **detail mode** for that plugin (step 4)

### 2. Resolve marketplace path

Read `~/.claude/plugins/user-config.json` and extract `paths.pluginMarketplaceName`. Use as `MARKETPLACE_NAME`.

Base path: `~/.claude/plugins/marketplaces/<MARKETPLACE_NAME>/`

### 3. Overview mode

Read `~/.claude/plugins/marketplaces/<MARKETPLACE_NAME>/.claude-plugin/marketplace.json` to get the plugin list.

For each plugin, read its `.claude-plugin/plugin.json` to get the description.

Display:

```
Installed Plugins

  setup     Morning dashboard — onboarding, AWS login, Jira briefing, calendar
  story     BPT2 story management — create, view, update, comment
  session   Session lifecycle — start, checkpoint, commit, finish
  release   Production deployments — CAB cards, release branches, deploy execution
  comms     Microsoft 365 — Teams messaging and email triage
  docs      Confluence documentation — init, update, propose, archive
  links     Browser navigation — named links and workspace management
  e2e       Playwright browser — persistent test browser with SSO auto-login

─────────────────────────────────────────────────────────────

Daily Workflow

  Start of day:    /session:start  →  /setup:local
  Working a story: /story:dashboard  →  /story:create  →  /session:checkpoint  →  /session:commit
  Shipping it:     /release:create  →  /release:deploy  →  /session:finish
  Stay current:    /setup:update  →  restart Claude Code

─────────────────────────────────────────────────────────────

For full details on any plugin: /setup:guide <plugin-name>
Example: /setup:guide story
```

### 4. Detail mode

Read the following for the named plugin:

1. `~/.claude/plugins/marketplaces/<MARKETPLACE_NAME>/<plugin>/.claude-plugin/plugin.json` — description and command paths
2. `~/.claude/plugins/marketplaces/<MARKETPLACE_NAME>/<plugin>/skills/<plugin>/SKILL.md` — background context, design intent, key behaviors
3. Each command file listed in the plugin's `commands` array — read the full content of each

Generate a descriptive breakdown covering:

- **What it does** — plain language, focus on what problem it solves and when you'd reach for it
- **Commands** — for each command: name, what it does, when to use it, any important args or prerequisites
- **How it connects** — dependencies on other plugins or external tools (MCP, GitHub, AWS) noted in the SKILL.md
- **Gotchas** — anything non-obvious from the skill or command files worth calling out

Format clearly with sections. Keep each command description to 2–3 sentences — enough to know when to use it, not a full tutorial.

End with: "For anything not covered here, ask directly — I can read the source files and answer specific questions."
