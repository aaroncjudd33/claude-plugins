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
   - **Exists + plugin session** → go directly to the Plugin session resume path in Step 4 (no start-impl.md read needed).
   - **Exists + other type** → read start-impl.md, go directly to Step 4 (Resume existing) with that session.
   - **Does not exist** → before Step 6, check `<session_root>/_inbox.md` for a `[spawn]` entry whose label matches the target name. If found, archive it immediately with stamp `[PICKED UP YYYY-MM-DD — <target-name>]` to `<session_root>/_inbox_archive.md` (creating the archive file if needed). Read start-impl.md, then go to Step 6.
5. Skip Steps 2, 3 entirely — no session listing, no inbox counts, no routing block.

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

Run **three calls in parallel** (four for plugin type). **Issue all calls in a single response — do not process any result before all calls are issued.**

1. **List sessions directory with timestamps:**
   ```bash
   ls -lt <session_root>/
   ```
   Extract session names from `.md` filenames only. **Skip every file whose name starts with `_`** (e.g. `_history.md`, `_inbox.md`, `_index.md`, `_active`, `_inbox_archive.md`) and skip `*.approved-hash` files — do not read any of them. Use the file modification date as the sort key and display date.

2. **Combined bash — inbox counts + active session + repo memory (non-plugin only). Issue as a single Bash call:**

   **Plugin type:**
   ```bash
   echo "---INBOX---"
   for f in "<session_root>/_inbox"*.md; do printf "%s: " "$f"; grep -c "^## \|^\[20" "$f" 2>/dev/null || echo 0; done
   echo "---ACTIVE---"
   cat "<session_root>/_active" 2>/dev/null || true
   ```

   **Non-plugin type:**
   ```bash
   echo "---INBOX---"
   for f in "<session_root>/_inbox"*.md; do printf "%s: " "$f"; grep -c "^## \|^\[20" "$f" 2>/dev/null || echo 0; done
   echo "---REPO---"
   RTOP=$(git rev-parse --show-toplevel 2>/dev/null); if [ -n "$RTOP" ] && [ -f "$RTOP/.claude/memory/MEMORY.md" ]; then grep -c "^\- \[" "$RTOP/.claude/memory/MEMORY.md"; else echo "no-repo-memory"; fi
   echo "---ACTIVE---"
   cat "<session_root>/_active" 2>/dev/null || true
   ```

   Parse sections by `---X---` separator lines. Global inbox (`_inbox.md`) counted separately — surfaced in Step 3. **Do not read any inbox file contents at listing time.** Repo memory: if output is a number that's the entry count; `no-repo-memory` → omit the repo memory line.

3. **Read `<session_root>/_index.md`** (if it exists). Two supported formats — detect by counting `|`-delimited columns in the header:
   - **7-column (current):** `name | @created-by | created-date | @updated-by | updated-date | status | title`
   - **6-column (legacy):** `name | created-by | updated-by | date | status | title` — treat `date` as both created-date and updated-date; prepend `@` to creator/updater values if missing.
   Parse whichever format is present. **Do not read any session `.md` files during this step.**

4. **Read `<marketplace_root>/.claude-plugin/marketplace.json`** (plugin type only — used in Step 3). Omit for non-plugin types.

**If `_index.md` is absent or missing entries for sessions found in call 1:** display the table immediately using only data from calls 1 and 4 — show `—` for any missing creator, created-date, or title columns. **Do not read session files or run git log at listing time.** Add a footer note below the table:
```
  (index missing or incomplete — type 'index' to build it)
```
The index is built lazily: Step 8 seeds an entry whenever a session is loaded or created. If the user types `index`, run a parallel read of all session `.md` files (no git log), extract `updated-by:`, `updated:`, `created-by:`, and `Title:` fields, write `_index.md` in 7-column format, and re-display the table.

If sessions exist, display in-progress and paused sessions first (sorted by updated-date, newest first), completed sessions grouped at the bottom. Always include a column header line:
```
Sessions in <slug>
  #    name         title                            status        in  out  created        last edit
  1    CAB-9240     BP2 - Downline Reports - SG...   in-progress    0    0   @ajudd May 18  @ajudd May 27
  2    BPT2-6377    Shopify Member Agreement Pro...   in-progress    1    0   @ajudd Jun 01  @nivi  Jun 11

  2 in-progress · 0 paused · 7 completed
```

**Title truncation:** cap title at 32 characters. If longer, truncate and append `...`. If title is `—` (absent), show `—` with no padding.

Show `@creator date` in "created" column; show `@updater date` in "last edit" column. When creator == updater AND dates differ, still show both columns. Always show both `in` and `out` counts (show `0` — never omit). Mark the active session from call 6 with `←` on that row.

**Status summary line:** always show all three statuses in this exact format: `N in-progress · N paused · N completed`. Show `0` for any status with no sessions — never omit a status. Do not append any instructional text like "type 'all' to show" — the Search by block already covers that. When user types `all`, re-display including completed sessions.

**`filter_mine` active** (user passed `mine` arg): filter index entries where `@created-by` or `@updated-by` matches the current user — no additional file reads needed. Show `[filtered to @<handle>]` on the header.

If repo memory was found (call 5), add one line after the sessions table:
```
  Repo memory: N entries
```
Omit entirely if `.claude/memory/MEMORY.md` does not exist.

If `session_root` does not exist or is empty, skip this section.

### 3. Present Routing Block and Wait

Output the routing block and wait for one free-text reply. **Do not use AskUserQuestion.**

**Free-text and search:** If the user types text that doesn't match a routing action, interpret it as a natural-language filter — match against name, title, handle, status, inbox count, or any session field. Accept plain descriptions like `has inbox`, `updated by nivi`, `created by me`, `paused`, `completed this week`. Re-display the filtered table with `(filtered by '<query>')` and re-show the routing block. If no sessions match and the text looks like intent rather than a filter, proceed naturally. Keywords `mine`, `all`, `backlog`, `index`, `status` are handled directly (see Step 2).

**Parse combinations freely.** A single reply may include multiple signals — session number, mode, modifiers, inbox dispositions. Examples: `1`, `resume 1`, `1 planning`, `resume session reviewed work 2`, `start release`, `2 yes 4 skip`. Infer intent; speak up only if genuinely ambiguous.

---

**Plugin project:**

List any plugins from `marketplace.json` not already in the sessions table:
```
  · <plugin-name> — <one-phrase description>  (no session yet)
```

If the active session (call 6) is in the table, append inline hints on the following line:
```
  + planning / both → change mode  ·  reviewed → mark plugin reviewed  ·  work/done/backlog <n> → inbox items
```
(Omit hints that don't apply — e.g. omit the inbox hint if inbox count is 0.)

Then output the routing block:
```
  Start / Resume:
    resume <n>       — resume by number
    start <plugin>   — start a session for a plugin
    new plugin       — create a brand new plugin

  Search by:
    mine             — show only your sessions
    all              — include completed sessions
    status <value>   — filter by in-progress / paused / completed
    <text>           — search name or title, or describe a filter (e.g. "has inbox", "updated by nivi")
```

**Accepted inputs:**
- Number or session name alone (`1`, `session`) → resume
- `resume <n>` / `resume <name>` → resume
- `start <plugin-name>` → start that plugin session (new or existing)
- `new plugin` → new plugin creation flow
- `mine` → filter table to sessions where @created-by or @updated-by matches current user; re-display and re-show routing
- `all` → re-display including completed sessions, re-show routing
- `status <value>` → filter table to sessions matching that status; re-display and re-show routing
- Mode modifier (`planning` / `both` / `coding`) → set mode after loading
- `reviewed` → mark plugin reviewed after loading
- `work <n>` / `done <n>` / `backlog <n>` / `keep` → inbox disposition after loading
- Combinations: `resume 1 planning` / `1 reviewed work 2`
- Any other text → natural-language filter; match against any field; re-display with `(filtered by '<query>')` and re-show routing

If the user replies with just `start` (no plugin name), ask: "Which plugin?" as the only follow-up.

---

**Work project:**

If `_inbox.md` has logical items, show compactly before the routing line. Flag `[spawn]` entries with ★:
```
Global inbox (N items):
  ★ [spawn] <label> — from <source>/<session>, ready to start as <type>
  [date] from <source-slug>/<session-name> — <one-line description>
```
Full inbox handling (work/done/backlog/keep) happens at Step 5.

Then output the routing block:
```
  Start / Resume:
    resume <n>       — resume by number (e.g. resume 2)
    start story      — start a new story — you'll give a key or URL
    start cab        — start a new CAB — you'll give story keys

  Search by:
    mine             — show only your sessions
    all              — include completed sessions
    status <value>   — filter by in-progress / paused / completed
    <text>           — search name or title, or describe a filter (e.g. "has inbox", "updated by nivi")
```

**Accepted inputs:**
- Number or session name → resume
- `resume <n>` → resume
- `start story` → route to new story; if no key in reply, ask "Story key or URL?" as follow-up
- `start story BPT2-XXXX` → route directly with that key
- `start cab` → route to new CAB; if no keys in reply, ask "Story keys? (space-separated)" as follow-up
- `work <n>` on a global inbox `[spawn]` item → route through spawn flow
- `mine` → filter table to sessions where @created-by or @updated-by matches current user; re-display and re-show routing
- `all` → re-display including completed sessions and re-show routing
- `status <value>` → filter table to sessions matching that status; re-display and re-show routing
- Any other text → natural-language filter; match against name, title, handle, status, inbox count, or any field; re-display with `(filtered by '<query>')` and re-show routing

---

**Personal project:**

If `_inbox.md` has items, show compact summary before the routing line.

Then output the routing block:
```
  Start / Resume:
    resume <n>       — resume by number
    start            — start a new session — you'll give it a name

  Search by:
    mine             — show only your sessions
    all              — include completed sessions
    status <value>   — filter by in-progress / paused / completed
    <text>           — search name or title, or describe a filter (e.g. "has inbox", "updated by nivi")
```

**Accepted inputs:**
- Number or session name → resume
- `resume <n>` → resume
- `start` → route to new personal session; if no name in reply, ask "Session name?" as follow-up
- `start <name>` → route directly with that name
- `mine` → filter table to sessions where @created-by or @updated-by matches current user; re-display and re-show routing
- `all` → re-display including completed sessions and re-show routing
- `status <value>` → filter table to sessions matching that status; re-display and re-show routing
- Any other text → natural-language filter; match against name, title, handle, status, inbox count, or any field; re-display with `(filtered by '<query>')` and re-show routing

---

**General / unknown project:**

If `_inbox.md` has items, show compact summary before the routing line.

Then output the routing block:
```
  Start / Resume:
    resume <n>       — resume by number
    start            — start a new session — you'll give a name and context

  Search by:
    mine             — show only your sessions
    all              — include completed sessions
    status <value>   — filter by in-progress / paused / completed
    <text>           — search name or title, or describe a filter (e.g. "has inbox", "updated by nivi")
```

**Accepted inputs:**
- Number or session name → resume
- `resume <n>` → resume
- `start` → route to new session; if no name/context in reply, ask "Name and what you're working on?" as follow-up
- `mine` → filter table to sessions where @created-by or @updated-by matches current user; re-display and re-show routing
- `all` → re-display including completed sessions and re-show routing
- `status <value>` → filter table to sessions matching that status; re-display and re-show routing
- Any other text → natural-language filter; match against name, title, handle, status, inbox count, or any field; re-display with `(filtered by '<query>')` and re-show routing

---

### 4. Act on User's Reply

Once the user replies, act immediately. **Do not read start-impl.md first** for the plugin resume path below.

---

**Plugin session — resume existing:**

Run **three reads in parallel:**
- Read `<session_root>/<name>.md`
- ```bash
  wc -l < "<session_root>/_history.md" 2>/dev/null && tail -n 1 "<session_root>/_history.md" 2>/dev/null || echo "0"
  ```
- Read `<session_root>/_inbox_<name>.md` (skip if file does not exist)

Display resume block:
```
Resuming <name>
  Branch:      [branch]
  Updated by:  @<handle>
  Mode:        [planning / coding / both]
  Open items (mine, N):
    - [date @handle] item
  Inbox (N items):
    1  [date] <description> — in-progress / pending
  Next steps (mine, N):
    - [date @handle] step
  History:     N entries — last: [condensed one-liner]
  Memory:      <N> global entries available — say 'load memory [topic]' to load relevant files
```
- Omit teammate sections if no items tagged with a different @handle.
- If inbox empty: `Inbox: none`. If history file missing: `History: none`.
- Count N by scanning `~/.claude/memory/MEMORY.md` lines starting with `- [` (already in context — no extra call).
- Mine vs. teammate: item is mine if tagged `[YYYY-MM-DD @<handle>]` matching current user, or untagged.

**Inbox + reviewed batch** (one stop — Pattern 2). Omit entirely if inbox is empty AND plugin version unchanged:
```
(1) Inbox [in-progress]: "<desc>"  →  keep / done
(2) Inbox: "<desc>"  →  work / done / backlog / keep
(3) Plugin reviewed? (last: v<stored>, current: v<current>)  →  skip / yes

Reply with overrides or "go".
```
Plugin reviewed check: `grep -o '"version": "[^"]*"' "<plugin_root>/.claude-plugin/plugin.json" | head -1` — compare MAJOR.MINOR of `Plugin reviewed:` field vs current. Show only if they differ.

Apply answers:
- **in-progress done**: archive with `[DONE YYYY-MM-DD]` stamp, remove from inbox, remove matching `[inbox] <item>` from Open items.
- **in-progress keep**: no change.
- **pending work**: add `[in-progress — <session-name>, YYYY-MM-DD]` immediately after the `## [date]...` header; add `[inbox] <short desc>` to Open items.
- **pending done**: archive with stamp.
- **backlog**: move to `_backlog_<name>.md` (create if needed), remove from inbox.
- **pending keep**: leave as-is.
- **reviewed yes**: update `Plugin reviewed: <current-version>` in session file.

Write state:
- `<session_root>/<name>.md` — updated-by `@<handle>`, updated date = today, Status = in-progress, Open items = post-inbox state.
- `~/.claude/memory/sessions/<slug>/_active` — session name (plain text).
- `_index.md` — find line starting with `<name> | ` and replace (or append): `<name> | @<created-by> | <created-date> | @<handle> | <today> | in-progress | <title-or-dash>`.

Read `<plugin_root>/.claude-plugin/plugin.json` and `<plugin_root>/skills/<plugin>/SKILL.md` in parallel. Apply any mode modifier from the user's reply. Ask what needs to change.

---

**All other cases** — read `session/commands/start-impl.md` immediately, then continue from Step 4 there:
- New plugin session
- Work / personal / general session (resume or new)
- Any case requiring a follow-up question (story key, plugin name, session name)

<!-- Steps 4–9 for new sessions and non-plugin types are in start-impl.md -->
