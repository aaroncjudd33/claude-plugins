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

List all `.md` files in `~/.claude/memory/sessions/<slug>/` (skip `_active` and `_inbox*` files).

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

Read `~/.claude/memory/sessions/<slug>/<name>.md` and display:

```
Switching to <name>
  Branch:      [branch]
  Last work:   [last worked on]
  Open items:  [bullets or "none"]
  Next step:   [next step]
```

### 4. Check Inbox

For plugin sessions (path contains `ajudd-claude-plugins`): check `~/.claude/memory/sessions/<slug>/_inbox_<name>.md`.
For all other sessions: check `~/.claude/memory/sessions/<slug>/_inbox.md`.

If the inbox file has content beyond the header, display and handle each item with **Work on it / Mark done / Keep** — same logic as session:start Step 5, including archive file handling and auto-purge.

For plugin sessions, also check `~/.claude/memory/sessions/<slug>/_inbox.md` for global items. Display only — never auto-cleared.

### 5. Write _active and Update Session File

Write `~/.claude/memory/sessions/<slug>/_active` with the new session name (plain text, no `.md`).

Update the `updated` date in `~/.claude/memory/sessions/<slug>/<name>.md` to today if it differs.

Done — proceed with the work.
