---
name: finish
description: End-of-day close — full checklist; Jira, Teams, Confluence, and browser steps run conditionally by session type.
---

# Session Finish

Full end-of-day close. Runs the complete checklist to ensure nothing is left behind.

## Instructions

### 0. Read Session Context

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).

Determine the session name from conversation context:
1. Look back at the current conversation for the most recent "Resuming `<name>`" line (from session:start) OR "Switching to `<name>`" line (from session:switch). Use whichever is most recent.
2. If neither is found in this conversation, fall back to reading `~/.claude/memory/sessions/<slug>/_active` as a hint.
3. If neither is available, ask the user: "Which session are you finishing?"

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
Session Finish — <name> (<type>)
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

Report anything that could be lost. If uncommitted changes exist: "Want to commit before closing?"

If clean: "Git: clean"

### 3. Memory

Review the conversation for anything worth saving:
- Feedback, corrections, or rules established
- Workflow or convention changes
- Project or session state updates
- Anything non-obvious that future sessions should know

Save what's missing. Report: "Saved: [list]" or "Memory: nothing new to save."

### 4. Jira Update *(story/cab only)*

**plugin / personal / general:** Skip this step entirely — do not read the reference.

**story / cab:** Read `references/finish-story-cab.md` (Step 4 section) and perform the Jira actions silently before the batch block. (The reference is loaded once here and also supplies the Step 6 prep additions, the Step 7 story/cab slot bodies, and the Step 9 post-deployment checks — keep it in context for the rest of this finish.)

### 5. Scope Scan

Read the `Scope:` field from the session file. If the field is missing or the session type is `general`, skip this step.

If the scope value is relative, resolve it as: `local_cfg.projectRoot + "/" + scope_value` (read `local_cfg` from `~/.claude/config/<slug>.json`). For legacy sessions with absolute scope, use as-is.

Review file paths that were accessed or modified during this conversation (Read, Edit, Write, Bash file operations). Any path that does not begin with the resolved absolute scope is out-of-scope.

**If out-of-scope items found — hard block.** Show prominently before the batch block and wait (Pattern 5 — finish is a hard block, not a warn):

```
Cross-scope work detected — cannot close this session cleanly.

  Out-of-scope changes:
    · <file path>  (belongs in: <target slug> / <target session>)

Resolve before closing:
  (1) Route to <target> inbox?    yes / note / cancel
```

- **yes (route):** invoke `/session:inbox` flow with the out-of-scope item pre-populated. User sees and confirms before inbox write. Once resolved, continue to batch block.
- **note:** record excluded work in Open items, no inbox write. Continue.
- **cancel:** stop. Do not write session summary or deactivate.

Only proceed to the batch block once all flagged items are resolved.

### 6. Pre-Batch Preparation (Silent)

Before assembling the batch, gather contextual data needed to build the batch items. **Run all applicable reads in parallel — issue them as a single batch before processing any result.**

Universal reads (all types):

1. **Inbox file:** read `<session_root>/_inbox_<name>.md` (plugin) or `<session_root>/_inbox.md` (others). Categorize items as in-progress or pending.
2. **Plugin version:** if type is plugin, read current version from `plugin.json`.
3. **Loaded memories:** read the session file's `- **Loaded memories:**` field. If it has entries, note them for the validate-shape of batch item (A2). If absent or empty, (A2) takes its capture-only shape — it is always presented.

**story / cab only:** also issue the type-specific prep reads (epic file, story doc path, browser, Teams guide pre-fetch) from `references/finish-story-cab.md` (Step 6 section) in this same parallel batch.

### 7. Finish Batch

Gather all pending questions and present as **one batched block**. Output and wait (Pattern 2). **Do not use AskUserQuestion.**

**Batch skeleton — canonical slot order.** Assemble the numbered list by walking these slots in order, omitting any whose condition isn't met, and assigning each surviving slot the next running number `(N)`. Universal slots (and the plugin-only F) are defined inline below; story/cab slot bodies live in `references/finish-story-cab.md` (already loaded in Step 4 for story/cab sessions). For plugin / personal / general sessions the story/cab slots are simply absent — never read the reference for them.

| Slot | Item | Applies to | Body |
|------|------|-----------|------|
| A  | CDK/DynamoDB check            | story/cab | `references/finish-story-cab.md` |
| A2 | Memory validation + capture   | **all**   | inline below |
| B  | Epic update (+B+1 Confluence) | story/cab | `references/finish-story-cab.md` |
| B2 | Epic validation for CAB       | cab       | `references/finish-story-cab.md` |
| C  | Confluence story page         | story/cab | `references/finish-story-cab.md` |
| D  | Story doc                     | story     | `references/finish-story-cab.md` |
| E  | Browser                       | story     | `references/finish-story-cab.md` |
| F  | Plugin reviewed               | plugin    | inline below |
| G  | Open items                    | all       | inline below |
| H  | In-progress inbox items       | all       | inline below |
| I  | Legacy [inbox] Open items     | all       | inline below |
| J  | Pending inbox sweep           | all       | inline below |
| K  | Teams update                  | story/cab | `references/finish-story-cab.md` |

**Inline slot bodies (universal + plugin):**

**(A2) Memory validation + capture** — **always include this item** (for any session type). This closes the context-rot loop and provides the finish-time opportunity to record project knowledge. Two shapes:

- **If the session has loaded memories** (from Step 6 item 3): every memory that influenced this session's work gets an accuracy check, plus the option to capture a new one.
  ```
  (N) Loaded memories (M) — validate for accuracy, and capture anything new?    skip / review / new / both
  ```
- **If no memories were loaded:** offer capture only — especially valuable when work touched an area with no memory yet.
  ```
  (N) Capture anything from this session as a project memory?    skip / new
  ```

**(F) Plugin reviewed** — plugin type only, if `plugin_reviewed` is missing, a legacy value, or MAJOR.MINOR differs:
```
  (N) Plugin reviewed? (last: v<stored>, current: v<current>)    skip / yes
```

**(G) Open items** — if there are non-`[inbox]` Open items:
```
  (N) Open items done?
        1  [item one text]
        2  [item two text]
     skip / all / <number(s)>
```

**(H) In-progress inbox items** — one per item found in Step 6:
```
  (N) Inbox [in-progress]: "<description>"    keep / done
```

**(I) Legacy [inbox] Open items** — any `[inbox]` tag with no corresponding in-progress inbox entry:
```
  (N) Open item [inbox legacy]: "<text>"    keep / done
```

**(J) Pending inbox sweep** — one per pending inbox item:
```
  (N) Inbox pending: "<description>" — addressed this session?    nothing / done / picked-up
```

**Assembled block example (story type):**
```
  (1) CDK/DynamoDB patterns verified?    not-applicable / yes / remind
  (2) Loaded memories (2) — validate for accuracy, and capture anything new?    skip / review / new / both
  (3) Epic update (BPT2-6300) — mark story done and record final notes?    skip / yes
  (4) Push epic update to Confluence architecture page?    skip / yes
  (5) Update Confluence page for this story?    skip / yes
  (6) Story doc — update existing?    skip / yes
  (7) Open items done?
        1  Fix scope guard edge case
     skip / all / 1
  (8) Inbox [in-progress]: "Update session tests"    keep / done
  (9) Inbox pending: "Review DynamoDB schema" — addressed?    nothing / done / picked-up
  (10) Post closing update to BPT2-6258 — Shopify Member Agreement?    skip / yes

Reply with overrides or "go".
```

**Parsing:** `go` accepts all defaults. Parse freely: `3 yes 6 yes 10 yes`, `all skip`, `8 done 10 yes`, etc.

**Applying answers:**

For **story/cab slots (A, B, B2, C, D, E, K)** the apply-logic lives in `references/finish-story-cab.md` (Step 7 sections) — already in context. The universal/plugin slots are applied here:

*(A2) Memory validation + capture:* (run after the batch is processed — these are justified follow-ups since per-memory dispositions and new-memory content can't be known in advance)
- **review:** run the staleness check (scoped mode) from the memory plugin's `references/staleness-check.md` against the session's loaded memories. Present only the **flagged** files (unresolved code references) as a batch — clean loaded memories are kept automatically and skipped. Apply per `/memory:groom` Steps 2–3 (scoped). If all loaded memories are clean: skip the review, surface only the capture offer. Any memory deleted is dropped from the session's `Loaded memories:` field in Step 9. If the memory plugin is not installed, fall back to inline review: read each file, show it, and ask `keep / update / delete`.
- **new:** run the memory plugin's `/memory:save` flow — infer the feature area from this session's work, propose a `feature:X/Y` label + name + body, and on confirm write the file, update `MEMORY.md`, and add it to the session's `Loaded memories:` field. Offer to capture more than one if the session spanned distinct areas. If the memory plugin is not installed, fall back to writing the file inline using the `feature:X/Y` convention.
- **both:** run review first, then capture.
- **skip:** leave memories untouched. (Skipping review means nothing needed revision; skipping capture means nothing new to record.)

*(F) Plugin reviewed:*
- **yes:** update `Plugin reviewed: <current-version>` in the session file.
- **skip:** leave as-is.

*(G) Open items:*
- **all:** remove all non-`[inbox]` items from the list.
- **<number(s)>:** remove those items.
- **skip:** keep all open.

*(H) In-progress inbox items:*
- **done:** strip `[in-progress — ...]`, archive with `[DONE YYYY-MM-DD]` to `_inbox_<name>_archive.md`, remove from inbox, remove `[inbox] <item>` from Open items.
- **keep:** no change. Will carry as in-progress to next session.

*(I) Legacy [inbox] items:*
- **done:** remove `[inbox] <item>` from Open items.
- **keep:** no change.

*(J) Pending inbox sweep:*
- **done:** archive with `[DONE YYYY-MM-DD]`, remove from inbox.
- **picked-up:** insert `[in-progress — <session-name>, YYYY-MM-DD]` after `## [date]...` header; add `[inbox] <item>` to Open items.
- **nothing:** skip.

**Auto-purge archive:** After handling inbox items, if the archive file exists, drop entries whose `[DONE YYYY-MM-DD]` date is more than 30 days before today. Rewrite with only retained entries (preserving the header line).

### 8. History Entry

Compose a 1-sentence description of the work accomplished this session. Write it as a complete thought that stands alone without conversation context.

Append to `<session_root>/_history.md` via Bash — **do not Read the file first:**
```bash
[ -f "<session_root>/_history.md" ] || printf "# History — <slug>\n" > "<session_root>/_history.md"
printf "[YYYY-MM-DD @<handle>] <session-name> — <accomplished sentence>\n" >> "<session_root>/_history.md"
```

The composed entry is already in context and becomes the value for `Last worked on` in the session file — **do not re-read `_history.md` to retrieve it.**

### 9. Session Summary

**Before writing — tag any untagged items:** For each Open item that does not already start with `[YYYY-MM-DD @`, prepend `[today @<handle>] `. Preserve existing tags as-is.

**Story type only — post-deployment checks:** Run the post-deployment-checks prompt from `references/finish-story-cab.md` (Step 9 section, already in context). Skip entirely for non-story types.

**Derive `Next steps` — do not ask.** Use only mine-tagged items. Check in order:
1. Remaining items in `<session_root>/_inbox_<name>.md` (pending or in-progress) → `[today @<handle>] See inbox — N items pending`
2. Non-`[inbox]`-tagged Open items → use the first mine-tagged item's text as the next step
3. Story/CAB type → check Jira status and branch state for a concrete action. **Never suggest "create PR to master", "merge to master", or any variant.** If the story is otherwise complete: "Hand off to /release:create when ready to deploy."
4. If none of the above apply → ask: "What's the first thing to pick up next time? (or 'skip')"

After deriving, offer routing for a **new** item as a brief inline prompt:
```
Route next step → inbox (ready) / backlog (defer) / skip (keep as-is)
```
- **inbox:** invoke `/session:inbox` targeting this same session. Add `[today @<handle>] See inbox` to Next steps.
- **backlog:** write to `<session_root>/_backlog_<name>.md` (plugin) or `<session_root>/_backlog.md`. Set Next steps to `none`.
- **skip:** keep the derived Next steps as-is.

Write `<session_root>/<name>.md` with the final state:

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
- **Scope:** [scope path]   ← preserve from existing file; write relative if new; omit for general
- **Status:** completed
- **Branch:** [branch or "n/a"]
- **Last worked on:** [the entry composed and written in Step 8 — use that value directly; do not re-read _history.md]
- **Open items:**
  - [YYYY-MM-DD @<handle>] <item text>   ← all items tagged; "none" if empty
- **Next steps:**
  - [YYYY-MM-DD @<handle>] <next step>   ← array format; "none" if no next step
- **Loaded memories:**   ← preserve surviving entries (drop any deleted during Step 7 memory validation); omit the field if none
  - <name>  [<label>]
- **Commits:**   ← preserve existing entries exactly as-is; omit the field if not present. Written by session:commit
  - [YYYY-MM-DD] <short-sha> — <commit subject>
- **Plugin reviewed:** <version>   ← plugin type only; omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Post-deployment checks:**   ← story type only; omit if field not present
  - [ ] <check description>
  - [x] <acknowledged check description>
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
- **linked_sessions:** [<session-name>, ...]   ← preserve as-is; omit if not present
```

**Backward compat:** If the existing session file has a `Project:` field, preserve it. If `- **Next step:** <text>` (scalar), re-write as `- **Next steps:**` array tagged `[today @<handle>]`. `Commits:` is preserve-only at finish (written by session:commit). `Loaded memories:` carries forward minus anything deleted during the Step 7 memory-validation item.

**After writing — update approved-hash (repo sessions only):** Recompute hash and overwrite `~/.claude/memory/sessions/<slug>/<name>.approved-hash`:
```bash
git hash-object "<session_root>/<name>.md" > ~/.claude/memory/sessions/<slug>/<name>.approved-hash
```

**Update `_index.md`:** Find the line for `<name>`: extract `@created-by` and `created-date` to preserve. Replace or append: `<name> | @<created-by> | <created-date> | @<handle> | <today> | completed | <title-or-dash>`.

**General sessions only:** Also check `~/.claude/memory/sessions/<slug>/<name>/` — if notes, decisions, or outputs were produced today, ensure they are written there before closing.

Print the summary to screen as the final output.

### 10. Work Log

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

### 11. Deactivate Session

Remove the active marker so no future conversation inherits stale state. `_active` is always local — do not touch the repo session directory for this step:

```bash
rm -f ~/.claude/memory/sessions/<slug>/_active
```

On PowerShell use: `Remove-Item -ErrorAction SilentlyContinue ~/.claude/memory/sessions/<slug>/_active`
