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

**Session guard (command-level enforcement — acp-ajudd#1).** `finish` closes the active session, so a session must exist. If neither the conversation context nor `~/.claude/memory/sessions/<slug>/_active` yields a session name, **stop cleanly** — do not ask, do not treat as a general session, do not proceed:

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

Report anything that could be lost.

**Non-plugin types:** if uncommitted changes exist, ask "Want to commit before closing?"

**Plugin type:** do NOT prompt for a separate commit here. Uncommitted changes and unpushed local commits (from `session:commit`) are *expected* at plugin finish — they are the work being shipped, and the **deploy step (Step 11) commits, bumps, pushes, and reinstalls them** (deactivation, Step 12, is the terminal action after it). Report them as informational only, e.g. "Uncommitted changes + N local commits — will ship in the deploy step," never as at-risk. This is the finish half of the polymorphic lifecycle: for plugins, finish = the deploy.

If clean: "Git: clean" (for plugin, this means there is nothing to deploy — note that Step 11 will be a no-op).

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

- **yes (route):** invoke `/session:inbox` flow with the out-of-scope item pre-populated. Choosing `route` IS the go-ahead — `/session:inbox` writes it directly and surfaces the `Sent inbox item <id> to <target> inbox` line (free rein + visible, never silent — acp-ajudd#5; no separate pre-write approval). Once routed, continue to batch block.
- **note:** record excluded work in Open items, no inbox write. Continue.
- **cancel:** stop. Do not write session summary or deactivate.

Only proceed to the batch block once all flagged items are resolved.

### 6. Pre-Batch Preparation (Silent)

Before assembling the batch, gather contextual data needed to build the batch items. **Run all applicable reads in parallel — issue them as a single batch before processing any result.**

Universal reads (all types):

1. **Inbox file — fresh read at close (acp-ajudd#6).** The recap must reflect the *live* inbox, not a snapshot taken at session start — a concurrent planning session or another terminal may have added items while this session ran.
   - **plugin / personal (item-driven):** read the **canonical `<session_root>/_inbox.md` fresh, now** — do NOT reuse a session-start snapshot, and do NOT look for a per-session `_inbox_<name>.md` (item-driven sessions are fold-then-delete; that file does not exist for them). **Exclude** any item this session folded at pickup or marked completed; **include** everything else currently in the file (so concurrently-added items appear).
   - **story / cab / general:** read the per-session `<session_root>/_inbox_<name>.md` (these are not item-driven — a per-session handoff file is correct). Same fresh-read discipline.
   - **Parser (both):** count and list **by the `## <id> · [date…]` header lines**. **Skip the `> [type: … · status: …]` metadata line** under each header — it is item metadata (shipped v1.57.0, acp-ajudd#9), not a separate item and not body content; never miscount it. Tolerate legacy items with no `<id>` prefix and no metadata line. **Exclude `type: note` / `type: data` mailbox items** from the pickup sweep (acp-ajudd#10) — they are not work to close out; they're read/archived only on request (§ Mailbox). Categorize each surviving **story** item as in-progress (has an `[in-progress — …]` marker) or pending.
2. **Plugin version:** if type is plugin, read current version from `plugin.json`.
3. **Loaded memories:** read the session file's `- **Loaded memories:**` field. If it has entries, note them for the validate-shape of batch item (A2). If absent or empty, (A2) takes its capture-only shape — it is always presented.

**story / cab only:** also issue the type-specific prep reads (epic file, story doc path, browser, Teams guide pre-fetch) from `references/finish-story-cab.md` (Step 6 section) in this same parallel batch.

**CDK detection (story/cab only — run once before building the batch):**
```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
CDK_PRESENT=""
[ -n "$REPO_ROOT" ] && { [ -f "$REPO_ROOT/cdk.json" ] || [ -d "$REPO_ROOT/cdk" ]; } && CDK_PRESENT=true
```
If `REPO_ROOT` can't be resolved, leave `CDK_PRESENT` unset and default to showing Slot A (no silent loss of the gate for real infra work).

### 7. Finish Batch

Gather all pending questions and present as **one batched block**. Output and wait (Pattern 2). **Do not use AskUserQuestion.**

**Plugin type — smart defaults (finish = done, ship it).** For a plugin session Aaron is planner + coder + tester + QA in one seat, so finish should NOT interrogate him slot-by-slot. Claude owns the routine judgment calls and only surfaces genuine exceptions; a bare `go` performs the full sensible close. This is the opposite of story/cab, whose batch stays prompt-heavy **by design** (external Jira/CAB/QA gates that Claude cannot decide). Concretely, for plugin type:

- **Memory capture (A2):** do not ask `skip / new`. Claude reviews the session itself, decides whether there is project/session knowledge worth saving, and captures it — reporting the outcome (`Captured: <name>` or `Memory: nothing new`). Override honored ("capture X, this way"), but the default is "you assess and do it."
- **Plugin reviewed (F):** when this finish is deploying (Step 11 will run), the review is **mandatory, not optional** — run it automatically rather than presenting `skip / yes`. A deploy without a review is not acceptable.
- **Open items completed this session (G/H/I):** items that were *this session's* picked-up `[inbox]` work and got completed are **auto-marked done** (show the reasoning, e.g. "marking done — completed this session"), not left open and re-asked.
- **Net:** a bare `go` runs capture-if-relevant (Claude's call) → review → mark completed items done → then the deploy (Step 11) → deactivation (Step 12). Aaron overrides only exceptions.
- **Empty batch → no stop.** After applying these defaults, if no slots remain that genuinely need a decision, do NOT present an empty batch and wait — report the auto-resolutions (captured memory, auto-done items, review result) as informational output and proceed straight through Steps 8–12. Only stop at the batch when at least one ambiguous slot survives.

The slot bodies and apply-logic below note where this default changes behavior for plugin type. **Story / cab / personal / general are unchanged** — they keep their explicit prompts.

**Batch skeleton — canonical slot order.** Assemble the numbered list by walking these slots in order, omitting any whose condition isn't met, and assigning each surviving slot the next running number `(N)`. Universal slots (and the plugin-only F) are defined inline below; story/cab slot bodies live in `references/finish-story-cab.md` (already loaded in Step 4 for story/cab sessions). For plugin / personal / general sessions the story/cab slots are simply absent — never read the reference for them.

| Slot | Item | Applies to | Body |
|------|------|-----------|------|
| A  | CDK/DynamoDB check            | story/cab + CDK_PRESENT | `references/finish-story-cab.md` |
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

**Plugin type — A2 is not a batch question.** Do not present the `skip / review / new / both` (or `skip / new`) prompt in the batch. Instead, Claude assesses the session itself: validate any loaded memories for accuracy automatically (drop/update stale ones, per the apply-logic), and capture new project/session memory if warranted. Report the outcome outside the batch (`Captured: <name> [<label>]` / `Memory: nothing new`). If genuinely uncertain whether a specific capture is worth making, that single item may be surfaced — but the default is decide-and-do, not ask.

**(F) Plugin reviewed** — plugin type only.

- **If this finish is deploying** (there is work to ship, so Step 11 will run): the review is **mandatory — auto-run it, do not present a skip/yes prompt.** Run the plugin review automatically before the deploy and report the result. A deploy without a review is not acceptable.
- **If this finish is NOT deploying** (clean tree, Step 11 is a no-op) and `plugin_reviewed` is missing, a legacy value, or MAJOR.MINOR differs, it may still be offered:
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
  (N) [<id>] Inbox [in-progress]: "<description>"    keep / done
```

**(I) Legacy [inbox] Open items** — any `[inbox]` tag with no corresponding in-progress inbox entry:
```
  (N) Open item [inbox legacy]: "<text>"    keep / done
```

**Plugin type — auto-resolve this-session's completed work (G/H/I).** For plugin sessions, any G/H/I item that was **this session's picked-up work AND got completed** is marked done automatically — not presented as a question. Detection heuristic: `[inbox]`-tagged Open items (or in-progress inbox items) matching the work this session picked up, when the session actually produced the corresponding changes. Show the resolution with reasoning outside the question set, e.g.:
```
  Auto-resolved (completed this session):
    ✓ [inbox] Make session:finish the plugin deploy — marking done
    ✓ [inbox] session:commit = local checkpoint — marking done
```
Only items that are genuinely ambiguous (started but not clearly finished, or unrelated to the picked-up work) remain as batch questions. If uncertain, default to **done** for plugin type (finish = done) with an easy override — the user can reply `<n> keep` to reopen any auto-resolved item. Story/cab/personal/general keep the explicit `skip / all / keep / done` prompts unchanged.

**(J) Pending inbox sweep** — one per pending inbox item (single-line provenance form — see `references/inbox-convention.md`):
```
  (N) [<id>] Inbox pending: "<description>"  ·  ↳ <session> (<type>) — addressed this session?    nothing / done / picked-up
```
Lead with the item's stable `[<id>]` (omit for legacy items that have none). Include `<slug>` in the `↳` when the item's source repo differs from the current slug; drop it when same-repo; omit `(<type>)` for legacy items.

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
  (8) [vo-ajudd#4] Inbox [in-progress]: "Update session tests"    keep / done
  (9) [vo-ajudd#12] Inbox pending: "Review DynamoDB schema"  ·  ↳ BPT2-6258 (story) — addressed?    nothing / done / picked-up
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
- **done:** strip `[in-progress — ...]`, archive with `[DONE YYYY-MM-DD]`, remove from inbox, remove `[inbox] <item>` from Open items. **Archive file is type-aware:** `_inbox_archive.md` for plugin / personal (item-driven — the canonical inbox is `_inbox.md`), `_inbox_<name>_archive.md` for story / cab / general.
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
1. Remaining items in the fresh inbox read from Step 6 (pending or in-progress) — **plugin / personal → the canonical `_inbox.md`**; **story / cab / general → `_inbox_<name>.md`** → `[today @<handle>] See inbox — N items pending` (N counted by `## <id>` header lines, not the metadata line)
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

**Frontmatter:** for `plugin` and `personal` types, write `type:`, `mode:`, and `status:` keys alongside `updated:`. At finish, `status: completed` — this is what excludes the session from the default `/session:start` resumable listing (the file is never deleted). For `story` / `cab` / `general`, write only `updated:` (preserve any existing extra keys as-is).

```
---
updated: [today's date]
type: [type]            ← plugin/personal only
mode: [planning / coding / both]   ← plugin/personal only; preserve from session file
status: completed       ← plugin/personal only; marks the session done (file kept, hidden from default listing)
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

**Backward compat:** If the existing session file has a `Project:` field, preserve it. If `- **Next step:** <text>` (scalar), re-write as `- **Next steps:**` array tagged `[today @<handle>]`. `Commits:` is preserve-only at this step (written by session:commit) — for plugin type, the deploy (Step 11) appends its deploy commit afterward. `Loaded memories:` carries forward minus anything deleted during the Step 7 memory-validation item.

**After writing — update approved-hash (repo sessions only):** Recompute hash and overwrite `~/.claude/memory/sessions/<slug>/<name>.approved-hash`:
```bash
git hash-object "<session_root>/<name>.md" > ~/.claude/memory/sessions/<slug>/<name>.approved-hash
```

**Update `_index.md`:** Find the line for `<name>`: extract `@created-by` and `created-date` to preserve. Replace or append: `<name> | @<created-by> | <created-date> | @<handle> | <today> | completed | <title-or-dash>`.

**General sessions only:** Also check `~/.claude/memory/sessions/<slug>/<name>/` — if notes, decisions, or outputs were produced today, ensure they are written there before closing.

Print the summary to screen. **For plugin type, this is not the final output** — the deploy (Step 11) runs after the worklog (Step 10) while the session is still active, then deactivation (Step 12) closes out silently, so the deploy's result is the true last line. For all other types, the summary is the final output.

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

### 11. Deploy — plugin type only (runs before deactivation)

**Plugin finish IS the deploy.** This is where the session's work goes live. It runs after the history entry (8), the session summary + mark-completed (9), and the worklog (10) — but **before deactivation (Step 12), deliberately.** All session state is settled first; the code (version bump + push + reinstall) lands last among the content steps, mirroring the repo-based branch flow (state first, code last). Deactivation (removing `_active`) is the true terminal action, run only after the deploy fully completes — so the active session pointer stays present through the entire deploy and closes out last. (This ordering no longer has an edit-permission dependency — acp-ajudd#1 removed the edit-blocking hook — but keeping the deploy before deactivation is the clean lifecycle sequence and positions for future repo-tracked session state shared across developers.)

**For story / cab / personal / general: skip this step entirely.** Those types push during `commit` and have no version/reinstall concept — Step 11 is skipped and their finish ends at deactivation (Step 12).

**No-op guard:** if the Step 2 git scan found nothing to ship (clean tree AND no unpushed local commits from `session:commit`), report `Nothing to deploy — finish complete.` and stop. Do not bump or push.

Otherwise, present the deploy as the clearly-final, visually distinct step — the last thing the user sees (only the silent deactivation of Step 12 follows it):

```
────────────────────────────────────────────────
FINAL STEP — DEPLOY  (bump → commit → push → reinstall → live)
────────────────────────────────────────────────
```

**11a. Derive the target plugin(s) from changed paths** — not from the session name. Using the Step 2 git scan (uncommitted changes + unpushed local commits), map each changed file under the marketplace root to its top-level plugin directory (e.g. `session/commands/finish.md` → `session`). Collect the distinct set. A deploy may span multiple plugins; each affected plugin gets its own bump.

**11b. Version bump — prompted, never silent.** For each affected plugin, read the current version from `<plugin>/.claude-plugin/plugin.json` and suggest a level + next version (one bump per plugin per feature):
- **PATCH** — bug fixes only
- **MINOR** — new command / feature / meaningful behavior addition
- **MAJOR** — redesign or breaking change

Show and wait (this is the one real decision in the deploy):
```
Deploy bump:
  session   v1.53.0 → v1.54.0   (MINOR — finish now deploys; commit is local-only)
go / <plugin> <level> / cancel
```
Apply the confirmed version to each affected `plugin.json`. On **cancel**, stop — nothing is committed, pushed, or reinstalled (the session is already closed; the deploy can be re-run later by re-opening).

**11c. Commit + push to master.** Stage the plugin changes (edited files + bumped `plugin.json`), draft a commit message summarizing the shipped work in the repo's style (`git log --oneline -5`), commit, and **push to master**. Any unpushed local commits made via `session:commit` during the session ride along in the push. End the commit message with the Co-Authored-By trailer per the repo convention (see CLAUDE.md). Direct pushes to `master` on this repo are authorized — no PR.

**11d. Reinstall — make it live, with the Windows fallback.** For each deployed plugin:
```bash
claude plugin update <plugin>@ajudd-claude-plugins
```
**Verify it took** — `claude plugin update` / marketplace update can fail silently on Windows. If the installed version does not match the new `plugin.json` version, fall back to the manual sequence:
```bash
cd ~/.claude/plugins/marketplaces/ajudd-claude-plugins && git pull
claude plugin uninstall <plugin>
claude plugin install <plugin>@ajudd-claude-plugins
```
A Claude Code restart may be required to load the new version — note this if so.

**11e. Record + report.** Append the deploy commit to the session file's `Commits:` field (one-line append — SHA + subject; the file was written in Step 9). Then print the deploy result as the last visible output:
```
Deployed: session v1.53.0 → v1.54.0 — pushed to master, reinstalled (live)
```

### 12. Deactivate Session (terminal action)

The true final action of finish — run **only after the deploy (Step 11) has fully completed** (for plugin type), so the version bump and any other plugin-file edits during the deploy were still authorized by an active coding session. For non-plugin types Step 11 is skipped, so deactivation follows the session summary directly. This step edits no plugin files — it only removes the marker — so it is always safe to run last.

Remove the active marker so no future conversation inherits stale state. `_active` is always local — do not touch the repo session directory for this step:

```bash
rm -f ~/.claude/memory/sessions/<slug>/_active
```

On PowerShell use: `Remove-Item -ErrorAction SilentlyContinue ~/.claude/memory/sessions/<slug>/_active`

Deactivation is silent — it produces no user-facing output, so for plugin type the Step 11 `Deployed: …` line remains the last thing on screen.
