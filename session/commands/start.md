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

Run **five calls in parallel** — no session file reads at this stage. **Issue all five as a single parallel batch before processing any result — do not wait for one to complete before issuing the next.**

1. **List sessions directory with timestamps:**
   ```bash
   ls -lt <session_root>/
   ```
   Extract session names from `.md` filenames only. **Skip every file whose name starts with `_`** (e.g. `_history.md`, `_inbox.md`, `_index.md`, `_active`, `_inbox_archive.md`) and skip `*.approved-hash` files — do not read any of them. Use the file modification date as the sort key and display date.

2. **Count inbox items — no content read:**
   ```bash
   for f in "<session_root>/_inbox"*.md; do printf "%s: " "$f"; grep -c "^## \|^\[20" "$f" 2>/dev/null || echo 0; done
   ```
   Extract item count per named inbox file from the line counts. Global inbox (`_inbox.md`) counted separately — surfaced in Step 3. **Do not read any inbox file contents at listing time** — content is loaded in Step 5 only after the user selects a session.

3. **Read `<marketplace_root>/.claude-plugin/marketplace.json`** (plugin type only — used in Step 3).

4. **Read `<session_root>/_index.md`** (if it exists). Two supported formats — detect by counting `|`-delimited columns in the header:
   - **7-column (current):** `name | @created-by | created-date | @updated-by | updated-date | status | title`
   - **6-column (legacy):** `name | created-by | updated-by | date | status | title` — treat `date` as both created-date and updated-date; prepend `@` to creator/updater values if missing.
   Parse whichever format is present. **Do not read any session `.md` files during this step.**

5. **Check for repo memory (single bash call):**
   ```bash
   git rev-parse --show-toplevel 2>/dev/null && [ -f "<repo_root>/.claude/memory/MEMORY.md" ] && grep -c "^\- \[" "<repo_root>/.claude/memory/MEMORY.md" || echo "no-repo-memory"
   ```
   If output is a number, that's the entry count. If `no-repo-memory`, skip the repo memory line.

**If `_index.md` is absent or missing entries for sessions found in call 1:** display the table immediately using only data from calls 1 and 4 — show `—` for any missing creator, created-date, or title columns. **Do not read session files or run git log at listing time.** Add a footer note below the table:
```
  (index missing or incomplete — type 'index' to build it)
```
The index is built lazily: Step 8 seeds an entry whenever a session is loaded or created. If the user types `index`, run a parallel read of all session `.md` files (no git log), extract `updated-by:`, `updated:`, `created-by:`, and `Title:` fields, write `_index.md` in 7-column format, and re-display the table.

If sessions exist, display in-progress and paused sessions first (sorted by updated-date, newest first), completed sessions grouped at the bottom. Always include a column header line:
```
Sessions in <slug>
  #    name         created              last edit            status        in  out  title
  1    CAB-9240     @ajudd  May 18       @ajudd  May 27       in-progress    0    0   BP2 - Downline Reports - SG Daily Reports Fix
  2    BPT2-6377    @ajudd  Jun 01       @nivi   Jun 11       in-progress    1    0   Shopify Member Agreement Prompt

  7 completed — type 'all' to show
```

Show `@creator date` in "created" column; show `@updater date` in "last edit" column. When creator == updater AND dates differ, still show both columns. Always show both `in` and `out` counts (show `0` — never omit). When user types `all`, re-display including completed sessions.

**`filter_mine` active** (user passed `mine` arg): filter index entries where `@created-by` or `@updated-by` matches the current user — no additional file reads needed. Show `[filtered to @<handle>]` on the header.

If repo memory was found (call 5), add one line after the sessions table:
```
  Repo memory: N entries
```
Omit entirely if `.claude/memory/MEMORY.md` does not exist.

If `session_root` does not exist or is empty, skip this section.

### 3. Present Options

**Free-text and search:** Before showing the action picker, the user may type text to filter the sessions table (keywords `mine`, `all`, `backlog`, and `index` are handled directly — see above). If the user uses the "Other" field in the AskUserQuestion picker to type something, try it as a session filter first — match against name, title, handle, or status. Re-display the filtered table with `(filtered by '<query>')` and re-present the picker. If no sessions match, treat the input as free-form intent and proceed naturally.

**Plugin project** — use the `marketplace.json` loaded in Step 2. List any plugins from `marketplace.json` not already in the sessions table as reference below the table:
```
  · <plugin-name> — <one-phrase description>  (no session yet)
```

Then use **AskUserQuestion** (single-select):
```yaml
question: "What would you like to do?"
header: "Action"
options:
  - label: "resume"
    description: "Resume an existing session — you'll pick the number next"
  - label: "start"
    description: "Start a session for a plugin — you'll give the name"
  - label: "new plugin"
    description: "Create a brand new plugin from scratch"
```
"Other" is the free-text path — type anything and Claude will interpret it.

After selection:
- **resume** → ask immediately: "Which number?" — use it to load the session in Step 4.
- **start** → ask immediately: "Which plugin?" — route to new or existing session.
- **new plugin** → proceed to Step 6 new plugin flow.
- **Other** → interpret the typed text as intent and proceed naturally.

**Work project:**

If `_inbox.md` has logical items, show them compactly after the sessions table and before the options. Flag `[spawn]` entries with ★ — they are ready-to-start handoffs, not just notes:
```
Global inbox (N items):
  ★ [spawn] <label> — from <source>/<session>, ready to start as <type>
  [date] from <source-slug>/<session-name> — <one-line description>
  ...
```
Full handling (work/done/backlog/keep) happens at Step 5.

Use **AskUserQuestion** (single-select) after the inbox summary:
```yaml
question: "What would you like to do?"
header: "Action"
options:
  - label: "resume"
    description: "Resume an existing session — you'll pick the number next"
  - label: "start story"
    description: "Start a new story — you'll give a Jira key (BPT2-XXXX) or URL"
  - label: "start cab"
    description: "Start a CAB — you'll list the story keys"
```
"Other" is the free-text path — type anything and Claude will interpret it.

After selection:
- **resume** → ask immediately: "Which number?" — use it to load the session in Step 4.
- **start story** → ask immediately: "Story key or URL?"
- **start cab** → ask immediately: "Story keys? (space-separated, e.g. BPT2-6499 BPT2-6500)"
- **Other** → interpret the typed text as intent and proceed naturally.

**Personal project** (path under `/c/claude/`):

Same global inbox compact display as above if `_inbox.md` has items.

Use **AskUserQuestion** (single-select):
```yaml
question: "What would you like to do?"
header: "Action"
options:
  - label: "resume"
    description: "Resume an existing session — you'll pick the number next"
  - label: "start"
    description: "Start a new personal session — you'll give it a name"
```
"Other" is the free-text path. After: **resume** → "Which number?"; **start** → "Session name?"; **Other** → proceed naturally.

**General / unknown project:**

Same global inbox compact display as above if `_inbox.md` has items.

Use **AskUserQuestion** (single-select):
```yaml
question: "What would you like to do?"
header: "Action"
options:
  - label: "resume"
    description: "Resume an existing session — you'll pick the number next"
  - label: "start"
    description: "Start something new — you'll name it and pick a category"
```
"Other" is the free-text path. After: **resume** → "Which number?"; **start** → "Name and category?"; **Other** → proceed naturally.

### 4. Handoff to Implementation

Once the user has made their selection and answered any follow-up question (session number, story key, plugin name, etc.), **read `session/commands/start-impl.md` immediately** as the very next action. That file contains Steps 4–9: session load, security check, inbox processing, Teams setup, write state, and routing by type.

Do not proceed further until start-impl.md is loaded.

---
<!-- Steps 4–9 are in start-impl.md — loaded on demand after user picks -->

