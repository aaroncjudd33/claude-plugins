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
- `type` (plugin / story / cab / personal / general)
- `name`
- `title` (story/cab only — may be absent in older session files; treat as empty string if missing)
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
| personal | current working directory |
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

### 4. Scope Check

Read the `Scope:` field from the session file. If the field is missing or the session type is `general`, skip this step.

Review file paths accessed or modified during this conversation. Any path not beginning with the `Scope:` value is out-of-scope.

If out-of-scope work is found, warn but do not block:

```
Out-of-scope work detected — will be excluded from this checkpoint.

  Out-of-scope:
    - <file path>  (belongs in: <target slug>)

  Write a handoff note to the target session's inbox? (Yes / Skip)
```

If Yes: derive the target slug from the file path and append to `~/.claude/memory/sessions/<target-slug>/_inbox.md`:

```markdown
## [date] from <source-slug> / <session-name>
- <description of out-of-scope work done>
```

Create the file if it does not exist, starting with `# Inbox — <target-slug>` as the first line.

Continue with the checkpoint for in-scope work only.

### 5. Session Summary

Before writing, read the existing `Open items` from the session file. If there are any **non-`[inbox]`** items, display them and ask:

```
Open items — any complete?
  [1] <item>
  [2] <item>
  Mark done (enter numbers), or 'skip'
```

Remove confirmed-complete items from the Open items list before writing.

Write `~/.claude/memory/sessions/<slug>/<name>.md` with the current state:

```
---
updated: [today's date]
---

# Session State — <name>

- **Type:** [type]
- **Name:** [name]
- **Title:** [Jira summary]   ← story/cab only; omit for other types
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Project:** [project path]
- **Scope:** [scope path]   ← story/cab/personal: pwd; plugin: ~/.claude/plugins/marketplaces/ajudd-claude-plugins/<name>; omit for general
- **Branch:** [branch or "n/a"]
- **Last worked on:** [1 sentence — what is happening right now]
- **Open items:** [bullet list, or "none"]
- **Next step:** [concrete next action]
- **Plugin reviewed:** [yes / no]   ← plugin type only, omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
```

Print the summary to screen.

### 6. Inbox Completion Check

Read the `Open items` from the session state just written. If any items are prefixed with `[inbox]`, handle each one:

```
Inbox item complete?
  [inbox] <item summary>
  Yes / Keep open
```

- **Yes:** locate the corresponding entry in the inbox file (`_inbox_<name>.md` for plugins, `_inbox.md` otherwise); move it to the archive file with `[DONE today]` prepended; remove the `[inbox]` line from Open items; rewrite both files. The session summary's Open items field (step 5) should be rewritten to reflect the removal.
- **Keep open:** leave the `[inbox]` item in Open items and the entry in the inbox file as-is

If no `[inbox]` items exist in Open items, skip silently.

### 7. Work Log

Append to `~/.claude/memory/worklog/<YYYY-MM-DD>.md` (create the file and `~/.claude/memory/worklog/` directory if they don't exist).

Use today's date for the filename. Use the current local time (HH:MM) for the entry header.

Entry format varies by type:

- **story/cab with title:** `## <HH:MM> — <name> — <title> (<type>)`
- **story/cab without title** (older session files): `## <HH:MM> — <name> (<type>)`
- **plugin:** `## <HH:MM> — <name>` (no type label — the name is self-identifying)
- **personal/general:** `## <HH:MM> — <name> (<type>)`

```markdown
## <HH:MM> — <formatted header per above>

**Accomplished:** <last worked on — same 1-sentence value just written to the session file>

**Open items:** <open items from session state, or "none">
```

Multiple entries per day are expected — always append, never overwrite.
