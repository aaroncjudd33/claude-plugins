---
name: status
description: Show everything in flight for the current project — all sessions with their status, branch, open item count, and any spawned sessions waiting to start. Read-only, works mid-session.
---

# Session Status

Read-only snapshot of all sessions for the current project. Use this mid-session to orient yourself or answer "what else is in flight?" without opening a new terminal or disrupting your current session.

## Instructions

### 1. Scan Sessions

Run `pwd` and extract the repo slug (last path component).

List all `.md` files in `~/.claude/memory/sessions/<slug>/` — skip `_active`, `_inbox*`, `_history*`, `_backlog*`, and `_context*` files.

For each session file, read and extract:
- `Name`
- `Status` (default to `in-progress` if field absent)
- `Branch`
- `Open items` — count bullet points
- `Last worked on` — date portion only (first 10 chars)

### 2. Scan Global Inbox for Spawns

Read `~/.claude/memory/sessions/<slug>/_inbox.md`. Count total logical items (lines beginning with `[20` or `## `). Extract any entries tagged `[spawn]` for separate display.

### 3. Output

Print immediately — no prompts, no writes:

```
Sessions in <slug>
  <name>          <status>        branch: <branch>        open: N   <date>
  <name>          <status>        branch: <branch>        open: N   <date>
  ★ [spawn] <label>   ready to start — from <source-session>

Global inbox: N items
```

Status values and display:
- `in-progress` — currently being worked on
- `paused` — started but not active right now
- `prepare-clear` — waiting for /session:resume after a /clear
- `completed` — finished (session:finish was run)
- `spawned` — staged by /session:spawn, not yet started

Sort order: `prepare-clear` first (needs immediate attention), then `in-progress`, then `paused`, then `spawned`/`completed` last.

If no sessions exist, print: "No sessions found for `<slug>`."
