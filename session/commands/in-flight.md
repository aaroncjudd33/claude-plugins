---
name: in-flight
description: Show everything in flight for the current project — all sessions with their status, branch, open item count, and any spawned sessions waiting to start. Read-only, works mid-session.
---

# Session In-Flight

Read-only snapshot of all sessions for the current project. Use this mid-session to orient yourself or answer "what else is in flight?" without opening a new terminal or disrupting your current session.

## Instructions

### 1. Scan Sessions

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).

Check for a `mine` argument — if present, set `filter_mine = true`.

List all `.md` files in `session_root` — skip `_active`, `_inbox*`, `_history*`, `_backlog*`, and `_context*` files.

**Read all session files in parallel** (one read call per file), then extract:
- `Name`
- `Status` (default to `in-progress` if field absent)
- `Branch`
- `updated-by` (may be absent in older files)
- `Open items` — count bullet points
- `Last worked on` — date portion only (first 10 chars)

If `filter_mine`, filter to sessions where `updated-by` matches `@<handle>`.

### 2. Scan Inboxes, Outboxes, and Global Inbox

For each session, count:
- Inbox items: lines beginning with `[20` or `## ` in `<session_root>/_inbox_<name>.md`
- Outbox items: lines beginning with `## ` in `<session_root>/_outbox_<name>.md`

Read `<session_root>/_inbox.md`. Count total logical items. Extract any entries tagged `[spawn]` for separate display.

### 3. Output

Print immediately — no prompts, no writes. Add mine-filter hint if multiple developers' sessions are visible:

```
Sessions in <slug>   (type '/session:in-flight mine' to filter to yours)
  <name>   @<handle>   <status>   branch: <branch>   open: N   inbox: N  outbox: N   <date>
  <name>   @<handle>   <status>   branch: <branch>   open: N   inbox: N  outbox: N   <date>
  ★ [spawn] <label>   ready to start — from <source-session>

Global inbox: N items
```

Status values and display:
- `in-progress` — currently being worked on
- `paused` — started but not active right now
- `prepare-clear` — waiting for /session:restore after a /clear
- `completed` — finished (session:finish was run)
- `spawned` — staged by /session:spawn, not yet started

Sort order: `prepare-clear` first (needs immediate attention), then `in-progress`, then `paused`, then `spawned`/`completed` last.

If no sessions exist, print: "No sessions found for `<slug>`."
