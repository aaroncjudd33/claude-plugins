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
- `type` (plugin / story / cab / personal / general)
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
| personal | current working directory |
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

**plugin / personal / general:** Skip.

### 5. Teams Update

**All types** — if `teams_chat` is not `none`:
- Prompt: "Post a closing update to [teams_chat]?"
- If yes: read `~/.claude/plugins/marketplaces/ajudd-claude-plugins/comms/skills/comms/references/teams-html-guide.md`, draft using the Standard Message Template, preview, wait for confirmation before sending

Story and cab: prompt automatically.
Plugin, personal, and general: only prompt if the user asks or something significant was resolved.

### 6. Confluence

**All types:** If this session's context has a linked Confluence page, prompt:
"Does anything from this session need to go to Confluence?"

Skip if no Confluence page is set up for this session's context.

### 7. Browser

**story only:** Check if `/c/dev/vo-playwright-tests/.browser-ws.txt` exists.

- If it does not exist → skip.
- If it exists, check ownership before prompting:
  1. Read `/c/dev/vo-playwright-tests/.browser-owner.txt` if present
  2. Compute current owner: `<slug>/<session-name>` (slug = last component of `pwd`; session name = contents of `~/.claude/memory/sessions/<slug>/_active`)
  3. If owner file exists AND does not match current session → log "Browser running (owned by `<owner>`) — skipping close" and skip
  4. If owner matches OR no owner file exists → prompt: "Browser still running on port [N] — stop it? (or run `/e2e:stop`)"
     - If yes: run `npm run browser:stop` from `/c/dev/vo-playwright-tests`, then delete `.browser-ws.txt` and `.browser-owner.txt`

**All other types:** Skip.

### 8. Cross-Scope Guard

Read the `Scope:` field from the session file. If the field is missing or the session type is `general`, skip this step.

Review file paths that were accessed or modified during this conversation (Read, Edit, Write, Bash file operations). Any path that does not begin with the `Scope:` value is out-of-scope.

If out-of-scope work is found, **hard block** — do not proceed to the Session Summary:

```
Cross-scope work detected — cannot close this session cleanly.

  Out-of-scope changes:
    - <file path>  (belongs in: <target slug>)

  Options:
    [1] Write a handoff note to the correct session's inbox and exclude from this record
    [2] Acknowledge as out-of-scope, exclude from record (no handoff)
    [3] Cancel finish — I'll handle it manually
```

**Option [1]:** Derive the target slug from the file path (e.g. `ajudd-claude-plugins` for plugin files; last component of `/dev/` paths for work projects).

If the target slug is `ajudd-claude-plugins`, also determine the target plugin:
- If the file path contains `ajudd-claude-plugins/<plugin>/` → write to `~/.claude/memory/sessions/ajudd-claude-plugins/_inbox_<plugin>.md`. Create the file if it doesn't exist with header `# Inbox — <plugin> plugin`.
- If the item is a new plugin idea (no specific existing plugin maps to the file path) → write to `~/.claude/memory/sessions/ajudd-claude-plugins/_inbox.md` with a `[new-plugin]` tag on the entry. Create the file if it doesn't exist with header `# Inbox — ajudd-claude-plugins`.

For all other target slugs, append to `~/.claude/memory/sessions/<target-slug>/_inbox.md`. Create the file if it doesn't exist with header `# Inbox — <target-slug>`.

In all cases, the entry format is:

```markdown
## [date] from <source-slug> / <session-name>
- <description of out-of-scope work done>
```

**Option [2]:** Note the excluded work in the session summary's Open items field.

**Option [3]:** Stop. Do not write the Session Summary or Deactivate the session.

Only proceed to step 9 once all flagged items are resolved (or none were found).

### 9. Session Summary

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
- **Scope:** [scope path]   ← story/cab/personal: pwd; plugin: ~/.claude/plugins/marketplaces/ajudd-claude-plugins/<name>; omit for general
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

### 10. Deactivate Session

Remove the active marker so no future conversation inherits stale state:

```bash
rm ~/.claude/memory/sessions/<slug>/_active
```
