---
name: commit
description: Commit and push current work, update memory, and save session state. Mid-session save with a real git commit — no Jira, no Teams, no session deactivation.
---

# Session Commit

Commit in-progress work, update memory, and save session state. Use this mid-session when you want your changes committed and context saved without closing out the session.

## Instructions

### 0. Read Session Context

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).

Determine the session name from conversation context:
1. Look for the most recent "Resuming `<name>`" line (from session:start) OR "Switching to `<name>`" line (from session:switch). Use whichever is most recent.
2. Fall back to reading `~/.claude/memory/sessions/<slug>/_active` if not in context.
3. If neither is available, ask the user: "Which session are you committing for?"

Read `<session_root>/<name>.md` and extract all fields. Minimally:
- `type` (plugin / story / cab / personal / general)
- `name`
- `branch`
- `mode` (may be absent — preserve as-is)
- `title` (story/cab only — may be absent in older session files; treat as empty)
- `category` (general only — may be absent)
- `teams_chat`
- `related_cab` (story only — may be absent)
- `post_deployment_checks` (story only — preserve entire block verbatim)
- `related_stories` (cab only — may be absent)
- `linked_sessions` (may be absent)
- `plugin_reviewed` (plugin only — may be absent)

When writing the session file in Step 6, preserve all fields present in the existing file — do not drop any field that was read here.

### 1. Git Scan

| Type | Scope |
|------|-------|
| plugin | `~/.claude/plugins/marketplaces/<pluginMarketplaceName>` (read from user-config) |
| story | current working directory (work repo) |
| cab | current working directory |
| personal | current working directory |
| general | current working directory |

Run from the appropriate directory:

**Run all git checks in parallel:**

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

Append to `<session_root>/_history.md` (create the file if it does not exist, with header `# History — <slug>`):

```
[YYYY-MM-DD @<handle>] <session-name> — <accomplished sentence>
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

If the scope value is relative, resolve it as: `local_cfg.projectRoot + "/" + scope_value` (read `local_cfg` from `~/.claude/config/<slug>.json`). For legacy sessions with absolute scope, use as-is.

Review file paths accessed or modified during this conversation. Any path not beginning with the resolved absolute scope is out-of-scope.

If out-of-scope work is found, warn but do not block:

```
Out-of-scope work detected — will be excluded from this session record.

  Out-of-scope:
    - <file path>  (belongs in: <target slug>)

  Write a handoff note to the target session's inbox? (Yes / Skip)
```

If Yes: derive the target slug from the file path. Resolve the target session_root using Path Resolution.

If the target slug matches `<pluginMarketplaceName>` (read from `~/.claude/plugins/user-config.json`), also determine the target plugin:
- If the file path contains `<pluginMarketplaceName>/<plugin>/` → write to `<target_session_root>/_inbox_<plugin>.md`. Create the file if it doesn't exist with header `# Inbox — <plugin> plugin`.
- If the item is a new plugin idea → write to `<target_session_root>/_inbox.md` with a `[new-plugin]` tag.

For all other target slugs, append to `<target_session_root>/_inbox.md`. Create if needed with header `# Inbox — <target-slug>`.

Entry format in all cases:

```markdown
## [YYYY-MM-DD @<handle>] from <source-slug> / <session-name>
- <description of out-of-scope work done>
```

### 6. Session State

Write `<session_root>/<name>.md` with current state:

```
---
updated: [today's date]
---

# Session State — <name>

- **Type:** [type]
- **Mode:** [planning / coding / both]   ← preserve from session file; omit if not present (backward compat)
- **Name:** [name]
- **updated-by:** @<handle>
- **Title:** [Jira summary]   ← story/cab only; omit for other types
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Scope:** [scope path]   ← preserve from existing file; write relative if new; omit for general
- **Status:** in-progress
- **Branch:** [branch or "n/a"]
- **Last worked on:** [most recent entry from _history.md — do not synthesize, read from file]
- **Open items:** [bullet list, or "none"]
- **Next step:** [concrete next action]
- **Plugin reviewed:** <version>   ← plugin type only; write current plugin.json version when marking reviewed; omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Post-deployment checks:**   ← story type only; preserve existing value exactly as-is; omit if field not present
  - [ ] <check description>
  - [x] <acknowledged check description>
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
- **linked_sessions:** [<session-name>, ...]   ← preserve as-is; omit if not present
```

**Backward compat:** If the existing session file has a `Project:` field, preserve it on write.

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
