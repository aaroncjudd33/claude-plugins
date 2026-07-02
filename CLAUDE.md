# ajudd-claude-plugins — Authoring Conventions

Instructions for working *inside* this marketplace repo. (Aaron's personal global
plugin notes — install/update/rename mechanics, team data, etc. — live in
`~/.claude/CLAUDE.md`. This file is about how the plugins themselves are built.)

## Core principle: plugins must "install and just work"

These plugins are meant for other developers (Nivi, contractors), not just Aaron.
A teammate must be able to run `claude plugin install <plugin>@ajudd-claude-plugins`
and have it **fully work with no additional per-machine steps** — no hand-editing
`~/.claude/settings.json`, no seeding memories, no tribal-knowledge setup. Anything
that only exists on the author's machine means the plugin does **not** actually work
for anyone else.

Three rules follow from this. Apply them to **every** plugin, not just the one you're editing:

1. **Behavior ships IN the plugin.** Hooks, skills, commands, lint scripts, reference
   docs — all live under the plugin directory and are portable by definition. A
   plugin-shipped hook (`<plugin>/hooks/hooks.json`, auto-discovered — no `hooks` key
   in `plugin.json`) is active only when the plugin is enabled, which is exactly the
   "only enforce when loaded" behavior we want. Reference bundled files with
   `${CLAUDE_PLUGIN_ROOT}`, never absolute paths.

2. **Per-user identity goes through an explicit setup command** — never assumed, never
   hidden. `/setup:onboarding` → `~/.claude/plugins/user-config.json` is the sanctioned
   pattern: discoverable and repeatable. Prefer a *little more explicit config* over
   silent dependence on personal local state.

3. **Global memory is NEVER load-bearing.** `~/.claude/memory/*` is personal,
   non-portable, and invisible to teammates. Fine for Aaron's preferences; it must
   **never** gate how a plugin functions. If a plugin needs a fact to work, ship the
   fact in the plugin or read it from `user-config.json`.

**Declare cross-plugin / MCP dependencies explicitly.** If a plugin needs another
plugin or an MCP server that isn't installed alongside it (e.g. comms depends on
`yl-msoffice@youngliving-claude-plugins`, a *different* marketplace), document it as a
required prerequisite in the plugin's README/SKILL and add a runtime self-check that
points the user at the fix instead of failing silently. Close every hidden step.

## Hook conventions (precedent: the `session` plugin)

- Layout: `<plugin>/hooks/hooks.json` + `<plugin>/hooks/scripts/*.py`.
- No `hooks` key in `plugin.json` — hooks are auto-discovered.
- Matchers are regex against the tool name. For MCP tools, **match on the tool-name
  suffix** (`send_chat_message`, `execute_action`) rather than a hardcoded namespace,
  so an MCP rehost (`mcp__claude_ai_*` → `mcp__plugin_*_*`) can't silently disable the
  hook. Enumerate/anchor deliberately and comment the fragility.
- **Fail-open:** any parse error exits 0. An enforcement bug must never wedge normal
  work. Keep printed messages ASCII-only (Windows `python` fallback stdout may be
  cp1252 — a non-ASCII char raises `UnicodeEncodeError` and crashes the hook).
- Preserve the `python3 → python` fallback in hook commands for Windows.
