---
name: checkpoint
description: Mid-session save — git scan, memory, update session state. Fast, no prompts.
---

# Session Checkpoint

Quick mid-session save. Captures current state so nothing is lost if the session is interrupted.

## Instructions

### 0. Read Session Context

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (`references/path-resolution.md`).

Determine the session name from conversation context:
1. Look back at the current conversation for the most recent "Resuming `<name>`" line (from session:start) OR "Switching to `<name>`" line (from session:switch). Use whichever is most recent.
2. If neither is found in this conversation, fall back to reading `~/.claude/memory/sessions/<slug>/_active` as a hint.

**Session guard (command-level enforcement — acp-ajudd#1).** `checkpoint` saves the active session, so a session must exist. If neither the conversation context nor `~/.claude/memory/sessions/<slug>/_active` yields a session name, **stop cleanly** — do not ask, do not treat as a general session, do not proceed:

```
No session established for <slug>. Run /session:start first.
```

Editing files is never blocked; the session commands are what require a session. (`start` / `refine` and read-only views are exempt.)

Read `<session_root>/<name>.md` and extract:
- `type` (plugin / story / cab / personal / general)
- `name`
- `title` (story/cab only — may be absent in older session files; treat as empty string if missing)
- `teams_chat`
- `branch`

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

**Status → the session file, not other living docs (Session Skill § Work ownership).** Live/ephemeral status — dated events, test counts, blockers, next action — is recorded in the session file here. Do **not** mirror it into a contract/requirements doc (spec, ADR, design doc, ticket body — all developer-owned **work**) on your own initiative; those are edited only on explicit direction. Link to the work; don't duplicate its content or push status into it.

### 4. Scope Scan *(plugin/story/cab/personal only)*

Read the `Scope:` field from the session file. If the field is missing or the session type is `general`, skip this step.

The `Scope:` field may hold **one path or a comma-separated set** (a multi-plugin feature declares every plugin dir it touches — acp-ajudd#54). Split on `,`, trim each entry, and resolve each: if an entry is relative (no leading `/`, `~`, or drive letter), resolve it as `local_cfg.projectRoot + "/" + entry` (read `local_cfg` from `~/.claude/config/<slug>.json`); for legacy sessions with absolute scope, use as-is.

Review file paths accessed or modified during this conversation. A path is in-scope if it begins with **any** of the resolved scope paths; only paths under **none** of them are out-of-scope. A multi-plugin feature's own declared surface is in-scope by design — only edits outside the item's declared plugin set are the leakage this scan is for.

Record any out-of-scope items found — they will be surfaced in the batch block (Step 6) as warn-only questions.

### 5. History Entry

Compose a 1-sentence description of the work accomplished since the last checkpoint. Write it as a complete thought that stands alone without conversation context (e.g. "Fixed NoteForm missing Tags/Collections and wired ExpeditionPicker into NoteDetail" not "finished the bugs").

Append to `<session_root>/_history.md` via Bash — **do not Read the file first:**
```bash
[ -f "<session_root>/_history.md" ] || printf "# History — <slug>\n" > "<session_root>/_history.md"
printf "[YYYY-MM-DD @<handle>] <session-name> — <accomplished sentence>\n" >> "<session_root>/_history.md"
```

The composed entry is already in context and becomes the value for `Last worked on` in the session file — **do not re-read `_history.md` to retrieve it.**

**`_history.md` and `_index.md` are derived caches, gitignored in repo-based sessions and never committed (acp-ajudd#49 — see Session Skill § The committed-sessions model).** Writing to them here is a local cache update, not a change to commit. Checkpoint never creates a git commit, so nothing stages — but the discipline holds at commit/finish: fold session state into a meaningful commit, and never quote another team's secrets/findings/PII into a committed session file (reference by ticket/PR).

### 5a / 5b. Jira Progress Comment + Epic Check *(story/cab only)*

**plugin / personal / general:** Skip both — do not read the reference.

**story / cab:** Read `references/checkpoint-story-cab.md` and perform Step 5a (post the Jira progress comment) and Step 5b (silent epic check) per its instructions. (Loaded once here; it also supplies the Step 6 story/cab slot bodies — keep it in context for the rest of this checkpoint.)

### 6. Checkpoint Batch

Gather all pending questions after silent work is done. If all items have forced defaults and no user input is possible, skip the batch block and proceed directly to Step 7. Otherwise, assemble and display the batch block, then wait for one reply. **Do not use AskUserQuestion.**

**CDK detection (story/cab only — run once before building the batch):**
```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
CDK_PRESENT=""
[ -n "$REPO_ROOT" ] && { [ -f "$REPO_ROOT/cdk.json" ] || [ -d "$REPO_ROOT/cdk" ]; } && CDK_PRESENT=true
```

**Batch skeleton — canonical slot order.** Build the numbered list by walking these slots in order, omitting any whose condition isn't met, and assigning each surviving slot the next running number `(N)`. Universal slots (and the plugin-only D) are defined inline below; story/cab slot bodies live in `references/checkpoint-story-cab.md` (already loaded in Step 5a/5b for story/cab sessions). For plugin / personal / general sessions the story/cab slots are simply absent — never read the reference for them.

| Slot | Item | Applies to | Body |
|------|------|-----------|------|
| A | CDK/DynamoDB check          | story/cab + CDK_PRESENT | `references/checkpoint-story-cab.md` |
| B | Out-of-scope items          | all (with scope) | inline below |
| C | Epic update (+C+1 Confluence) | story/cab | `references/checkpoint-story-cab.md` |
| D | Plugin reviewed             | plugin    | inline below |
| E | Open items                  | all       | inline below |
| F | In-progress inbox items     | all       | inline below |
| G | Legacy [inbox] Open items   | all       | inline below |
| H | Pending inbox sweep         | all       | inline below |

**Inline slot bodies (universal + plugin):**

**(B) Out-of-scope items** — include one per item found in Step 4:
```
  (N) Out-of-scope: "<path>" → route to <target>?    skip / route / note
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

**(F) In-progress `work` entries** — **read the inbox fresh at checkpoint time (acp-ajudd#6), never a session-start snapshot.** File is type-aware: **plugin / personal → the canonical `_inbox.md`** (item-driven — there is no per-session `_inbox_<name>.md`); **story / cab / general → `_inbox_<name>.md`**. Count/list **by `## <id>` header lines** and **skip the `> [type: … · status: …]` metadata line** under each (legacy `> [status: …]` tolerated — never miscount it). **Exclude `capture`-type entries** (acp-ajudd#10) — they are not pickup work; they're read/archived only on request (§ Captures inbound). Include one per in-progress `work` entry:
```
  (N) [<id>] Inbox [in-progress]: "<description>"    keep / done
```

**(G) Legacy [inbox] Open items** — any `[inbox]` tag in Open items with no corresponding in-progress inbox entry:
```
  (N) Open item [inbox legacy]: "<text>"    keep / done
```

**(H) Pending inbox sweep** — include one per pending (non-in-progress) inbox item if any were present (single-line provenance form — see `references/inbox-convention.md`):
```
  (N) [<id>] Inbox pending: "<description>"  ·  ↳ <session> (<type>) — addressed this session?    nothing / done / picked-up
```
Lead with the item's stable `[<id>]` (omit for legacy items that have none). Include `<slug>` in the `↳` when the item's source repo differs from the current slug; drop it when same-repo; omit `(<type>)` for legacy items.

**Assembled block example:**
```
  (1) CDK/DynamoDB patterns verified?    not-applicable / yes / remind
  (2) Out-of-scope: "release/commands/create.md" → route to release?    skip / route / note
  (3) Epic update (BPT2-6300) — decisions or blockers?    skip / yes
  (4) Open items done?
        1  Fix scope guard edge case
        2  Add test coverage for spawn flow
     skip / all / <number(s)>
  (5) [vo-ajudd#4] Inbox [in-progress]: "Update session tests"    keep / done
  (6) [vo-ajudd#12] Inbox pending: "Review DynamoDB schema"  ·  ↳ BPT2-6258 (story) — addressed?    nothing / done / picked-up

Reply with overrides or "go".
```

**Parsing:** `go` accepts all defaults. Examples: `3 yes`, `4 all`, `4 1 2`, `5 done 3 yes`.

**Applying answers:**

For **story/cab slots (A, C)** the apply-logic lives in `references/checkpoint-story-cab.md` (Step 6 sections) — already in context. The universal/plugin slots are applied here:

*(B) Out-of-scope:*
- **route:** invoke `/session:inbox` flow with the out-of-scope item pre-populated. Choosing `route` IS the go-ahead — `/session:inbox` writes directly and surfaces the `Sent inbox item <id> to <target> inbox` line (free rein + visible, never silent — acp-ajudd#5; no separate pre-write approval).
- **note:** record the excluded work in Open items but do not write to any inbox.
- **skip:** continue without noting.

*(D) Plugin reviewed:*
- **yes:** update `Plugin reviewed: <current-version>` in the session file.
- **skip:** leave as-is.

*(E) Open items:*
- **all:** mark all non-`[inbox]` Open items as done — remove from list.
- **<number(s)>:** mark those specific items done — remove them.
- **skip:** keep all open.

*(F) In-progress inbox items:*
- **done:** strip the `[in-progress — ...]` line, archive with `[DONE YYYY-MM-DD]` stamp, remove entry from inbox, remove matching `[inbox] <item>` from Open items. **Archive file is type-aware:** `_inbox_archive.md` for plugin / personal (item-driven), `_inbox_<name>_archive.md` for story / cab / general (create with the matching `# Inbox Archive — …` header if needed).
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

**Frontmatter:** for `plugin` and `personal` types, write `type:` and `status:` keys alongside `updated:`, kept in sync with the body bullets. `status:` (consumed by the listing renderer to hide completed sessions) is `in-progress` at checkpoint; `type:` records the session's kind. For `story` / `cab` / `general`, write only `updated:` (preserve any existing extra keys as-is). **No `mode` key — a session is always a coding session (acp-ajudd#16); if an older file still carries `mode:`, simply drop it (do not preserve it).**

```
---
updated: [today's date]
type: [type]            ← plugin/personal only
status: in-progress     ← plugin/personal only; always reset to in-progress at checkpoint
---

# Session State — <name>

- **Type:** [type]
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
