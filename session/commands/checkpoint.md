---
name: checkpoint
description: Mid-session save — git scan, memory, update session state. Fast, no prompts.
---

# Session Checkpoint

Quick mid-session save. Captures current state so nothing is lost if the session is interrupted.

## Instructions

### 0. Read Session Context

Read `C:\Users\ajudd\.claude\memory\session_active.md` and extract:
- `type` (plugin / story / cab / general)
- `name`
- `teams_chat`
- `branch`

If the file does not exist, treat as `type: general` with `teams_chat: none`.

### 1. Header

Output:
```
Session Checkpoint — <DayOfWeek>, <Month> <Day>, <Year>
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

Update `C:\Users\ajudd\.claude\memory\session_active.md` with the current state:

```
---
updated: [today's date]
---

# Active Session State

- **Type:** [type]
- **Name:** [name]
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Project:** [project name or path]
- **Branch:** [branch or "n/a"]
- **Last worked on:** [1 sentence — what is happening right now]
- **Open items:** [bullet list, or "none"]
- **Next step:** [concrete next action]
```

Print the summary to screen.
