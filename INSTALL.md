# Install Guide — ajudd-claude-plugins

Personal Claude Code plugin suite for developer workflow automation. Covers Jira story management, production releases, Teams/email communication, Confluence docs, session lifecycle, and morning setup.

---

## Prerequisites

### Required for all plugins

- **Claude Code** — CLI or desktop app installed and authenticated
- **claude.ai Atlassian MCP** — needed by `story`, `setup`, `release`, `docs`. Configure in Claude Code settings under MCP servers.

### Required for Teams + email features

- **yl-msoffice MCP** — needed by `session`, `comms`, `setup` (calendar section). This is a Young Living-specific MCP server — teams/email features won't work without it.

### Required for AWS + CodeArtifact features

- **AWS CLI** with SSO profile configured — needed by `setup` (AWS section). Young Living-specific.

### Required for browser automation

- **Microsoft Edge** — needed by the `links` plugin. Windows only.

---

## Install

### 1. Add the marketplace

```bash
claude plugin marketplace add https://github.com/aaroncjudd33/claude-plugins.git ajudd-claude-plugins
```

### 2. Install plugins

Install all at once, or pick only what you need (see the plugin table below):

```bash
claude plugin install story@ajudd-claude-plugins
claude plugin install session@ajudd-claude-plugins
claude plugin install setup@ajudd-claude-plugins
claude plugin install release@ajudd-claude-plugins
claude plugin install comms@ajudd-claude-plugins
claude plugin install docs@ajudd-claude-plugins
claude plugin install links@ajudd-claude-plugins
claude plugin install e2e@ajudd-claude-plugins
```

### 3. Restart Claude Code

Plugin commands are registered at startup — a restart is required after install.

---

## First Run

### Run onboarding before anything else

```
/setup:onboarding
```

This collects your name, email, Jira account ID, and Teams user ID, then writes `~/.claude/plugins/user-config.json`. Commands across all plugins read identity from this file. Without it, Jira queries and Teams messages will fail or use incorrect values.

The onboarding command will offer to look up your Jira account ID and Teams user ID from your email address — you don't need to know them in advance.

### First commands to try

```
/story:dashboard        — see your open Jira stories
/session:start          — start a working session
/setup:local            — morning briefing (Jira + Confluence + calendar + AWS)
```

---

## Plugin Reference

| Plugin | Commands | Requires | Notes |
|--------|----------|----------|-------|
| `story` | `/story:create`, `/story:dashboard`, `/story:workspace`, `/story:comment`, `/story:update`, `/story:ready` | Atlassian MCP | Jira story lifecycle — BPT2 project |
| `session` | `/session:start`, `/session:checkpoint`, `/session:commit`, `/session:finish`, `/session:worklog`, `/session:switch` | yl-msoffice MCP | Session state across projects. Teams messages are optional. |
| `setup` | `/setup:onboarding`, `/setup:local`, `/setup:jira`, `/setup:confluence`, `/setup:calendar`, `/setup:aws` | Atlassian MCP, yl-msoffice MCP, AWS CLI | Morning dashboard. AWS section requires YL SSO. |
| `release` | `/release:create`, `/release:cab-card`, `/release:cab-branch`, `/release:cab-link`, `/release:cab-review`, `/release:update`, `/release:deploy` | Atlassian MCP, `story`, `session` | Production CAB release workflow — YL-specific |
| `comms` | `/comms:message`, `/comms:fetch`, `/comms:triage`, `/comms:sweep` | yl-msoffice MCP | Teams messaging + email triage |
| `docs` | `/docs:init`, `/docs:update`, `/docs:archive`, `/docs:propose` | Atlassian MCP | Confluence project documentation |
| `links` | `/links:open`, `/links:search`, `/links:link`, `/links:workspace`, `/links:prefix`, `/links:delete` | Edge browser | Named link registry + workspace management. Windows only. |
| `e2e` | `/e2e:start`, `/e2e:stop` | Playwright | Persistent browser session with SSO auth |

### Dependencies

- `release` requires `story` and `session` — install all three together
- `setup` works best with `story` installed (Jira section reuses story skill context)
- `session`, `comms`, `docs`, `links`, `e2e` are standalone

---

## Updating

```bash
# Pull latest from the repo
claude plugin marketplace update ajudd-claude-plugins

# Update a specific plugin
claude plugin update story@ajudd-claude-plugins

# If marketplace update fails silently (known issue on Windows), pull manually:
cd ~/.claude/plugins/marketplaces/ajudd-claude-plugins && git pull
# Then reinstall the affected plugin:
claude plugin uninstall story
claude plugin install story@ajudd-claude-plugins
```

---

## What's YL-Specific

These things are wired for Young Living and will need adaptation for other organizations:

- Jira project key (`BPT2`) and field IDs — configurable via `/setup:onboarding`
- CAB card workflow (`release` plugin) — specific to YL's Change Advisory Board process
- yl-msoffice MCP server — YL's Teams/Outlook integration
- AWS SSO profile names (`devops`, `bp-sandbox`) in `setup:aws`
- Atlassian cloud ID — set in `user-config.json` during onboarding (defaults to YL's instance)
