---
name: checkpoint
description: Mid-session save — git scan, memory, update session state. Fast, no prompts.
---

# Session Checkpoint

Quick mid-session save. Captures current state so nothing is lost if the session is interrupted.

## Instructions

### 0. Read Session Context

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).

Determine the session name from conversation context:
1. Look back at the current conversation for the most recent "Resuming `<name>`" line (from session:start) OR "Switching to `<name>`" line (from session:switch). Use whichever is most recent.
2. If neither is found in this conversation, fall back to reading `~/.claude/memory/sessions/<slug>/_active` as a hint.
3. If neither is available, ask the user: "Which session are you checkpointing?"

Read `<session_root>/<name>.md` and extract:
- `type` (plugin / story / cab / personal / general)
- `name`
- `title` (story/cab only — may be absent in older session files; treat as empty string if missing)
- `teams_chat`
- `branch`

If no session name can be determined and `_active` does not exist, treat as `type: general` with `teams_chat: none`.

If the session name is determined but `<session_root>/<name>.md` does not exist, warn the user: "Session file for `<name>` not found — run `/session:start` to re-establish." and stop.

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
| plugin | `~/.claude/plugins/marketplaces/<pluginMarketplaceName>` (read from user-config) |
| story | current working directory (work repo) |
| cab | current working directory — check release branch specifically |
| personal | current working directory |
| general | skip |

**Run all git checks in parallel:**
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

### 3a. yl-cdk Pattern Check *(story/cab only)*

If a commit was just made or is about to be made, prompt:

```
yl-cdk check:
  Were the yl-cdk-migration and yl-cdk-monitoring skills used to verify DynamoDB/CDK design patterns?
  Yes / Not applicable / Remind me
```

- **Yes / Not applicable:** proceed silently.
- **Remind me:** surface this note and continue — do not block:
  > "Run `/yl-cdk-migration` and `/yl-cdk-monitoring` before calling this story done. Install from `youngliving/claude-plugins` if not available."

Skip entirely for plugin, personal, and general session types.

### 4. Scope Check

Read the `Scope:` field from the session file. If the field is missing or the session type is `general`, skip this step.

If the scope value is relative (no leading `/`, `~`, or drive letter), resolve it as: `local_cfg.projectRoot + "/" + scope_value` (read `local_cfg` from `~/.claude/config/<slug>.json`). For legacy sessions with absolute scope, use as-is.

Review file paths accessed or modified during this conversation. Any path not beginning with the resolved absolute scope is out-of-scope.

If out-of-scope work is found, warn but do not block:

```
Out-of-scope work detected — will be excluded from this checkpoint.

  Out-of-scope:
    - <file path>  (belongs in: <target slug> / <target session>)

  [1] Route to target inbox now (via /session:inbox)
  [2] Acknowledge only — I'll handle it manually
  [3] Skip
```

- **[1] Route:** Derive the target slug and session name from the file path, then invoke the `/session:inbox` flow with the out-of-scope item pre-populated as the content and target. The routing is never silent — the user sees and confirms it.
- **[2] Acknowledge:** Note the excluded work in the session summary's Open items but do not write to any inbox.
- **[3] Skip:** Continue without noting.

Continue with the checkpoint for in-scope work only.

### 5. History Entry

Compose a 1-sentence description of the work accomplished since the last checkpoint. This is the canonical record — write it as a complete thought that stands alone without conversation context (e.g. "Fixed NoteForm missing Tags/Collections and wired ExpeditionPicker into NoteDetail" not "finished the bugs").

Append to `<session_root>/_history.md` (create the file if it does not exist, with header `# History — <slug>`):

```
[YYYY-MM-DD @<handle>] <session-name> — <accomplished sentence>
```

This entry becomes the value for `Last worked on` in the session file.

### 5a. Jira Progress Comment *(story/cab only)*

Post a 1–2 sentence progress comment to the Jira story.

- **story:** story key = session name (e.g. `BPT2-6258`)
- **cab:** post to each story in `Related stories`

Content: current status + what was just accomplished + what's next. Business-readable — no file paths, class names, or token names. Example: *"Extended filter validation: all three input types now show required errors immediately on Add/Apply click. Committed and deploying to env6 for QA review."*

Before posting, check if the most recent Jira comment is from today and already covers this milestone — if so, skip.

**plugin / personal / general:** Skip.

### 5b. Epic Update *(story/cab only)*

If the session file has an `Epic` field, read `~/.claude/memory/epics/<key>.md` and prompt:

```
Epic update (<key>):
  Any cross-story decisions, resolved questions, or blockers to record?
  Yes — describe / No
```

- **Yes:** append to the epic file. For new decisions, add under `## Architecture Decisions` as `### [DECIDED] <title>` with a description and `- Source: <session-name> <date>`. For resolved Open Questions, move the row from the Open Questions table to `## Resolved` with the answer and `[YYYY-MM-DD <session-name>]` note.
- **No:** skip silently.

**plugin / personal / general:** Skip entirely.

### 6. Session Summary

**Plugin type only — if `plugin_reviewed` is missing, a legacy `yes`/`no` value, or its `MAJOR.MINOR` < current plugin.json version's:** before writing, prompt:
```
Plugin reviewed this session? (Yes — I ran the code-reviewer / No)
```
- **Yes:** set `plugin_reviewed: <current-plugin-version>` in the session file.
- **No:** leave as-is — reminder fires at next session start if minor version still differs.

Before writing, read the existing `Open items` from the session file. If there are any **non-`[inbox]`** items, display them and ask:

```
Open items — any complete?
  [1] <item>
  [2] <item>
  Mark done (enter numbers), or 'skip'
```

Remove confirmed-complete items from the Open items list before writing.

Write `<session_root>/<name>.md` with the current state:

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
- **Scope:** [scope path]   ← preserve from existing file; write relative if new (story/cab/personal: "./"; plugin: "<plugin-name>/"); omit for general
- **Status:** in-progress   ← always reset to in-progress at checkpoint
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

**Backward compat:** If the existing session file has a `Project:` field, preserve it on write. Do not add it to new sessions.

Print the summary to screen. After the summary block, display the last 5 entries from `_history.md` (all entries if fewer than 5):

```
Recent history (<slug>):
  <line 1 — most recent>
  <line 2>
  ...
```

### 7. In-Progress Inbox Check

For **plugin sessions**: read `<session_root>/_inbox_<name>.md`.
For **all other sessions**: read `<session_root>/_inbox.md`.

**Step A — In-progress items:** Scan the inbox file for entries with an `[in-progress — ...]` line.

**Step B — Legacy [inbox] items:** Read session `Open items`. Any `[inbox]` tag that has no corresponding in-progress entry in the inbox file was picked up under the previous system and already archived — include it as a legacy item.

If either category has items, display them together and ask:

```
In-progress inbox items — mark any done?
  [1] [in-progress since YYYY-MM-DD] <description from ## header>
  [2] [inbox legacy] <item text from Open items>
  Mark done (numbers, 'all', or 'skip')
```

For each **inbox-file item** (Step A) marked done:
1. Strip the `[in-progress — ...]` line from the entry.
2. Archive the full entry with `[DONE YYYY-MM-DD]` stamp prepended to `_inbox_<name>_archive.md`. Create archive with header `# Inbox Archive — <name>` if it does not exist. Preserve any `Work file:` reference in the archive entry.
3. Remove the entry from the inbox file. Rewrite inbox preserving header and remaining entries.
4. Remove the matching `[inbox] <item>` line from session `Open items`. Rewrite the session file.

For each **legacy item** (Step B) marked done:
- Remove the `[inbox] <item>` line from session `Open items`. No archive file changes needed.

If no in-progress or legacy items exist, skip silently.

### 7a. Pending Inbox Sweep

After handling in-progress items, check if any remaining pending items in the inbox were addressed this session without being formally picked up:

```
Inbox — any pending items addressed this session (outside in-progress tracking)?
  [1] [date] from <source> — <description>
  Numbers, 'none', or 'skip'
```

- **Marked done:** archive with `[DONE YYYY-MM-DD]` stamp, remove from inbox. Rewrite inbox.
- **Marked as picked up mid-session:** insert `[in-progress — <session-name>, YYYY-MM-DD]` in the inbox entry after the `## [date]...` header, add `[inbox] <item>` to Open items — will be handled at next checkpoint or finish.

If no pending items remain, skip silently.

**Auto-purge archive:** After handling inbox items, if the archive file exists, drop entries whose `[DONE YYYY-MM-DD]` date is more than 30 days before today. Rewrite with only retained entries (preserving the header line).

### 8. Work Log

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
