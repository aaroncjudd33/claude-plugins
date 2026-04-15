---
name: checkpoint
description: Save work state and ensure nothing is lost before closing or pausing. Use mid-session or end of day.
---

# Session Checkpoint

Save work state and ensure nothing important is lost. Works mid-session or at end of day.

## Instructions

### 1. Closing or Mid-Session?

Ask the user one question: "Closing for the day, or mid-session checkpoint?"
- **Closing**: run full checklist including browser prompt
- **Mid-session**: same checklist, skip browser prompt, frame summary as "current state" not "pick up here"

Output a header:
```
Session Checkpoint — <DayOfWeek>, <Month> <Day>, <Year>
================================================================
```

### 2. Git Scan (Auto)

Scope to the current working directory's repo only.

Check:
- Uncommitted or unstaged changes (`git status`)
- Stashed changes (`git stash list`)
- Unpushed commits (`git log --oneline @{u}..HEAD 2>/dev/null`)
- Current branch name

Report anything that could be lost. If uncommitted changes exist, ask: "Want to commit before closing?"

If everything is clean: "Git: clean"

### 3. Memory (Auto)

Review the conversation for anything worth saving:
- New feedback or corrections from the user
- Workflow changes or rules established
- Project or story state changes
- Anything non-obvious that future sessions should know

Save what's missing. Report: "Saved: [list]" or "Memory: nothing new to save."

### 4. Active Story (Contextual)

If a story was worked on this session:

- **Jira status** — is it current?
- **Jira comment** — does it need one before closing?
- **Local story doc** — check `C:\Users\ajudd\claude\jira-stories\<project>\<slug>.md`:
  - If it exists: is it up to date?
  - If it doesn't exist: create it now based on conversation context, then confirm with user

Skip entirely if no story was active.

### 5. Teams Update (Contextual)

If a story has a Teams chat and meaningful work happened:
- Prompt: "Does [BPT2-XXXX] need a Teams update before you close?"
- If yes: draft one, preview, wait for confirmation before sending

Skip if no story or no meaningful work happened.

### 6. Confluence (Contextual)

If implementation decisions were made or scope changed:
- Prompt: "Does the Confluence page for [BPT2-XXXX] need updating?"

Skip if no Confluence page exists for this story, or nothing changed.

### 7. Browser (Closing only — Contextual)

Check if `C:\dev\vo-playwright-tests\.browser-ws.txt` exists.
- If it does: "Browser still running on port [N] — stop it?"
- If yes: run `cd /c/dev/vo-playwright-tests && npm run browser:stop`
- Skip entirely if the file doesn't exist or if mid-session.

### 8. Session Summary

Write current work state to `C:\Users\ajudd\.claude\memory\session_active.md` (update if exists, create if not).

Content to save:
- Project: [name or working directory]
- Story: [BPT2-XXXX] — [title] (or "No active story")
- Status: [current Jira status]
- Branch: [current branch]
- Last worked on: [1 sentence — what happened this session]
- Open items: [bullet list, or "none"]
- Next step: [concrete first action when resuming]

Then print the summary to screen as the final output.
