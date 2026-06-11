---
name: start
description: Start a working session. Loads last session context and routes into the right workflow.
---

# Session Start

Begin a working session. Establishes session identity, Teams chat, and routes into the right workflow.

## Instructions

### 0. Fast-Path Argument Check

If arguments were passed to `/session:start`, attempt to resolve them before running the full discovery flow.

**Detect arg type** (checked in order):

| Pattern | Example | Resolves to |
|---------|---------|-------------|
| `mine` | `/session:start mine` | full discovery flow with mine filter |
| `BPT2-XXXX` (Jira story key) | `/session:start BPT2-6429` | story session |
| `CAB-XXXX` (CAB key) | `/session:start CAB-9260` | cab session |
| `cab BPT2-XXXX [...]` | `/session:start cab BPT2-6429 BPT2-6430` | new CAB for those stories |
| Plugin name in marketplace | `/session:start release` | plugin session |

**Fast-path flow:**
1. Run `pwd`, extract slug, read `~/.claude/plugins/user-config.json` (same as Step 1). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).
2. If arg is `mine`: set `filter_mine = true`, fall through to Step 1 — full discovery with mine filter.
3. Derive session type and target name from the arg (story key → type=story, name=BPT2-XXXX; plugin name → type=plugin, name=<plugin>; etc.).
4. Check whether `<session_root>/<name>.md` exists:
   - **Exists** → go directly to Step 4 (Resume existing) with that session.
   - **Does not exist** → before Step 6, check `<session_root>/_inbox.md` for a `[spawn]` entry whose label matches the target name. If found, archive it immediately with stamp `[PICKED UP YYYY-MM-DD — <target-name>]` to `<session_root>/_inbox_archive.md` (creating the archive file if needed). Then go to Step 6 (Establish Session Identity) and continue through Steps 7–8 as normal before Step 9 routing.
5. Skip Steps 2, 3 entirely — no session listing, no inbox counts, no menu.

**No argument or unrecognized argument:** fall through to Step 1 — run the full discovery flow as normal.

---

### 1. Derive Repo Slug and Session Type

Run `pwd` and extract the **last path component** as the repo slug:
- `/c/Users/ajudd/.claude/plugins/marketplaces/ajudd-claude-plugins` → `ajudd-claude-plugins`
- `/c/dev/gen-leadership-bonus` → `gen-leadership-bonus`

Read `~/.claude/plugins/user-config.json` and extract:
- `paths.pluginMarketplaceName` — if absent, auto-detect by listing `~/.claude/plugins/marketplaces/` and using the first directory found
- `paths.workReposDir` — e.g. `/c/dev` (may be empty)
- `paths.personalProjectsDir` — e.g. `/c/claude` (may be empty)

Detect session type from the current path:
- **plugin** — path contains the value of `pluginMarketplaceName`
- **story / cab** — `workReposDir` is set and path begins with it; fallback: path contains `/dev/`
- **personal** — `personalProjectsDir` is set and path begins with it; fallback: path contains `/c/claude/`
- **general** — anything else

Resolve `session_root` and `handle` using Path Resolution (see Session Skill). If repo-based and `~/.claude/config/<slug>.json` is missing, auto-create it silently (see First-Run Auto-Config in Session Skill).

### 2. Load Sessions

Run **three calls in parallel** — no session file reads at this stage:

1. **List sessions directory with timestamps:**
   ```bash
   ls -lt <session_root>/
   ```
   Extract session names from `.md` filenames, skipping files that start with `_`. Use the file modification date as last-active date for display. Note any `_outbox_<name>.md` files for outbox count detection.

2. **Read all inbox files in one shot:**
   ```bash
   for f in "<session_root>/_inbox"*.md; do echo "=== FILE: $f ==="; cat "$f"; done
   ```
   Count logical items per named inbox file (lines beginning with `[20` or `## `). Global inbox (`_inbox.md`) counted separately — surfaced in Step 3.

3. **Read `<marketplace_root>/.claude-plugin/marketplace.json`** (plugin type only — used in Step 3).

**Do not read session file contents, history, or outbox files here** — all of that loads in Step 4 after the user picks a session.

If sessions exist, display sorted by modification date (newest first):
```
Sessions in <slug>
  [1]  <name>  |  inbox N  outbox 0  |  <date>
  [2]  <name>  |  inbox 0  outbox 0  |  <date>
```

Outbox count: 0 unless `_outbox_<name>.md` appeared in the `ls` output, in which case count its `## ` lines.

**CRITICAL — no session file reads in the listing:** The table above uses ONLY data from `ls -lt` (name, date) and inbox counts from Step 2. Do NOT read session files to add titles, "last worked on" text, status, or any other content to this table. Titles and details load in Step 4 after the user picks a session.

**`filter_mine` active** (user passed `mine` arg): read session files in a separate parallel batch just to extract `updated-by`, then filter. Show `[filtered to @<handle>]` on the header.

If `session_root` does not exist or is empty, skip this section.

### 3. Present Options

**Plugin project** — use the `marketplace.json` loaded in Step 2. Always show the inbox count (use `inbox 0` when empty):
- **[N] Resume <plugin-name>**  inbox N  — <date>
- **<plugin-name>** — <one-phrase description> *(one line per plugin in marketplace.json not already in sessions list)*
- New plugin
- Something else — describe it

**Work project:**

If `_inbox.md` has logical items, show them compactly after the sessions table and before the options. Flag `[spawn]` entries with ★ — they are ready-to-start handoffs, not just notes:
```
Global inbox (N items):
  ★ [spawn] <label> — from <source>/<session>, ready to start as <type>
  [date] from <source-slug>/<session-name> — <one-line description>
  ...
```
Full handling (Work on it / Mark done / Move to backlog / Keep) happens at Step 5.

- **[N] Resume <BPT2-XXXX>** — inbox N | <date>  *(use name + inbox count + date from table above — no session file reads; titles and details load in Step 4)*
- Pick up a story (Jira URL or key)
- Start a CAB
- Something else — describe it

**Personal project** (path under `/c/claude/`):

Same global inbox compact display as above if `_inbox.md` has items.

- **[N] Resume <name>** — inbox N | <date>  *(name + inbox count + date only — no session file reads)*
- Start something new — give it a name

**General / unknown project:**

Same global inbox compact display as above if `_inbox.md` has items.

- **[N] Resume <name>** — inbox N | <date>  *(name + inbox count + date only — no session file reads)*
- Start something new — give it a name and category

### 4. User Picks — Load or Create Session File

**Resume existing [N]:**

**Run these three reads in parallel:**
- Read `<session_root>/<name>.md`
- Read `<session_root>/_history.md` — count total entries and extract the most recent one for display.
- Read the inbox file (`_inbox_<name>.md` for plugins, `_inbox.md` otherwise — from `session_root`) and collect all items (both in-progress and pending) for display.

**Security check (repo sessions only):** If `session_root` is inside a repo (not `~/.claude/memory/sessions/`), run the approval-hash check before displaying any session content:

1. Compute `hash_now = SHA-256(file content)`:
   ```bash
   python3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "<session_root>/<name>.md"
   ```
2. Read `~/.claude/memory/sessions/<slug>/<name>.approved-hash` (local, never in repo).
3. **Hash file missing (first-time load):**
   - Show: `"First time loading this session file from the repo — reviewing before use."`
   - Display key fields: Type, Branch, Mode, Open items, Next steps, Notes.
   - Ask: `"Approve and load? (yes / skip teammate fields / cancel)"`
     - **yes** → write `hash_now` to `~/.claude/memory/sessions/<slug>/<name>.approved-hash`, load normally.
     - **skip teammate fields** → quarantine items not tagged with current `@<handle>` (see Quarantine below), write hash.
     - **cancel** → abort session start.
4. **Hash matches** → load normally, no prompt.
5. **Hash differs (changes since last approval):**
   - Run: `git log -1 --format="%an — %ar" -- "<session_root>/<name>.md"` → who changed it, when.
   - Run: `git diff HEAD~1 HEAD -- "<session_root>/<name>.md"` → what changed. If file not yet in git history, show full content instead.
   - Display: `"Session file modified by @<committer> since you last approved it."` + diff output.
   - Ask: `"Approve these changes? (yes / load with changes quarantined / cancel)"`
     - **yes** → overwrite approved-hash with `hash_now`, load normally.
     - **quarantined** → show changed fields as `[PENDING REVIEW — @handle, date]` in resume block; not added to active Open items routing. Hash still differs — approval required on next load too.
     - **cancel** → abort.

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
    Updated by:  @<handle>   ← from updated-by field; confirms attribution
    Mode:        [planning / coding / both]
    Open items (mine, N):
      - [date @ajudd] item one
      - [date @ajudd] item two
    Teammate notes (N — read-only):
      - [date @other] their item
    Inbox (N):
      [1] [date] <description> — in-progress
      [2] [date] <description> — pending
    Next steps (mine, N):
      - [date @ajudd] next step one
    Teammate next steps (N):
      - [date @other] their suggestion
    Related CAB: [CAB-XXX]   ← story type only, omit if none
    Post-deploy: N pending / all acknowledged / none   ← story type only, omit if none
    Epic:        [BPT2-XXXX]   ← story type only, omit if none
    Related:     [BPT2-XXXX, ...]   ← cab type only, omit if none
    History:     N entries — last: [condensed one-liner of most recent _history.md entry]
  ```
  If inbox is empty: `Inbox: none`. If `_history.md` does not exist: `History: none`.

  **Mine vs. teammate split rules:**
  - "Mine" = item tagged `[YYYY-MM-DD @<handle>]` where handle matches current user, OR untagged (backward compat — treat as mine).
  - "Teammate" = tagged with a different handle.
  - Old scalar `Next step: <text>` → treat as mine, re-write as array item on next checkpoint/finish.
  - If no teammate items exist, omit the "Teammate notes" and "Teammate next steps" blocks entirely.

  **After displaying teammate next steps**, offer:
  ```
  Adopt any teammate next steps as your own? (numbers, 'all', or 'skip')
  ```
  Adopted items re-tagged: `[YYYY-MM-DD @<handle>] <text> (via @<original-handle>)` and moved into your active Next steps. Declined items remain as FYI context only — not used for inbox routing or finish derivation.
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
- plugin → `<plugin-name>.md`
- cab → `CAB-XXX.md`
- personal → `<name>.md`
- general → `<name>.md`

### 5. Check Inbox

**For all sessions**, check `<session_root>/_inbox_<name>.md` (e.g. `_inbox_release.md`, `_inbox_BPT2-6479.md`). This is the session-specific inbox where cross-scope work is routed via `/session:inbox`.

If the inbox file exists and has content beyond the header line, scan for two categories of items based on whether an `[in-progress — ...]` line appears immediately after the `## [date]...` entry header:

**In-progress items** (already picked up by this or a prior unfinished session) — show first:

```
Resuming in-progress (<N> item(s)):
  [1] [in-progress since YYYY-MM-DD] <description from entry header>
  Mark done (numbers, 'all') / Keep working / skip
```

- **Mark done:** strip the `[in-progress — ...]` line, archive with `[DONE YYYY-MM-DD]` stamp (see Archive files below), remove entry from inbox, remove matching `[inbox] <item>` from session Open items.
- **Keep working:** no change — stays in inbox as in-progress, stays in Open items.

**Pending items** (no in-progress marker) — show after:

```
Inbox (<N> item(s)):
  [1] [date] from <source-slug> / <session-name>
      - <one-line summary>
  [2] [date] from <source-slug> / <session-name>
      - <one-line summary>
```

If multiple pending items, offer a bulk shortcut first: **"Handle all: Work on all / Mark all done / Move all to backlog / Keep all"**. Handle each item individually with: **Work on it / Mark done / Move to backlog / Keep**

- **Work on it:** insert `[in-progress — <session-name>, YYYY-MM-DD]` on the line immediately after the `## [date]...` header in the inbox file. Do NOT archive yet — the item stays in the inbox until work is complete. Add `[inbox] <short description>` to session `Open items`. For items with significant depth, offer: "Create a work file for decisions/notes? (yes / skip)" — if yes, create `<session_root>/_work_<name>_YYYY-MM-DD-<short-slug>.md` with the original problem and a `## Notes` section; add `Work file: _work_<name>_YYYY-MM-DD-<short-slug>.md` to the inbox entry on a new line after the in-progress marker.
- **Mark done:** archive with `[DONE YYYY-MM-DD]` stamp (see Archive files), remove from inbox.
- **Move to backlog:** move to backlog file (`_backlog_<name>.md` for plugins, `_backlog.md` for others), remove from inbox. Create the backlog file if it doesn't exist with header `# Backlog — <name> plugin` (plugin) or `# Backlog — <slug>` (others). No archive — backlog items stay until explicitly deleted.
- **Keep:** leave as-is. Do NOT add to Open items.

If the file does not exist or contains only the header, skip silently.

**Archive files:**
- All sessions: `<session_root>/_inbox_<name>_archive.md` — header: `# Inbox Archive — <name>`

Create the archive file if it does not exist. Archive entry format (append, blank line between entries):
```
[DONE YYYY-MM-DD]
[original ## date line]
  - [original item content]
  [Work file: _work_<name>_YYYY-MM-DD-<slug>.md]   ← only if a work file was created
```

All archived entries use `[DONE YYYY-MM-DD]`. The `[in-progress — ...]` marker is stripped before archiving — it is only meaningful while the work is active.

**Auto-purge archive:** After handling inbox items, if the archive file exists, read it and drop any entries whose `[DONE YYYY-MM-DD]` date is more than 30 days before today. Rewrite the file with only the retained entries (preserving the header line).

**Additionally**, check `<session_root>/_inbox.md` for global items (undirected notes, new plugin ideas, or spawned sessions without a named target). If it has content, show it separately. Flag `[spawn]` entries prominently — they are pre-loaded handoffs ready to start as a new session:

```
Global inbox (<N> item(s)):
  ★ [spawn] <label> — from <source-slug>/<session-name>, ready to start as <type>
      Next step: <next step from spawn entry>
  [date] from <source-slug>/<session-name> — <regular item description>
```

- **`[spawn]` entries:** Picking one up ("Work on it") runs the full new-session kickoff (Jira story, branch, etc.) with the spawn's linked context pre-loaded. Archive after Step 6 once the new session name is established, using stamp `[PICKED UP YYYY-MM-DD — <new-session-name>]`. Note: spawns are the only inbox entries that archive at pickup — the spawn's job is done once it routes into a new session. All other items use the in-progress marker and archive only when work is complete.
- **Regular entries:** Work on it / Mark done / Move to backlog / Keep — same flow as always.

Global inbox items are never auto-cleared. The same handling options apply, using `_inbox_archive.md` as the archive.

**Backlog:** After all inbox handling, check `_backlog_<name>.md` (plugin) or `_backlog.md` (others) and count logical items (lines beginning with `[20` or `## `). If count > 0, show:

```
Backlog: N items — type 'backlog' to review
```

If the user types 'backlog', display each item numbered with: **Pull into inbox / Delete**
- **Pull into inbox:** move the entry from the backlog file to the inbox file; it enters the normal Work on it / Mark done / Move to backlog / Keep flow next session.
- **Delete:** remove from backlog, no archive.

If the backlog file does not exist or is empty, omit this line entirely.

### 6. Establish Session Identity

| Type | name | teams_chat |
|------|------|------------|
| plugin | plugin name (e.g. `office`) | `<Name> - Claude Plugin` |
| story | story key (e.g. `BPT2-1234`) | `BPT2-XXXX — <title>` (from Jira) |
| cab | CAB number (e.g. `CAB-456`) | `CAB-XXX — <description>` (from Jira) |
| personal | name the user provides | `none` |
| general | name the user provides | `<Name> - Claude <Category>` |

For **general**, also ask for a category if not obvious: Research / Prototype / Training / Other.

For **personal**, no category prompt — and Teams chat is always `none` (no lookup or creation).

### 6a. Session Mode

Use **AskUserQuestion** with a single-select question:

```
question: "What mode?"
header: "Mode"
options:
  - label: "coding"
    description: "Full access — implement freely (default)"
  - label: "planning"
    description: "Read-only — design, analyze, write to inbox; no code edits or file writes"
  - label: "both"
    description: "Full access — planning and coding in the same session"
```

For **resume**: the current mode is already shown in the resume block. Use AskUserQuestion with two options:

```
question: "Mode is [current] — keep it or change?"
header: "Mode"
options:
  - label: "Keep [current]"
    description: "Continue with the existing mode"
  - label: "Change"
    description: "Pick a different mode"
```

If the user selects "Change", present the three-option AskUserQuestion above.

Store the result as `mode` for use in Step 8.

### 7. Teams Chat Setup

Look in `~/.claude/plugins/known-chats.md` for a chat whose Name, Aliases, or Topic matches the expected `teams_chat` value and has `Active=yes`. If the file does not exist, treat it as empty and proceed to the Not found branch.

Match priority (case-insensitive):
1. Exact match on Name
2. Match on any entry in the Aliases column (comma-separated; match each alias individually)
3. Substring match on Topic

When the user refers to a chat informally ("my team chat", "the group chat", "cab chat"), check Aliases before Topic. If matched via alias, confirm before proceeding: "Matched '[phrase]' → [Name]. Using that — ok?"

- **Found:** "Using Teams chat: [name]" — proceed, or offer to repoint if the user wants a different one
- **Not found:** "No chat found for `[teams_chat]`. Create it? (Yes / Skip / Use a different chat)"
  - **Yes:** create the chat via yl-msoffice MCP, add the entry to `known-chats.md`. Do **not** include `ajudd@youngliving.com` in the members array — the Graph API automatically adds the authenticated user; passing them explicitly causes a "Duplicate chat members" error.
  - **Skip:** set `teams_chat` to `none` — Teams steps in checkpoint will be skipped
  - **Different:** ask which existing chat to use, store that name instead

### 8. Write Session State

Create `session_root` directory if it does not exist.

**Use the Open items list as it stands after Step 5 processing** — any items removed or added during inbox handling must be reflected here, not the state read in Step 4.

Write `<session_root>/<name>.md`:

```
---
updated: [today's date]
---

# Session State — <name>

- **Type:** [type]
- **Mode:** [planning / coding / both]
- **Name:** [name]
- **updated-by:** @<handle>
- **Title:** [Jira summary]   ← story/cab only — from getJiraIssue; omit for other types
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Scope:** [scope path]   ← relative path: story/cab/personal: "./"; plugin: "<plugin-name>/"; omit for general
- **Status:** in-progress
- **Branch:** [branch or "n/a"]
- **Last worked on:** [will be updated at checkpoint]
- **Open items:** [carried from previous session, or "none"]
- **Next step:** [will be updated at checkpoint]
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

### 9. Route Based on Choice

**If Mode is `planning`**, print before routing:
```
PLANNING MODE — No code edits this session.
Any implementation work should be routed to this session's inbox for a coding session to pick up.
```

**Plugin — existing plugin:**
1. **Read all of these files in parallel as a single batch:** `plugin.json`, all command `.md` files, `SKILL.md` if present, and all files under the skill's `references/` directory if it exists
2. Check `plugin_reviewed` in the session file. Read the current version from `plugin.json`. If `plugin_reviewed` is missing, a legacy `yes`/`no` value, or its `MAJOR.MINOR` differs from the current version's `MAJOR.MINOR`, show:
   > "⚠ This plugin has not been reviewed yet." (if missing/legacy) or "⚠ This plugin has not been reviewed since v<stored> (current: v<current>)."
   Follow immediately with: "Mark as reviewed? (Yes — I've already run it / No — remind me later)"
   - **Yes:** update `plugin_reviewed: <current-version>` in the session file immediately. No further action needed.
   - **No:** continue. Will show again at next session start if minor version still differs.
   Patch bumps within the same `MAJOR.MINOR` do not trigger the reminder.
3. Ask what needs to change if not already stated
4. Confirm approach before making changes

**Plugin — new plugin:**
1. Ask for the plugin name and what it should do
2. Create the folder structure and files
3. Add entry to `marketplace.json`, commit, push, install

**Story — resume:**
1. `getJiraIssue` — verify status matches memory
2. Check git branch — confirm it matches, offer to switch if not
3. If the session file has no `Epic` field: check the Jira issue data from step 1 for an Epic Link.
   - **Epic Link found in Jira:** set `Epic: <key>` in the session file. Follow the same load/create flow as new kickoff step 2.
   - **No Epic Link in Jira:** skip silently — epic links are managed in Jira by the team lead; the session plugin reacts to them, it does not create them.
   - If the session file already has an `Epic` field, skip this step (epic was loaded in Step 4).
4. Summarize: what's done, what's open, what's next

**Story — new kickoff:**
1. `getJiraIssue` → transition to In Progress → create feature branch
2. Check for Epic Link in the Jira issue. If an epic key is present:
   - Check whether `~/.claude/memory/epics/<epic-key>.md` exists
   - **Not found:** "No epic memory for <key> — create one? (Yes / Skip)"
     - **Yes:** create `~/.claude/memory/epics/<key>.md` with pre-populated structure: epic title from Jira, story map row for the current story. Use `references/epic-template.md` from the session skill as the structural template.
   - **Found:** note "Epic memory loaded for <key>" — file is already in context
   - Set `Epic: <key>` in the session file
3. Investigate codebase, confirm Teams chat exists, check Confluence page

**CAB — new:**
- Route to `/release:create-cab`

**CAB — resume:**
1. Read the CAB card from Jira
2. Check release branch status

**Personal — resume:**
1. Check git branch — confirm it matches the session file, offer to switch if not
2. Summarize: what's done, what's open, what's next

**Personal — new:**
1. Ask for the project name
2. Check current git branch, record it in the session file
3. Understand the task, confirm approach, proceed

**General:**
1. Ensure `~/.claude/memory/sessions/<slug>/<name>/` exists (create if not)
2. Load any prior notes from that folder
3. Understand the task, confirm approach, proceed
