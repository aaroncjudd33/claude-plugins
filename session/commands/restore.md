---
name: restore
description: Instantly restore session context after /clear — an explicit named-file load. `/session:restore <name>` picks up the context file `/session:store` wrote; bare restore lists the available context files to pick from.
---

# Session Restore

Fast context restoration after `/clear`. Loads a named pre-clear context file (`_context_<name>.md`, written by `/session:store`) plus its session file, and drops you back in without navigation.

Restore is **explicit**: `/session:restore <name>` picks up exactly that session's context file — no hidden markers, no guessing which session was active. This works identically after a `/clear` in the same terminal or from a brand-new session later. Bare `/session:restore` (no name) lists the context files available to pick from.

**This is not session:start.** No inbox processing, no Teams setup, no options list (unless you run it bare with multiple context files present). Pure context restoration.

## Instructions

### 1. Resolve the Target Session

Resolve the repo slug as `basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"` and use that output verbatim. **Do NOT use the dashed project-directory name from your environment context** (e.g. `C--Users-ajudd--...`) — that is Claude Code's mangled memory-path key, not the slug; using it is exactly why a restore can come up empty when a store succeeded. Resolve `session_root` using Path Resolution (see Session Skill). **Context files are always local** — they live at `~/.claude/memory/sessions/<slug>/`, treated exactly like `_active` (never in a repo, never migrated). A restore point is a personal, ephemeral, local stash.

**If a name was given** (`/session:restore <name>`) — that is the target. No scanning, no guessing. Proceed to Step 2 with `<session-name> = <name>`. (If `_context_<name>.md` turns out not to exist, Step 3 notes it and restores from the session file alone.)

**If no name was given** (bare `/session:restore`) — list the available context files and let the user pick. Enumerate `_context_*.md` in the local session dir with a no-match-safe command (a bare glob aborts under zsh on macOS):
```bash
find ~/.claude/memory/sessions/<slug> -maxdepth 1 -name '_context_*.md' 2>/dev/null | xargs -r ls -1t 2>/dev/null
```
Derive each session name by stripping the `_context_` prefix and `.md` suffix. Order most-recently-modified first. Read `~/.claude/memory/sessions/<slug>/_active` (if present) to flag the matching entry as "last active".

- **None found:** there is no saved context to restore. **Stop cleanly** (command-level enforcement — acp-ajudd#1):
  ```
  No stored context for <slug>. Run /session:store before /clear, or /session:start to pick up work.
  ```
  Editing files is never blocked; the session commands are what require a session. (`start` / `refine` and read-only views are exempt.)
- **One found:** proceed automatically with that session — no prompt needed.
- **Multiple found:** show a numbered list and wait for a plain-text reply — no widget:
  ```
  Stored context available:
    1  <session-name-1>   ← last active
    2  <session-name-2>
    ...
  Which? (number or name)
  ```
  Resolve the reply to a `<session-name>`, then proceed to Step 2.

### 2. Load Session File

Read `<session_root>/<session-name>.md` and extract all fields.

Read last 5 entries from `<session_root>/_history.md` (omit block if file doesn't exist).

### 3. Load Pre-Clear Context (if present)

Check for `~/.claude/memory/sessions/<slug>/_context_<session-name>.md` (always local).

If found, read the full file. This is the volatile reasoning layer captured before `/clear`.

If **not** found (e.g. a name was given for a session that was never `store`d, or the context file was already archived), note it and continue with the session file alone — the resume still works, just without the extra pre-clear layer:
```
No _context_<session-name>.md found — restoring from the session file only.
```

### 4. Display Resume Block

```
Resuming <name> (after /clear)
  Branch:      <branch>
  Open items:  <bullets or "none">
  Next step:   <next step>

Recent history:
  [YYYY-MM-DD] <entry>
  ...

Pre-clear context:
  Problem:     <problem being solved>
  Decisions:   <key decisions>
  Next action: <exact next action>
  [full context available — type 'context' to see all sections]
```

Show a compact summary by default. If the user types `context`, display the full `_context_<session-name>.md` contents. **Omit the `Pre-clear context:` block entirely** if no context file was loaded (Step 3 found none) — the resume then shows just the session-file fields and recent history.

### 5. Clean Up

If `_context_<session-name>.md` was loaded, **delete it now — no prompt.** A restore point is consumed on load: it has been read into context, so it no longer serves a purpose and does not stick around. (This is the "git stash" model — pop, don't keep.) Report it inline: `Context file loaded and consumed (deleted _context_<name>.md).`

Update `Status` field in `<session_root>/<session-name>.md` back to `in-progress`.

Write `~/.claude/memory/sessions/<slug>/_active` with the session name (always local — this is `_active`'s legitimate current-session-marker job: it refreshes the hint for `session:start` and satisfies the command-level session check, but restore no longer *reads* it to decide what to load — the name (or the context-file listing) does that).

### 6. Continue

No inbox processing. No Teams setup. Work resumes from where it left off.
