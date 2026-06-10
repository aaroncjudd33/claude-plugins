---
name: switch
description: Switch to a different session without the full session:start overhead. Use mid-day to pivot between sessions.
---

# Session Switch

Lightweight context swap for mid-day pivots between sessions. Skips permission mode, teams chat setup, and routing branches — just loads the target session and goes.

## Instructions

### 1. Derive Repo Slug

Run `pwd` and extract the last path component as the repo slug.

### 2. Load Session List

List all `.md` files in `~/.claude/memory/sessions/<slug>/` (skip `_active`, `_inbox*`, `_history*`, `_backlog*`, and `_context*` files).

For each file, read and extract: Name, Branch, Last worked on.

For plugin sessions (path contains `ajudd-claude-plugins`): count logical items in `_inbox_<name>.md` for each session (lines beginning with `[20` or `## `).
For all other sessions: count logical items in `_inbox.md`.

If an argument was passed to the command (e.g. `/session:switch release`), skip the list and jump directly to step 3 with that name.

Otherwise, print the numbered list and wait for selection:
```
Sessions in <slug>
  [1]  <name>  |  master  |  inbox 0  |  <last worked on>
  [2]  <name>  |  master  |  inbox 2  |  <last worked on>
```

### 3. Display Resume Block

Read `~/.claude/memory/sessions/<slug>/<name>.md`.
Read `~/.claude/memory/sessions/<slug>/_history.md` — count total entries and extract the most recent one.
Read the inbox file (`_inbox_<name>.md` for plugins, `_inbox.md` otherwise) and collect all items (in-progress and pending).

Display:

```
Switching to <name>
  Branch:      [branch]
  Mode:        [planning / coding / both — omit if field absent]
  Open items:  [bullets or "none"]
  Inbox (N):
    [1] [date] <description> — in-progress / pending
  History:     N entries — last: [condensed one-liner of most recent entry]
```

If inbox is empty: `Inbox: none`. If no history: `History: none`.

### 4. Check Inbox

For plugin sessions (path contains `ajudd-claude-plugins`): check `~/.claude/memory/sessions/<slug>/_inbox_<name>.md`.
For all other sessions: check `~/.claude/memory/sessions/<slug>/_inbox.md`.

If the inbox file has content beyond the header, first scan for in-progress items, then handle pending items.

**In-progress items** (entries with an `[in-progress — ...]` line) — show first:

```
Resuming in-progress (<N> item(s)):
  [1] [in-progress since YYYY-MM-DD] <description from entry header>
  Mark done (numbers, 'all') / Keep working / skip
```

- **Mark done:** strip the `[in-progress — ...]` line, archive with `[DONE YYYY-MM-DD]` stamp to `_inbox_<name>_archive.md` (plugin) or `_inbox_archive.md` (others), remove entry from inbox, remove matching `[inbox] <item>` from session Open items.
- **Keep working / skip:** no change.

**Pending items** (no in-progress marker) — show after, and handle each with **Work on it / Mark done / Move to backlog / Keep**:
- **Work on it:** insert `[in-progress — <session-name>, YYYY-MM-DD]` after the `## [date]...` header in the inbox file. Do NOT archive. Add `[inbox] <item>` to session Open items.
- **Mark done:** archive with `[DONE YYYY-MM-DD]` stamp to `_inbox_<name>_archive.md` (plugin) or `_inbox_archive.md` (others), remove from inbox.
- **Move to backlog:** move to `_backlog_<name>.md` (plugin) or `_backlog.md` (others), remove from inbox.
- **Keep:** leave as-is. Do not add to Open items.

Auto-purge archive entries with `[DONE]` dates older than 30 days after handling.

For plugin sessions, also check `~/.claude/memory/sessions/<slug>/_inbox.md` for global items. Display only — never auto-cleared.

### 5. Write _active and Update Session File

Write `~/.claude/memory/sessions/<slug>/_active` with the new session name (plain text, no `.md`).

Update the `updated` date in `~/.claude/memory/sessions/<slug>/<name>.md` to today if it differs.

Done — proceed with the work.
