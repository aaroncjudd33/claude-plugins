---
name: finish
description: End-of-day close — full checklist including Jira, Teams, Confluence, browser, and session summary.
---

# Session Finish

Full end-of-day close. Runs the complete checklist to ensure nothing is left behind.

## Instructions

### 0. Read Session Context

Run `pwd` and extract the repo slug (last path component).

Read `~/.claude/memory/sessions/<slug>/_active` to get the session name.

Read `~/.claude/memory/sessions/<slug>/<name>.md` and extract:
- `type` (plugin / story / cab / general)
- `name`
- `teams_chat`
- `branch`

If `_active` does not exist, treat as `type: general` with `teams_chat: none`.

If `_active` exists but `<name>.md` does not, warn the user: "Session file for `<name>` not found — run `/session:start` to re-establish." and stop.

### 1. Header

Output:
```
Session Finish — <name> (<type>)
<DayOfWeek>, <Month> <Day>, <Year>
================================================================
```

### 2. Git Scan

| Type | Scope |
|------|-------|
| plugin | `~/.claude/plugins/marketplaces/ajudd-claude-plugins` |
| story | current working directory (work repo) |
| cab | current working directory — check release branch specifically |
| general | skip |

Check:
- Uncommitted/unstaged changes (`git status`)
- Stashed changes (`git stash list`)
- Unpushed commits (`git log --oneline @{u}..HEAD 2>/dev/null`)
- Current branch name

Report anything that could be lost. If uncommitted changes exist: "Want to commit before closing?"

If clean: "Git: clean"

### 3. Memory

Review the conversation for anything worth saving:
- Feedback, corrections, or rules established
- Workflow or convention changes
- Project or session state updates
- Anything non-obvious that future sessions should know

Save what's missing. Report: "Saved: [list]" or "Memory: nothing new to save."

### 4. Jira Update

**story:**
- Is the story status current? Transition if needed.
- Does it need a progress comment before closing?

**cab:**
- Are the CAB card fields up to date?
- Is the release branch reflected correctly?

**plugin / general:** Skip.

### 5. Teams Update

**All types** — if `teams_chat` is not `none`:
- Prompt: "Post a closing update to [teams_chat]?"
- If yes: draft update, preview, wait for confirmation before sending

Story and cab: prompt automatically.
Plugin and general: only prompt if the user asks or something significant was resolved.

### 6. Confluence

**All types:** If this session's context has a linked Confluence page, prompt:
"Does anything from this session need to go to Confluence?"

Skip if no Confluence page is set up for this session's context.

### 7. Browser

**story only:** Check if `C:\dev\vo-playwright-tests\.browser-ws.txt` exists.
- If it does: "Browser still running on port [N] — stop it? (or run `/chrome:stop`)"
- If yes: run `npm run browser:stop` from `/c/dev/vo-playwright-tests`, then delete `.browser-ws.txt`

**All other types:** Skip.

### 8. Session Summary

Write `~/.claude/memory/sessions/<slug>/<name>.md` with the final state for today:

```
---
updated: [today's date]
---

# Session State — <name>

- **Type:** [type]
- **Name:** [name]
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Project:** [project path]
- **Branch:** [branch or "n/a"]
- **Last worked on:** [1 sentence — what was accomplished today]
- **Open items:** [bullet list, or "none"]
- **Next step:** [concrete first action when resuming tomorrow]
- **Plugin reviewed:** [yes / no]   ← plugin type only, omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
```

**General sessions only:** Also check `~/.claude/memory/sessions/<slug>/<name>/` — if notes, decisions, or outputs were produced today, ensure they are written there before closing.

Before writing, ask the user: "What's the first thing to pick up next time?" Use their answer for the `Next step` field. If they say "same" or similar, carry forward the current value.

Print the summary to screen as the final output.

### 9. Deactivate Session

Remove the active marker so no future conversation inherits stale state:

```bash
rm ~/.claude/memory/sessions/<slug>/_active
```
