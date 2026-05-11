---
name: finish
description: End-of-day close — full checklist including Jira, Teams, Confluence, browser, and session summary.
---

# Session Finish

Full end-of-day close. Runs the complete checklist to ensure nothing is left behind.

## Instructions

### 0. Read Session Context

Run `pwd` and extract the repo slug (last path component).

Determine the session name from conversation context:
1. Look back at the current conversation for the most recent `session:start` output — find the "Resuming `<name>`" line. Use that name.
2. If no `session:start` output is found in this conversation, fall back to reading `~/.claude/memory/sessions/<slug>/_active` as a hint.
3. If neither is available, ask the user: "Which session are you finishing?"

Read `~/.claude/memory/sessions/<slug>/<name>.md` and extract:
- `type` (plugin / story / cab / personal / general)
- `name`
- `title` (story/cab only — may be absent in older session files; treat as empty string if missing)
- `teams_chat`
- `branch`

If no session name can be determined and `_active` does not exist, treat as `type: general` with `teams_chat: none`.

If the session name is determined but `<name>.md` does not exist, warn the user: "Session file for `<name>` not found — run `/session:start` to re-establish." and stop.

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

**story/cab only — yl-cdk pattern check before updating Jira:**

```
yl-cdk check:
  Were the yl-cdk-migration and yl-cdk-monitoring skills used to verify DynamoDB/CDK design patterns?
  Yes / Not applicable / Remind me
```

- **Yes / Not applicable:** proceed silently.
- **Remind me:** surface this note before continuing — do not block:
  > "Run `/yl-cdk-migration` and `/yl-cdk-monitoring` before closing this story. Install from `youngliving/claude-plugins` if not available."

**story:**
- Is the story status current? Transition if needed.
- Post a closing Jira comment: what was accomplished this session, what's next (testing, CAB, deployment). Business-readable — no file paths or class names. Check the most recent existing comment first; only post if it doesn't already cover this session's work.

**cab:**
- Are the CAB card fields up to date?
- Is the release branch reflected correctly?
- Post a closing comment to each story in `Related stories` (same format as story above).

**plugin / personal / general:** Skip (including the yl-cdk check above).

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

### 6a. Story Doc *(story type only)*

Read `paths.jiraStoriesDir` from `~/.claude/plugins/user-config.json`. If the field is absent or empty, skip this step entirely.

Derive the doc path: `<jiraStoriesDir>/<jiraProject>/<session-name>-<slug>.md` where `<jiraProject>` is the Jira project key (e.g. `BPT2`) and `<slug>` is a short kebab-case description of the story (derive from the session Title field, or use the session name alone if Title is absent).

Check if the file exists:

- **Exists:** prompt "Story doc exists — update it with today's changes? (Yes / Skip)"
- **Does not exist:** prompt "No story doc found — create one? (Yes / Skip)"

If **Yes:** write or update the file with:
- Root cause / problem being solved
- Implementation approach and key decisions
- Testing notes and known edge cases
- Any gotchas discovered

Keep it technical and concise — this is a personal reference, not team documentation. Do not block session:finish if the user skips.

### 7. Browser

**story only:** Read `paths.voPlaywrightTestsDir` from `~/.claude/plugins/user-config.json`. If the field is empty or absent, skip this step entirely (e2e plugin is not configured for this machine).

Check if `<voPlaywrightTestsDir>/.browser-ws.txt` exists.

- If it does not exist → skip.
- If it exists, check ownership before prompting:
  1. Read `<voPlaywrightTestsDir>/.browser-owner.txt` if present
  2. Compute current owner: `<slug>/<session-name>` (slug = last component of `pwd`; session name = contents of `~/.claude/memory/sessions/<slug>/_active`)
  3. If owner file exists AND does not match current session → log "Browser running (owned by `<owner>`) — skipping close" and skip
  4. If owner matches OR no owner file exists → prompt: "Browser still running on port [N] — stop it? (or run `/e2e:stop`)"
     - If yes: run `npm run browser:stop` from `<voPlaywrightTestsDir>`, then delete `.browser-ws.txt` and `.browser-owner.txt`

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

### 9. Inbox Completion Check

Read the current `Open items` from the session file. If any items are prefixed with `[inbox]`, handle each one before writing the final session summary:

```
Inbox item complete?
  [inbox] <item summary>
  Yes / Keep open
```

- **Yes:** remove the `[inbox]` line from Open items. The inbox entry was already archived when the session picked it up — no file move needed.
- **Keep open:** leave the `[inbox]` item in Open items — it will be carried forward to the next session.

If no `[inbox]` items exist, skip silently.

### 10. History Entry

Compose a 1-sentence description of the work accomplished this session. Write it as a complete thought that stands alone without conversation context.

Append to `~/.claude/memory/sessions/<slug>/_history.md` (create the file if it does not exist, with header `# History — <slug>`):

```
[YYYY-MM-DD] <session-name> — <accomplished sentence>
```

This entry becomes the value for `Last worked on` in the session file.

### 11. Session Summary

Before writing, read the existing `Open items` from the session file. If there are any **non-`[inbox]`** items, display them and ask:

```
Open items — any complete?
  [1] <item>
  [2] <item>
  Mark done (enter numbers), or 'skip'
```

Remove confirmed-complete items from the Open items list before writing.

Write `~/.claude/memory/sessions/<slug>/<name>.md` with the final state for today:

```
---
updated: [today's date]
---

# Session State — <name>

- **Type:** [type]
- **Mode:** [planning / coding / both]   ← preserve from session file; omit if not present (backward compat)
- **Name:** [name]
- **Title:** [Jira summary]   ← story/cab only; omit for other types
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Project:** [project path]
- **Scope:** [scope path]   ← story/cab/personal: pwd; plugin: ~/.claude/plugins/marketplaces/ajudd-claude-plugins/<name>; omit for general
- **Status:** completed
- **Branch:** [branch or "n/a"]
- **Last worked on:** [most recent entry from _history.md — do not synthesize, read from file]
- **Open items:** [bullet list, or "none"]
- **Next step:** [concrete first action when resuming tomorrow]
- **Plugin reviewed:** [yes / no]   ← plugin type only, omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Post-deployment checks:**   ← story type only, omit for other types; omit entire field if none defined
  - [ ] <check description>
  - [x] <acknowledged check description>
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
```

**General sessions only:** Also check `~/.claude/memory/sessions/<slug>/<name>/` — if notes, decisions, or outputs were produced today, ensure they are written there before closing.

**Story type only — post-deployment checks:**

Before writing, check the current `Post-deployment checks:` field (if present) and prompt:

```
Post-deployment checks — anything to add or update? (enter new checks, or 'skip')
```

- If the user enters checks, append them as `- [ ] <check>` items under `Post-deployment checks:`
- If the field does not exist yet and the user enters checks, create it
- If the user skips and the field is already set, preserve it as-is
- These checks will be surfaced and acknowledged when the related CAB closes via `/release:deploy`

**Ask next step:**

Before writing, ask the user: "What's the first thing to pick up next time? (or 'skip')" Then offer where to route it:

```
Add to: inbox (ready — pick up next session) / backlog (defer — not working on it soon) / skip
```

For **personal and general** session types, lead with inbox as the expected choice — work that surfaces at session close is usually planned and ready, not deferred.

- **inbox:** write as an inbox entry to `_inbox_<name>.md` (plugin) or `_inbox.md` (others) using format `## [YYYY-MM-DD] from <slug> / <name> — <description>`. Create the file if needed with header `# Inbox — <name> plugin` (plugin) or `# Inbox — <slug>` (others). Set `Next step` in the session file to the description (convenience echo of the inbox entry).
- **backlog:** write to `_backlog_<name>.md` (plugin) or `_backlog.md` (others) using the same entry format. Create the file if needed with header `# Backlog — <name> plugin` (plugin) or `# Backlog — <slug>` (others). Set `Next step` to "none".
- **skip:** set `Next step` to "none".

If the user says "same" or similar, carry forward the current `Next step` value and write it to inbox.

Print the summary to screen as the final output.

### 12. Work Log

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

### 13. Deactivate Session

Remove the active marker so no future conversation inherits stale state:

```bash
rm ~/.claude/memory/sessions/<slug>/_active
```
