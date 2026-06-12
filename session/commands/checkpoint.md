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

### 4. Scope Scan *(plugin/story/cab/personal only)*

Read the `Scope:` field from the session file. If the field is missing or the session type is `general`, skip this step.

If the scope value is relative (no leading `/`, `~`, or drive letter), resolve it as: `local_cfg.projectRoot + "/" + scope_value` (read `local_cfg` from `~/.claude/config/<slug>.json`). For legacy sessions with absolute scope, use as-is.

Review file paths accessed or modified during this conversation. Any path not beginning with the resolved absolute scope is out-of-scope.

Record any out-of-scope items found — they will be surfaced in the batch block (Step 6) as warn-only questions.

### 5. History Entry

Compose a 1-sentence description of the work accomplished since the last checkpoint. Write it as a complete thought that stands alone without conversation context (e.g. "Fixed NoteForm missing Tags/Collections and wired ExpeditionPicker into NoteDetail" not "finished the bugs").

Append to `<session_root>/_history.md` via Bash — **do not Read the file first:**
```bash
[ -f "<session_root>/_history.md" ] || printf "# History — <slug>\n" > "<session_root>/_history.md"
printf "[YYYY-MM-DD @<handle>] <session-name> — <accomplished sentence>\n" >> "<session_root>/_history.md"
```

The composed entry is already in context and becomes the value for `Last worked on` in the session file — **do not re-read `_history.md` to retrieve it.**

### 5a. Jira Progress Comment *(story/cab only)*

Post a 1–2 sentence progress comment to the Jira story.

- **story:** story key = session name (e.g. `BPT2-6258`)
- **cab:** post to each story in `Related stories`

Content: current status + what was just accomplished + what's next. Business-readable — no file paths, class names, or token names. Example: *"Extended filter validation: all three input types now show required errors immediately on Add/Apply click. Committed and deploying to env6 for QA review."* **Never mention "create PR to master" or "merge to master" as what's next** — that belongs to the release plugin, not the session.

Before posting, check if the most recent Jira comment is from today and already covers this milestone — if so, skip.

**plugin / personal / general:** Skip.

### 5b. Epic Check *(story/cab only)*

If the session file has an `Epic` field, read `~/.claude/memory/epics/<key>.md` (to have it in context for the batch block). Note whether the epic file exists and whether it has a Confluence link. This check is silent — the user question goes in Step 6.

### 6. Checkpoint Batch

Gather all pending questions after silent work is done. If all items have forced defaults and no user input is possible, skip the batch block and proceed directly to Step 7. Otherwise, assemble and display the batch block, then wait for one reply. **Do not use AskUserQuestion.**

**Build the batch block in this order (omit items that don't apply):**

**(A) CDK/DynamoDB check** — include if `type` is story or cab and a commit was just made or is about to be:
```
  (N) CDK/DynamoDB patterns verified?    not-applicable / yes / remind
```

**(B) Out-of-scope items** — include one per item found in Step 4:
```
  (N) Out-of-scope: "<path>" → route to <target>?    skip / route / note
```

**(C) Epic update** — include if type is story/cab and session file has an `Epic` field:
```
  (N) Epic update (<key>) — decisions or blockers to record?    skip / yes
```
If the epic file has a Confluence link, include the next item immediately after:
```
  (N+1) Push epic update to linked Confluence page?    skip / yes
```

**(D) Plugin reviewed** — include if type is plugin and `plugin_reviewed` is missing, a legacy value, or MAJOR.MINOR differs from current:
```
  (N) Plugin reviewed? (last: v<stored>, current: v<current>)    skip / yes
```

**(E) Open items** — include if there are non-`[inbox]` Open items in the session file. List them numbered:
```
  (N) Open items done?
        1  [item one text]
        2  [item two text]
     skip / all / <number(s)>
```

**(F) In-progress inbox items** — for plugin sessions: `_inbox_<name>.md`; others: `_inbox.md`. Include one per in-progress item:
```
  (N) Inbox [in-progress]: "<description>"    keep / done
```

**(G) Legacy [inbox] Open items** — any `[inbox]` tag in Open items with no corresponding in-progress inbox entry:
```
  (N) Open item [inbox legacy]: "<text>"    keep / done
```

**(H) Pending inbox sweep** — include one per pending (non-in-progress) inbox item if any were present:
```
  (N) Inbox pending: "<description from source/session>" — addressed this session?    nothing / done / picked-up
```

**Assembled block example:**
```
  (1) CDK/DynamoDB patterns verified?    not-applicable / yes / remind
  (2) Out-of-scope: "release/commands/create.md" → route to release?    skip / route / note
  (3) Epic update (BPT2-6300) — decisions or blockers?    skip / yes
  (4) Plugin reviewed? (last: v1.36, current: v1.40)    skip / yes
  (5) Open items done?
        1  Fix scope guard edge case
        2  Add test coverage for spawn flow
     skip / all / <number(s)>
  (6) Inbox [in-progress]: "Update session tests"    keep / done
  (7) Inbox pending: "Review DynamoDB schema" — addressed?    nothing / done / picked-up

Reply with overrides or "go".
```

**Parsing:** `go` accepts all defaults. Examples: `4 yes`, `5 all`, `5 1 2`, `6 done 4 yes`, `3 yes 4 yes`.

**Applying answers:**

*(A) CDK check:*
- **not-applicable / yes:** proceed silently.
- **remind:** surface note after the batch: "Run `/yl-cdk-migration` and `/yl-cdk-monitoring` before calling this story done."

*(B) Out-of-scope:*
- **route:** invoke `/session:inbox` flow with the out-of-scope item pre-populated. The routing is never silent — user sees and confirms before inbox write.
- **note:** record the excluded work in Open items but do not write to any inbox.
- **skip:** continue without noting.

*(C) Epic update:*
- **yes:** after the batch is fully processed, ask as a follow-up: "What should be recorded? (decisions, resolved questions, or blockers)" — append to the epic file: new decisions under `## Architecture Decisions` as `### [DECIDED] <title>`; resolved questions moved to `## Resolved` with answer and `[YYYY-MM-DD <session-name>]` note. This follow-up stop is justified — content couldn't be asked before knowing the answer was "yes".
- **skip:** no changes to epic file.
- **Confluence sync (C+1):** only applies if epic update = yes. **yes** → push epic memory update to the linked Confluence page after applying epic changes. **skip** → no sync.

*(D) Plugin reviewed:*
- **yes:** update `Plugin reviewed: <current-version>` in the session file.
- **skip:** leave as-is.

*(E) Open items:*
- **all:** mark all non-`[inbox]` Open items as done — remove from list.
- **<number(s)>:** mark those specific items done — remove them.
- **skip:** keep all open.

*(F) In-progress inbox items:*
- **done:** strip the `[in-progress — ...]` line, archive with `[DONE YYYY-MM-DD]` stamp to `_inbox_<name>_archive.md` (create with header `# Inbox Archive — <name>` if needed). Remove entry from inbox. Remove matching `[inbox] <item>` from Open items.
- **keep:** no change.

*(G) Legacy [inbox] items:*
- **done:** remove `[inbox] <item>` from Open items. No archive changes.
- **keep:** no change.

*(H) Pending inbox sweep:*
- **done:** archive with `[DONE YYYY-MM-DD]`, remove from inbox. Rewrite inbox.
- **picked-up:** insert `[in-progress — <session-name>, YYYY-MM-DD]` after `## [date]...` header; add `[inbox] <item>` to Open items.
- **nothing:** skip.

**Auto-purge archive:** After handling inbox items, if the archive file exists, drop entries whose `[DONE YYYY-MM-DD]` date is more than 30 days before today. Rewrite with only retained entries (preserving the header line).

### 7. Session Summary

**Before writing — tag any untagged items:** For each Open item that does not already start with `[YYYY-MM-DD @`, prepend `[YYYY-MM-DD @<handle>] `. Preserve existing tags as-is.

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
- **created-by:** @<original-handle>   ← read from existing file; preserve as-is — never overwrite
- **Title:** [Jira summary]   ← story/cab only; omit for other types
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Scope:** [scope path]   ← preserve from existing file; write relative if new (story/cab/personal: "./"; plugin: "<plugin-name>/"); omit for general
- **Status:** in-progress   ← always reset to in-progress at checkpoint
- **Branch:** [branch or "n/a"]
- **Last worked on:** [the entry composed and written in Step 5 — use that value directly; do not re-read _history.md]
- **Open items:**
  - [YYYY-MM-DD @<handle>] <item text>   ← all items tagged; "none" if empty
- **Next steps:**
  - [YYYY-MM-DD @<handle>] <next step>   ← array format; "none" if no next step
- **Loaded memories:**   ← preserve existing entries exactly as-is; omit the field if not present. Written by the memory plugin
  - <name>  [<label>]
- **Commits:**   ← preserve existing entries exactly as-is; omit the field if not present. Written by session:commit
  - [YYYY-MM-DD] <short-sha> — <commit subject>
- **Plugin reviewed:** <version>   ← plugin type only; write current plugin.json version when marking reviewed; omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Post-deployment checks:**   ← story type only; preserve existing value exactly as-is; omit if field not present
  - [ ] <check description>
  - [x] <acknowledged check description>
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
- **linked_sessions:** [<session-name>, ...]   ← preserve as-is; omit if not present
```

**Backward compat:** If the existing session file has a `Project:` field, preserve it on write. Do not add it to new sessions. If the existing file has `- **Next step:** <text>` (scalar), re-write as `- **Next steps:**` array with the item tagged `[today @<handle>]`. `Loaded memories:` and `Commits:` are preserve-only here — checkpoint never authors them (the memory plugin and session:commit do); carry existing values forward unchanged.

**After writing — update approved-hash (repo sessions only):** If `session_root` is inside a repo, recompute the hash of the written file and overwrite `~/.claude/memory/sessions/<slug>/<name>.approved-hash`:
```bash
git hash-object "<session_root>/<name>.md" > ~/.claude/memory/sessions/<slug>/<name>.approved-hash
```

**Update `_index.md`:** Read `<session_root>/_index.md` — create with header `# Session Index — <slug>` + `# name | created-by | created-date | updated-by | updated-date | status | title` if it does not exist. Find the line for `<name>`: extract `@created-by` (col 2) and `created-date` (col 3) to preserve them; if no existing line, use `@<handle>` and `<today>` for both. Replace or append: `<name> | @<created-by> | <created-date> | @<handle> | <today> | in-progress | <title-or-dash>`.

Print the summary to screen. After the summary block, display the last 5 entries from `_history.md` via Bash — **do not Read the full file:**
```bash
tail -n 5 "<session_root>/_history.md"
```

```
Recent history (<slug>):
  <line 1 — most recent>
  <line 2>
  ...
```

### 8. Work Log

Append to `~/.claude/memory/worklog/<YYYY-MM-DD>.md` via Bash — **do not Read the file first.** Worklog is append-only; existing content is never examined.

```bash
mkdir -p ~/.claude/memory/worklog
cat >> ~/.claude/memory/worklog/<YYYY-MM-DD>.md << 'ENTRY'
[entry content here]
ENTRY
```

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
