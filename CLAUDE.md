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

## Version bump levels (SemVer discipline)

Every plugin carries a `version` in its `.claude-plugin/plugin.json`, and a plugin
**deploys on `finish`** — the version bump + push + reinstall *is* the deploy (see the
`session` plugin's finish flow). Every plugin's `finish` references these tiers; pick the
level by **what changed**, and **hold the bump until the work is done** (one bump per
shipped unit of work):

- **PATCH** (`x.y.Z`) — **doc-only / doc-pointer / prose / typo**, plus bug fixes and
  any change that does not add or alter commands or behavior. **A documentation change
  is a PATCH** — this is the default and by far the most common case. A one-line
  doc-pointer edit is a PATCH, **never** a MINOR.
- **MINOR** (`x.Y.0`) — a **new command, or a new user-facing feature / capability**
  added to an existing plugin.
- **MAJOR** (`X.0.0`) — a **redesign**, a breaking change to existing command behavior,
  or a model / architecture change.

**Refinement discipline — spec the level, don't default to MINOR.** When a work item or
handoff is **doc-only**, it must **explicitly spec PATCH**. Defaulting a doc-only change
to MINOR is exactly the mistake this guidance exists to prevent: acp-ajudd#58 shipped a
doc-pointer one-liner as a MINOR bump (`2.4.2 → 2.5.0`) when it should have been a PATCH
(`→ 2.4.3`). The `finish` deploy consults these tiers, so getting the level right at
refinement time keeps the deployed version number honest. (acp-ajudd#61)

## Hook conventions (precedent: the `session` plugin)

- Layout: `<plugin>/hooks/hooks.json` + `<plugin>/hooks/scripts/*.py`.
- No `hooks` key in `plugin.json` — hooks are auto-discovered.
- Matchers are regex against the tool name. For MCP tools, **match on the tool-name
  suffix** (`send_chat_message`, `execute_action`) rather than a hardcoded namespace,
  so an MCP rehost (`mcp__claude_ai_*` → `mcp__plugin_*_*`) can't silently disable the
  hook. Enumerate/anchor deliberately and comment the fragility.
- **Fail-open:** any parse error exits 0. An enforcement bug must never wedge normal
  work. Keep printed messages ASCII-only (Windows `python` fallback stdout may be
  cp1252 — a non-ASCII char raises `UnicodeEncodeError` and crashes the hook). **The
  same cp1252 hazard bites file *writes*, not just stdout:** PS 5.1 `Get-Content -Raw`
  reads a BOM-less UTF-8 file as cp1252 and `Set-Content -Encoding UTF8` writes it back
  double-encoded + adds a BOM — silently mojibaking every `·` / `—` / `→` in a
  session/inbox/archive file (observed live corrupting `_inbox/*.md`, acp-ajudd#114).
  So **edit session/inbox/archive files only with UTF-8-safe I/O** — the Read/Edit
  tools, Python `open(..., encoding='utf-8')`, or bash — **never** PS 5.1 `Set-Content`
  / `Get-Content -Raw` round-trips. If PowerShell must touch them, use
  `[System.IO.File]::ReadAllText` / `WriteAllText` with an explicit UTF-8 (no-BOM)
  encoding, not the 5.1 cmdlets. `session-list.py` carries a detect-and-warn backstop
  (auto-strips a lone BOM, flags mojibake for manual repair) — but the discipline is
  the fix; the guard only catches what slips. (acp-ajudd#114)
- Preserve the `python3 → python` fallback in hook commands for Windows.
- **Block via the JSON deny contract, not exit 2.** To block a `PreToolUse` call
  *and* surface the reason to the assistant, print the documented JSON to stdout and
  exit 0:
  `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "<why + how to fix>"}}`.
  A bare `print(reason)` + `sys.exit(2)` still blocks, but this Claude Code version
  frames exit-2 as a generic `hook error: No stderr output` and drops the reason — so
  the "Fix: …" guidance never reaches the model. Keep fail-open as plain `sys.exit(0)`.
  (comms Teams-HTML lint, v2.4.1.)
- **The live hook runs from the installed CACHE, not the marketplace clone.**
  `${CLAUDE_PLUGIN_ROOT}` resolves to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`,
  so editing the file under `.../marketplaces/…` has zero live effect until you commit,
  push, and `claude plugin update <plugin>` (and restart if `hooks.json` — not just the
  script — changed). To verify a hook change, deploy + reinstall first, or pipe a test
  payload straight at the cache copy.
