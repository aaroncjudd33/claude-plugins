---
name: start-impl
description: Session start — Steps 4–9. Loaded on demand by start.md after the user selects a session.
---

# Session Start — Implementation (Steps 4–9)

Loaded by `start.md` after the user makes their selection. Context already in scope: `slug`, `session_root`, `handle`, session type, user's chosen action and target name.

---

### 4. User Picks — Load or Create Session File

**Resume existing** (`resume <n>` — plain `<n>` also accepted for backward compatibility):

**Run these reads in parallel:**
- Read `<session_root>/<name>.md`
- Run `wc -l < "<session_root>/_history.md" && tail -n 1 "<session_root>/_history.md"` via Bash — first output is total line count (= entry count), second line is the most recent entry. Do not Read the full file.
- Read the inbox file (`_inbox_<name>.md` for plugins, `_inbox.md` otherwise — from `session_root`) and collect all items (both in-progress and pending) for display.

**Security check (repo sessions only):** If `session_root` is inside a repo (not `~/.claude/memory/sessions/`), run the approval-hash check before displaying any session content:

1. Compute `hash_now`:
   ```bash
   git hash-object "<session_root>/<name>.md"
   ```
2. Read `~/.claude/memory/sessions/<slug>/<name>.approved-hash` (local, never in repo).
3. **Hash file missing (first-time load):**
   - Show: `"First time loading this session file from the repo — reviewing before use."`
   - Display key fields: Type, Branch, Mode, Open items, Next steps, Notes.
   - Output and wait (Pattern 6):
     ```
     Approve and load  ·  skip-teammate-fields  ·  cancel
     ```
     - **Approve and load** → write `hash_now` to `~/.claude/memory/sessions/<slug>/<name>.approved-hash`, load normally.
     - **Skip teammate fields** → quarantine items not tagged with current `@<handle>` (see Quarantine below), write hash.
     - **Cancel** → abort session start.
4. **Hash matches** → load normally, no prompt.
5. **Hash differs (changes since last approval):**
   - Run: `git log -1 --format="%an — %ar" -- "<session_root>/<name>.md"` → who changed it, when.
   - Run: `git diff HEAD~1 HEAD -- "<session_root>/<name>.md"` → what changed. If file not yet in git history, show full content instead.
   - Display: `"Session file modified by @<committer> since you last approved it."` + diff output.
   - Output and wait (Pattern 6):
     ```
     Approve changes  ·  load-quarantined  ·  cancel
     ```
     - **Approve changes** → overwrite approved-hash with `hash_now`, load normally.
     - **Load quarantined** → show changed fields as `[PENDING REVIEW — @handle, date]` in resume block; not added to active Open items routing. Hash still differs — approval required on next load too.
     - **Cancel** → abort.

**Quarantined field display:** Changed fields from teammates appear in the resume block as read-only, clearly marked:
```
  Teammate notes (quarantined — pending approval):
    [PENDING REVIEW — @hiranatam, 2026-06-11]
    - [2026-06-11 @hiranatam] Review DynamoDB schema before load test
```

- Display the resume block:
  ```
  Resuming <name>
    Branch:      [branch]
    Mode:        planning          ← show ONLY when Mode is planning; omit for coding/both/absent
    Open items (mine, N):
      - [date @ajudd] item one
      - [date @ajudd] item two
    Teammate notes (N — read-only):
      - [date @other] their item
    Inbox (N):          ← layout B; [<id>] + provenance dim below each item (see inbox-convention.md)
      1  [<id>]  <description> — in-progress
         ↳ <slug> / <session> (<type>) · MM-DD
      2  [<id>]  <description> — pending
         ↳ <slug> / <session> (<type>) · MM-DD
    Next steps (mine, N):
      - [date @ajudd] next step one
    Teammate next steps (N):
      - [date @other] their suggestion
    Loaded memories (N):
      - <name>  [<label>]
    Recent commits (N):
      - [date] <sha> — <subject>
    Related CAB: [CAB-XXX]   ← story type only, omit if none
    Post-deploy: N pending / all acknowledged / none   ← story type only, omit if none
    Epic:        [BPT2-XXXX]   ← story type only, omit if none
    Related:     [BPT2-XXXX, ...]   ← cab type only, omit if none
    History:     N entries — last: [condensed one-liner of most recent _history.md entry]
  ```
  - **Mode:** show the line only when Mode is `planning` (read-only session — a behavior-changing signal). Omit for `coding`/`both`/absent.
  - **Updated by** is intentionally not shown — it's already in the listing the user just saw.
  - **Memory:** do not print a standalone global/project memory hint line. The on-demand `load memory [topic]` capability still applies; surface it only if the user asks.
  - **Loaded memories:** read from the session file's `Loaded memories:` field. Omit the line if absent or empty. If present, append `— say 'reload' to load them back into context`; do not auto-read the files (on-demand rule). On `reload`, read each listed file from the resolved project memory root.
  - **Recent commits:** read from the session file's `Commits:` field. Show the most recent 3; omit the line if absent or empty.

  If inbox is empty: `Inbox: none`. If `_history.md` does not exist: `History: none`.

  **Mine vs. teammate split rules:**
  - "Mine" = item tagged `[YYYY-MM-DD @<handle>]` where handle matches current user, OR untagged (backward compat — treat as mine).
  - "Teammate" = tagged with a different handle.
  - Old scalar `Next step: <text>` → treat as mine, re-write as array item on next checkpoint/finish.
  - If no teammate items exist, omit the "Teammate notes" and "Teammate next steps" blocks entirely.

- For the `Post-deploy` line: count `- [ ]` items (pending) vs `- [x]` items (acknowledged) from the `Post-deployment checks:` field. Show "N pending" if any unchecked, "all acknowledged" if all checked, "none" if field is absent or empty.
- **If the session file has a `linked_sessions` field**, load each linked session and append a context block immediately after the `History:` line in the resume block:
  ```
  Linked session context:
    <linked-session-name> (<type>) — <last worked on>
      Open items:  [bullets or "none"]
      Next step:   [next step]
      History (last 5):
        [YYYY-MM-DD] <entry>
        ...
  ```
  Read each linked session's `.md` file from `session_root` and its last 5 entries from `<session_root>/_history.md`. If the linked session file does not exist, note "session file not found" and continue. This block is read-only context — it does not affect the current session's state.
- **If the session file has an `Epic` field**, load `~/.claude/memory/epics/<key>.md` and append a compact context block:
  ```
  Epic context: <key> — <title>
    Open questions: N open
    Blockers:       N active (🔴 N critical / 🟡 N watch)
    Last decision:  [most recent decision title]
  ```
  If the epic file does not exist, note: "Epic file for <key> not found."
  Load the full epic file into context so architectural decisions and blockers are available during the session.
- Continue through Steps 5–8 as normal — `_active` must always be written, even on resume.

**New story/plugin/personal/general — session filename:**
- story → `BPT2-XXXX.md`
- cab → `CAB-XXX.md`
- plugin → `<feature-name>.md`   ← derived from the picked inbox item (see Item Pickup below), NOT the plugin name
- personal → `<feature-name>.md` ← derived from the picked inbox item (same flow as plugin)
- general → `<name>.md`

**Item Pickup (plugin / personal only — `pick <n>` / `new <description>`):**

Plugin and personal sessions are created ONLY by picking up an inbox item — never blank, never named after the plugin/project. When the user chose `pick <n>` (or `new <description>`, which already appended the item in start.md Step 4), run this before Step 5:

1. **Locate the item.** The picked item is entry `<n>` (ephemeral list position) in `<session_root>/_inbox.md`, or the item whose stable id is `<id>` if the user picked by ID (`pick acp-ajudd#3`). Read its full `## <id> · [date @handle] from <slug> / <session> (<source-type>) — <description>` header and body (legacy items may lack the `<id> · ` prefix, the `(<source-type>)`, or the slug — read whatever is present). The `<id>` is preserved verbatim in the folded provenance block below (Step 3), so the retired handle stays discoverable in the session file.

   **Maturity guard.** Parse the item's `> [type: … · status: …]` line (missing line → `type: story · status: ready`; parse `type` and `status` independently). If **`status: refining`** — the item is still being scoped, not yet marked ready — **warn and confirm before folding**, keyed on the status value (not on where the item came from): `[<id>] is still refining (not yet marked ready) — pick it up anyway? (yes / leave it refining)`. On `leave it refining`, abort the pickup and leave the item untouched. A `ready` item (the default) is picked with no warning. `note`/`data` types have no maturity gate (their lifecycle is delivery, not maturity — acp-ajudd#10); pick proceeds normally.

2. **Derive a feature name.** Slugify into kebab-case:
   - If the header's `<description>` is a usable short title, slugify it (e.g. "Item-driven sessions for plugin work" → `item-driven-sessions`). Keep it concise (2–4 words).
   - Otherwise read the body and propose a name.
   - **Collision check:** if `<session_root>/<feature-name>.md` already exists, append a disambiguator or pick a distinct name.
   - **Confirm once** (the name is permanent — never silently guess): `Session name: <feature-name>  (reply 'ok' or give a different name)`. Apply any override.

3. **Fold the item into the new session.** When writing the session file in Step 8, seed `Open items` from the item body, and add a provenance block preserving the original header verbatim:
   ```
   ## Picked up from inbox
   <original ## [date @handle] from <slug> / <session> (<source-type>) — <description> header, verbatim (including its `> [type: … · status: …]` line, if any)>
   <original body>
   ```
   Place this in the session file body after the standard fields (it carries the full context so nothing is lost).

4. **Delete the item from `_inbox.md`** — outright, no archive, no `[DONE]` stamp. The session file is now the paper trail, and `git`/file history on `_inbox.md` records what came in and when. Remove exactly the one picked item; leave all other items byte-identical.

This fold-then-delete happens once, at creation. There is no per-session `_inbox_<name>.md` file for these new sessions — the consolidated `_inbox.md` is the only inbox.

### 5. Inbox and Loading Questions

After loading and displaying the resume block, gather all items that need a decision and present them as **one batched block**. Output and wait once (Pattern 2). **Do not use AskUserQuestion.**

**Build the batch block as follows. Omit the batch block entirely if there is nothing to decide (empty inbox, no teammate steps, no review flag).**

**Check `<session_root>/_inbox_<name>.md`** (e.g. `_inbox_release.md`, `_inbox_BPT2-6479.md`). Scan for items:

- **In-progress items** (have an `[in-progress — ...]` line immediately after the `## [date]...` header) — include as batch questions with default `keep`:
  ```
  (N) Inbox [in-progress]: "<description>"  →  keep / done
  ```

- **Pending items** (no in-progress marker) — include as batch questions with default `keep`:
  ```
  (N) Inbox: "<description>"  →  work / done / backlog / keep
  ```

**Teammate next steps** (if any displayed in resume block above) — include as batch questions with default `skip`:
```
(N) Adopt teammate step: "<text>" (via @<handle>)?  →  skip / adopt
```

**Plugin reviewed** (plugin type only) — check plugin.json version at this step:
```bash
grep -o '"version": "[^"]*"' "<plugin_root>/.claude-plugin/plugin.json" | head -1
```
Compare MAJOR.MINOR of `Plugin reviewed:` in session file vs. current version. If they differ (or `Plugin reviewed:` is missing/legacy), include:
```
(N) Plugin reviewed? (last: v<stored>, current: v<current>)  →  skip / yes
```

**Assemble the block:**
```
  (1) Inbox [in-progress]: "Fix prompt patterns UX"  →  keep / done
  (2) Inbox: "Review DynamoDB schema"  →  work / done / backlog / keep
  (3) Adopt teammate step: "Add test coverage" (via @nivi)?  →  skip / adopt
  (4) Plugin reviewed? (last: v1.36, current: v1.40)  →  skip / yes

Reply with overrides or "go".
```

**Defaults shown inline.** "go" accepts all defaults. User may reply with any combination:
`2 work`, `2 work 4 yes`, `1 done 3 adopt`, `go`, `all done`, etc.

**Applying the answers:**

For inbox items:
- **done** (in-progress): strip the `[in-progress — ...]` line, archive with `[DONE YYYY-MM-DD]` stamp, remove entry from inbox, remove matching `[inbox] <item>` from session Open items.
- **keep** (in-progress): no change — stays in inbox, stays in Open items.
- **work** (pending): insert `[in-progress — <session-name>, YYYY-MM-DD]` on the line immediately after the `## [date]...` header. Do NOT archive yet. Add `[inbox] <short description>` to session Open items.
- **done** (pending): archive with `[DONE YYYY-MM-DD]` stamp, remove from inbox.
- **backlog**: move to `_backlog_<name>.md` (plugin) or `_backlog.md` (others), remove from inbox. Create file if needed.
- **keep** (pending): leave as-is. Do NOT add to Open items.

For work items with significant depth, after applying the answer, note: "Create a work file for decisions/notes? (yes / skip)" — this follow-up is the only additional stop acceptable here (new info — can't know if a work file is needed until the item is chosen). If yes: create `<session_root>/_work_<name>_YYYY-MM-DD-<short-slug>.md` with the original problem and a `## Notes` section.

For teammate steps:
- **adopt**: re-tag as `[YYYY-MM-DD @<handle>] <text> (via @<original-handle>)`, move to active Next steps.
- **skip**: keep as FYI context only — not used for inbox routing or finish derivation.

For plugin reviewed:
- **yes**: update `Plugin reviewed: <current-version>` in the session file immediately.
- **skip**: continue. Will show again at next session start if minor version still differs.

**Archive files:**
- All sessions: `<session_root>/_inbox_<name>_archive.md` — header: `# Inbox Archive — <name>`

Create the archive file if it does not exist. Archive entry format (append, blank line between entries):
```
[DONE YYYY-MM-DD]
[original ## date line]
  - [original item content]
  [Work file: _work_<name>_YYYY-MM-DD-<slug>.md]   ← only if a work file was created
```

**Auto-purge archive:** After handling inbox items, if the archive file exists, drop any entries whose `[DONE YYYY-MM-DD]` date is more than 30 days before today. Rewrite the file with only the retained entries (preserving the header line).

**Global inbox (`_inbox.md`):** Check for global items (undirected notes, new plugin ideas, or spawned sessions without a named target). If it has content, show it separately after the batch block result (not folded in — it's separate from the session-specific inbox):

```
Global inbox (<N> item(s)):        ← layout B; [<id>] + provenance dim below (see inbox-convention.md)
  [<id>]  ★ [spawn] <label>
     ↳ <slug> / <session> (<type>) · MM-DD — ready to start as <type>
      Next step: <next step from spawn entry>
  1  [<id>]  <regular item description>
     ↳ <slug> / <session> (<type>) · MM-DD
```
(Drop `<slug>` when same-repo; omit `(<type>)` for legacy items; tolerate spaced/unspaced `/`.)

Routing line for global inbox (if any items):
```
  work <n>  ·  done <n>  ·  backlog <n>  ·  keep
```

- **`[spawn]` entries:** Picking one up (`work <n>`) runs the full new-session kickoff with the spawn's linked context pre-loaded. Archive after Step 6 once the new session name is established, using stamp `[PICKED UP YYYY-MM-DD — <new-session-name>]`.
- **Regular entries:** same dispositions as session inbox above; use `_inbox_archive.md` as archive.

**Backlog notice:** After all inbox handling, check `_backlog_<name>.md` (plugin) or `_backlog.md` (others) and count logical items (lines beginning with `[20` or `## `). If count > 0, show:
```
Backlog: N items — say 'backlog' to review
```
If the user later says `backlog`, display items numbered and use a plain routing line:
```
  pull <n>  ·  delete <n>  ·  keep  ·  all done
```
- **pull**: move to inbox — enters normal inbox flow at next session start.
- **delete**: remove permanently — no archive.
- **keep**: leave in backlog.

### 6. Establish Session Identity

| Type | name | teams_chat |
|------|------|------------|
| plugin | plugin name (e.g. `office`) | `Plugin — Aaron Work` (consolidated — all plugin work) |
| story | story key (e.g. `BPT2-1234`) | `BPT2-XXXX — <title>` (from Jira) |
| cab | CAB number (e.g. `CAB-456`) | `CAB-XXX — <description>` (from Jira) |
| personal | name the user provides | `none` |
| general | name the user provides | `<Name> - Claude <Category>` |

For **general**, also ask for a category if not obvious: Research / Prototype / Training / Other.

For **personal**, no category prompt — and Teams chat is always `none` (no lookup or creation).

### 6a. Session Mode

**Default: `coding`.** No stop needed.

For **new sessions**: state the mode as a note at the end of the Step 6 output:
```
Mode: coding  (say 'planning' or 'both' to change before we begin)
```
If the user included a mode modifier in their start.md reply, apply it silently.

For **resume**: mode is shown in the resume block. If the user included `planning`, `both`, or `coding` in their start.md reply, apply it now and note the change: `Mode changed to <new>`. If no modifier was given, keep the existing mode.

Store the result as `mode` for use in Step 8.

### 7. Teams Chat Setup

**Plugin sessions default to the consolidated "Plugin — Aaron Work" chat** (`19:8bff4d4e8659475da4a8edbfca0d270a@thread.v2`) — the whole plugin suite is one house, so there are no per-plugin "<Name> - Claude Plugin" chats anymore (those are retired, `Active=no`). Resolve to the consolidated chat by default; the repoint-to-different option below still applies if the user wants a specific chat for a session.

Look in `~/.claude/plugins/known-chats.md` for a chat whose Name, Aliases, or Topic matches the expected `teams_chat` value and has `Active=yes`. If the file does not exist, treat it as empty and proceed to the Not found branch.

Match priority (case-insensitive):
1. Exact match on Name
2. Match on any entry in the Aliases column (comma-separated; match each alias individually)
3. Substring match on Topic

When the user refers to a chat informally ("my team chat", "the group chat", "cab chat"), check Aliases before Topic.

- **Found:** "Using Teams chat: [name]" — proceed, or offer to repoint if the user wants a different one.
- **Not found:** output and wait (plain text routing):
  ```
  No Teams chat found for '<teams_chat>':
    create it  ·  use different  ·  skip
  ```
  After `use different` → ask: "Which existing chat should this session use?"
  - **Create it:** create the chat via yl-msoffice MCP, add the entry to `known-chats.md`. Do **not** include `ajudd@youngliving.com` in the members array — the Graph API automatically adds the authenticated user.
  - **Use different:** store the named chat instead.
  - **Skip:** set `teams_chat` to `none` — Teams steps in checkpoint will be skipped.

### 8. Write Session State

Create `session_root` directory if it does not exist.

**Use the Open items list as it stands after Step 5 processing** — any items removed or added during inbox handling must be reflected here, not the state read in Step 4.

Write `<session_root>/<name>.md`:

**Frontmatter — for `plugin` and `personal` types, write `type:`, `mode:`, and `status:` keys alongside `updated:`.** The scope-guard hook (`session-scope-guard.py`) reads `mode:` from the frontmatter only (never the body bullets) to decide whether Edit/Write is allowed — so these keys must be present and accurate for plugin/personal sessions. For `story` / `cab` / `general` types, write only `updated:` as before (those zones use instruction-only Mode handling — no need to churn their frontmatter). The body bullets (`- **Type:**`, `- **Mode:**`, `- **Status:**`) stay for all types regardless.

```
---
updated: [today's date]
type: [type]            ← plugin/personal only — keep in sync with the Mode bullet
mode: [planning / coding / both]
status: in-progress
---

# Session State — <name>

- **Type:** [type]
- **Mode:** [planning / coding / both]
- **Name:** [name]
- **updated-by:** @<handle>
- **created-by:** @<handle>   ← written once at creation; never overwrite on checkpoint/finish/commit/switch
- **Title:** [Jira summary]   ← story/cab only — from getJiraIssue; omit for other types
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Scope:** [scope path]   ← relative path: story/cab/personal: "./"; plugin: "<plugin-name>/"; omit for general
- **Status:** in-progress
- **Branch:** [branch or "n/a"]
- **Last worked on:** [will be updated at checkpoint]
- **Open items:** [carried from previous session, or "none"]
- **Next steps:** [will be updated at checkpoint — array format; "none" for a new session]
- **Loaded memories:**   ← preserve on resume; omit for a new session (none yet). Written by the memory plugin
  - <name>  [<label>]
- **Commits:**   ← preserve on resume; omit for a new session. Written by session:commit
  - [YYYY-MM-DD] <short-sha> — <commit subject>
- **Plugin reviewed:** <version>   ← plugin type only; write current plugin.json version when marking reviewed; omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Epic:** [BPT2-XXXX]   ← story type only; omit if no Jira epic link; set from Jira Epic Link during new story kickoff
- **Post-deployment checks:**   ← story type only, omit for other types; omit entire field if none defined
  - [ ] <check description>
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
- **linked_sessions:** [<session-name>, ...]   ← omit if empty; set by /session:spawn; preserve as-is on resume
```

**Scope field — relative path rules:**
- Plugin sessions: `<plugin-name>/` (e.g., `session/`, `release/`)
- Story / cab / personal: `./` (whole repo) or a service subdirectory if the session targets one
- General: omit the field entirely

The scope guard resolves this to an absolute path at runtime: `local_cfg.projectRoot + "/" + scope_value` for repo-based sessions; absolute path as-is for legacy local sessions.

**Backward compatibility:** When resuming an older session file that still has an absolute `Scope:` or a `Project:` field, preserve them as-is rather than rewriting. Rewrite only when the session is new or when the user explicitly runs `session:migrate`.

For story and cab types, populate **Title** from the `summary` field of `getJiraIssue`. When resuming an existing session, preserve the existing Title if present. If the session file predates this field (no Title line), fetch from Jira during Step 9 routing and add it.

Write `~/.claude/memory/sessions/<slug>/_active` (always local — plain text, just the name, no `.md` extension):
```
BPT2-1234
```

`_active` is a convenience hint for `session:start` resume suggestions only — it is not read by `session:checkpoint` or `session:finish` to determine session identity.

**Seed `_index.md`:** Update `<session_root>/_index.md` — create with header if not exists:
```
# Session Index — <slug>
# name | created-by | created-date | updated-by | updated-date | status | title
```
Find the line starting with `<name> | ` and replace it; if not found, append. Write line:
`<name> | @<handle> | <today> | @<handle> | <today> | in-progress | <title-or-dash>`
Where `<title-or-dash>` = `Title:` field for story/cab; `—` for other types.

### 9. Route Based on Choice

**If Mode is `planning`**, print before routing:
```
PLANNING MODE — No code edits this session.
Any implementation work should be routed to this session's inbox for a coding session to pick up.
```

**Plugin — feature session (new, via `pick`/`new`):**
1. **Determine the target plugin(s)** from the folded item body / feature scope. If the work targets one or more existing plugins, **read in parallel** their `plugin.json`, `SKILL.md` (if present), and all files under each skill's `references/` directory. **Do not pre-read individual command `.md` files** — load them on demand when the task targets a specific command. If the feature is scaffolding a brand-new plugin, skip this read; the folder/marketplace work happens within the session.
2. **Memory scan offer** — if project memory exists for this slug (a `MEMORY.md` at the resolved project memory root) and the session has no `Loaded memories:` yet, offer once: `Scan project memory for what's relevant to this work? (scan / skip)`. On `scan`, run the memory plugin's `/memory:scan` flow using the feature name + folded item as the feature-area signal; present candidates, load picks, record to `Loaded memories:`. On `skip`, proceed. Never auto-load.
3. Confirm approach before making changes.

**Plugin — resume feature session:**
1. **Read in parallel** the `plugin.json`/`SKILL.md`/`references/` for the plugin(s) the session's Scope targets.
2. The plugin reviewed check was already handled in Step 5. No additional review prompt here.
3. **Memory scan offer** — same as the new-session case (offer once if project memory exists and no `Loaded memories:` yet).
4. Summarize what's open and next; ask what needs to change if not already stated.

**Story — resume:**
1. `getJiraIssue` — verify status matches memory.
2. Check git branch — confirm it matches, offer to switch if not.
3. If the session file has no `Epic` field: check the Jira issue data from step 1 for an Epic Link.
   - **Epic Link found in Jira:** set `Epic: <key>` in the session file. Follow the same load/create flow as new kickoff step 2.
   - **No Epic Link in Jira:** skip silently.
   - If the session file already has an `Epic` field, skip (epic was loaded in Step 4).
4. Summarize: what's done, what's open, what's next.
5. **Memory scan offer** — if project memory exists for this repo (a `MEMORY.md` at the resolved project memory root) and the session has no `Loaded memories:` yet, offer once: `Scan project memory for what's relevant to this work? (scan / skip)`. On `scan`, run the memory plugin's `/memory:scan` flow (infer feature area, present candidates, load picks, record to `Loaded memories:`). On `skip`, proceed. Do not auto-load.

**Story — new kickoff:**
1. `getJiraIssue` → transition to In Progress → create feature branch.
2. Check for Epic Link in the Jira issue. If an epic key is present:
   - Check whether `~/.claude/memory/epics/<epic-key>.md` exists.
   - **Not found:** output and wait:
     ```
     No epic memory for <key> — create one?  yes / skip
     ```
     - **yes:** create `~/.claude/memory/epics/<key>.md` with pre-populated structure: epic title from Jira, story map row for the current story. Use `references/epic-template.md` from the session skill as the structural template.
   - **Found:** note "Epic memory loaded for <key>" — file is already in context.
   - Set `Epic: <key>` in the session file.
3. **Memory scan offer** — if project memory exists for this repo (a `MEMORY.md` at the resolved project memory root), offer once: `Scan project memory for what's relevant to this story? (scan / skip)`. On `scan`, run the memory plugin's `/memory:scan` flow using the story title and branch as the feature-area signal, present candidates, load the user's picks, and record them to the session's `Loaded memories:` field. On `skip`, proceed. Never auto-load — this is the point-in-time where relevant memory is surfaced for a new story.
4. Investigate codebase, confirm Teams chat exists, check Confluence page.

**CAB — new:**
- Route to `/release:create-cab`.

**CAB — resume:**
1. Read the CAB card from Jira.
2. Check release branch status.

**Personal — resume feature session:**
1. Check git branch — confirm it matches the session file, offer to switch if not.
2. **Memory scan offer** — if project memory exists for this slug (a `MEMORY.md` at the resolved project memory root) and the session has no `Loaded memories:` yet, offer once: `Scan project memory for what's relevant to this work? (scan / skip)`. On `scan`, run `/memory:scan`; on `skip`, proceed. Never auto-load.
3. Summarize: what's open, what's next.

**Personal — feature session (new, via `pick`/`new`):**
1. The session name and folded item come from Item Pickup (Step 4) — do NOT ask for a project name.
2. Check current git branch, record it in the session file.
3. **Memory scan offer** — same as resume (offer once if project memory exists and no `Loaded memories:` yet). This is the parity point with story work: project memory is surfaced at pickup so prior decisions inform the session.
4. Understand the task, confirm approach, proceed.

**General:**
1. Ensure `~/.claude/memory/sessions/<slug>/<name>/` exists (create if not).
2. Load any prior notes from that folder.
3. Understand the task, confirm approach, proceed.
