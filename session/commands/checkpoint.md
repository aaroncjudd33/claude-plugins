---
name: checkpoint
description: Mid-session save — git scan, memory, update session state. Fast, no prompts.
---

# Session Checkpoint

Quick mid-session save. Captures current state so nothing is lost if the session is interrupted.

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
Session Checkpoint — <name> (<type>)
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

Report anything that could be lost. If uncommitted changes exist: "Want to commit before continuing?"

If clean: "Git: clean"

### 3. Memory

Review the conversation for anything worth saving:
- Feedback, corrections, or rules established
- Workflow or convention changes
- Project or session state updates
- Anything non-obvious that future sessions should know

Save what's missing. Report: "Saved: [list]" or "Memory: nothing new to save."

### 4. Session Summary

Write `~/.claude/memory/sessions/<slug>/<name>.md` with the current state:

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
- **Last worked on:** [1 sentence — what is happening right now]
- **Open items:** [bullet list, or "none"]
- **Next step:** [concrete next action]
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
```

Print the summary to screen.
