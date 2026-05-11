---
name: commit
description: Commit and push current work, update memory, and save session state. Mid-session save with a real git commit — no Jira, no Teams, no session deactivation.
---

# Session Commit

Commit in-progress work, update memory, and save session state. Use this mid-session when you want your changes committed and context saved without closing out the session.

## Instructions

### 0. Read Session Context

Run `pwd` and extract the repo slug (last path component).

Determine the session name from conversation context:
1. Look for the most recent `session:start` output — find the "Resuming `<name>`" line.
2. Fall back to reading `~/.claude/memory/sessions/<slug>/_active` if not in context.
3. If neither is available, treat as `type: general`.

Read `~/.claude/memory/sessions/<slug>/<name>.md` and extract:
- `type` (plugin / story / cab / general)
- `name`
- `branch`

### 1. Git Scan

| Type | Scope |
|------|-------|
| plugin | `~/.claude/plugins/marketplaces/ajudd-claude-plugins` |
| story | current working directory (work repo) |
| cab | current working directory |
| personal | current working directory |
| general | current working directory |

Run from the appropriate directory:

```bash
git status
git diff --staged
git diff
```

If there is nothing to commit (clean working tree, no staged changes): report "Git: nothing to commit" and skip to step 3.

If there are changes, continue to step 2.

### 2. Draft and Confirm Commit Message

Scan the staged and unstaged changes (`git diff HEAD`) to understand what changed. Draft a concise commit message following the repo's style (seen in recent `git log --oneline -5`).

Show the draft to the user:

```
Commit message:
  <drafted message>

Commit and push? (Yes / Edit / Cancel)
```

- **Yes:** stage all changed files (`git add` the relevant files — not `git add -A` blindly; add the files that belong to this session's scope), then commit with the drafted message and push.
- **Edit:** ask the user for their preferred message, then commit and push with that.
- **Cancel:** stop here. Do not proceed to memory or session state steps.

Commit format:
```bash
git commit -m "$(cat <<'EOF'
<message>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

### 2a. Jira Commit Comment *(story/cab only)*

Post a 1-line Jira comment summarizing what was just committed.

- **story:** story key = session name
- **cab:** post to each story in `Related stories`

Translate the commit message to business-readable language — status + milestone, no file paths, class names, or token names. Example: *"Committed touchToken fix for all 3 filter input types — testing in progress."*

Before posting, check if the most recent Jira comment already covers this commit — if so, skip.

**plugin / personal / general:** Skip.

### 3. History Entry

Compose a 1-sentence description of what was accomplished in this commit. Write it as a complete thought that stands alone without conversation context.

Append to `~/.claude/memory/sessions/<slug>/_history.md` (create the file if it does not exist, with header `# History — <slug>`):

```
[YYYY-MM-DD] <session-name> — <accomplished sentence>
```

This entry becomes the value for `Last worked on` in the session file.

### 4. Memory

Review the conversation since the last checkpoint/commit for anything worth saving:
- Feedback, corrections, or rules established
- Workflow or convention changes
- Anything non-obvious that future sessions should know

Save what's missing. Report: "Saved: [list]" or "Memory: nothing new to save."

### 5. Scope Check

Read the `Scope:` field from the session file. If the field is missing or the session type is `general`, skip this step.

Review file paths accessed or modified during this conversation. Any path not beginning with the `Scope:` value is out-of-scope.

If out-of-scope work is found, warn but do not block:

```
Out-of-scope work detected — will be excluded from this session record.

  Out-of-scope:
    - <file path>  (belongs in: <target slug>)

  Write a handoff note to the target session's inbox? (Yes / Skip)
```

If Yes: append to `~/.claude/memory/sessions/<target-slug>/_inbox.md`:

```markdown
## [date] from <source-slug> / <session-name>
- <description of out-of-scope work done>
```

Create the file if it does not exist, starting with `# Inbox — <target-slug>` as the first line.

### 6. Session State

Write `~/.claude/memory/sessions/<slug>/<name>.md` with current state:

```
---
updated: [today's date]
---

# Session State — <name>

- **Type:** [type]
- **Mode:** [planning / coding / both]   ← preserve from session file; omit if not present (backward compat)
- **Name:** [name]
- **Title:** [Jira summary]   ← story/cab only; omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Project:** [project path]
- **Scope:** [scope path]   ← story/cab/personal: pwd; plugin: ~/.claude/plugins/marketplaces/ajudd-claude-plugins/<name>; omit for general
- **Status:** in-progress
- **Branch:** [branch or "n/a"]
- **Last worked on:** [most recent entry from _history.md — do not synthesize, read from file]
- **Open items:** [bullet list, or "none"]
- **Next step:** [concrete next action]
- **Plugin reviewed:** [yes / no]   ← plugin type only, omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Post-deployment checks:**   ← story type only; preserve existing value exactly as-is; omit if field not present
  - [ ] <check description>
  - [x] <acknowledged check description>
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
- **linked_sessions:** [<session-name>, ...]   ← preserve as-is; omit if not present
```

Print the summary to screen.

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

**Accomplished:** <most recent entry from _history.md>

**Open items:** <open items from session state, or "none">
```

Multiple entries per day are expected — always append, never overwrite.
