---
name: finish
description: Close out a story session — transition Jira status, clear open items, and optionally send a [cab-prep] handoff to the release inbox.
argument-hint: "[BPT2-XXXX]"
---

# /story:finish [BPT2-XXXX]

Close out a completed story. Transitions Jira, cleans up the session file, and optionally
creates or updates a `[cab-prep]` item in the release inbox if the story is heading to prod.

---

## Steps

### 1. Resolve story key

Use the argument if provided. If not, extract the repo slug from `pwd` (last path component),
read `~/.claude/memory/sessions/<slug>/_active`, and read the session file to find the story
key. If still unclear, ask.

### 2. Fetch current Jira state

Call `getJiraIssue` to get: `summary`, `status`.

### 3. Transition Jira (optional)

Ask:
> "Transition story status? (current: [status])"

Options via AskUserQuestion:
- Done
- Approved for Release
- Skip — leave status as-is

Apply the transition if selected (see transition IDs in the story skill reference).

### 4. Update session file

Resolve `session_root` for this repo: check `<git-repo-root>/.claude/sessions/`; if it exists use it, otherwise use `~/.claude/memory/sessions/<slug>/`.

If a session file exists at `<session_root>/<story-key>.md`, update:
- `Status` → `complete`
- `Open items` → `none`
- `Next step` → `none`

### 5. CAB handoff (optional)

Read `pluginMarketplaceName` from `~/.claude/plugins/user-config.json`
(default: `ajudd-claude-plugins`).

Resolve the plugin marketplace session_root: check `<marketplace-repo-root>/.claude/sessions/` (where marketplace-repo-root is derived from `pluginMarketplaceName` path in user-config); if it exists use it, otherwise use `~/.claude/memory/sessions/<pluginMarketplaceName>/`.

Check `<plugin_session_root>/_inbox_release.md` for an existing
entry matching `## [...] from .* / <story-key> [cab-prep]`.

- **Entry exists:** "A cab-prep item already exists for <story-key> — update it? (yes / skip)"
- **No entry:** "Send to release inbox for CAB? (yes / skip)"

If the user says yes (either case), run the `/story:cab-prep` steps (steps 1–5 of that
command) using the story key already resolved. Skip steps 1–2 of cab-prep since the story
key and summary are already in hand.

### 6. Report

```
/story:finish — <story-key>
  <summary>

  Jira:        [status] → [new status]   ← or "unchanged"
  Session:     closed
  CAB handoff: ✓ written / ✓ updated / skipped
```
