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

The listing is rendered by a helper script so its deterministic formatting (grouping, title truncation, column widths, the active marker) is not generated token-by-token. **Issue the render call and the Step 3 input call(s) together in one response — do not process any result before all are issued.**

1. **Render the listing — run the script and display its stdout verbatim:**
   ```bash
   SL="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}/scripts/session-list.py"
   if command -v python3 >/dev/null 2>&1 && [ -f "$SL" ]; then
     python3 "$SL" --session-root "<session_root>" --slug "<slug>" --handle "<handle>"
   fi
   ```
   (`${CLAUDE_PLUGIN_ROOT}` is used when set; otherwise the script resolves from the marketplace clone — derive `<pluginMarketplaceName>` as in Step 1.) The script reads `_index.md` (7-col current / 6-col legacy), the per-session inbox files (`_inbox_<name>.md`, archives excluded), the `_active` marker, and the session `.md` filenames itself, then prints the finished, aligned, grouped table — default columns, with completed and `refinement-*` sessions hidden. **Display its stdout exactly as printed: do not re-align, re-order, restate, or wrap it in a code fence.**

2. **Step 3 inputs (same parallel batch):**
   - **Global inbox (all types):** read `<session_root>/_inbox.md` if it exists — Step 3's routing block lists its items and flags `[spawn]` entries with ★. (The script counts only per-session `_inbox_<name>.md` files; the global inbox is separate.)
   - **Non-plugin type:** repo-memory count —
     ```bash
     RTOP=$(git rev-parse --show-toplevel 2>/dev/null); if [ -n "$RTOP" ] && [ -f "$RTOP/.claude/memory/MEMORY.md" ]; then grep -c "^\- \[" "$RTOP/.claude/memory/MEMORY.md"; else echo "no-repo-memory"; fi
     ```
   - **Plugin type:** read `<marketplace_root>/.claude-plugin/marketplace.json` (used in Step 3).

**Filter flags** — when the user's reply is a deterministic filter, re-run the script with the matching flag and display the new stdout verbatim:
`full` → `--full` · `all` → `--show all` · `refinement` → `--show refinement` · `status <value>` → `--status <value>` · `mine` → `--mine`

**Free-text natural-language filters** (`has inbox`, `updated by nivi`, `paused this week`) are not deterministic — read `_index.md` yourself and render the filtered subset inline (the one case the model still formats), then re-show the routing block.

**Index rebuild** — if the listing ends with `(index missing or incomplete …)` and the user types `index`, read all session `.md` files in parallel (no git log), extract `updated-by:`, `updated:`, `created-by:`, `Title:`, write `_index.md` in 7-column format, then re-run the script.

**Example of the script's output** (this is what the script prints — echo it as-is, do not regenerate):
```
Sessions in virtual-office

  #  name       title                            status       in  last edit

  In Progress
  1  CAB-9240   BP2 - Downline Reports - SG...   in-progress  0   @ajudd May 27  ←
  2  BPT2-6377  Shopify Member Agreement Pro...  in-progress  1   @nivi Jun 11

  2 in-progress · 1 paused · 8 completed
```

**Fallback (script unavailable)** — if `python3` is absent, the script exits non-zero, or stdout is empty, render the listing yourself: read `_index.md`; group by status (In Progress, Paused; Completed only on `all`); one row per session — `# · name · title (≤32 chars, "..." if longer) · status · in-count · @updater date` (add `out` + `@creator created-date` only on `full`); mark the `_active` session with `←`; skip `_`-prefixed files and `refinement-*` (unless `refinement`/`all`); end with `N in-progress · N paused · N completed`. Plain unaligned text is fine in the fallback.

If repo memory was found (Step 3 input above), add one line after the sessions table:
```
  Repo memory: N entries
```
Omit entirely if `.claude/memory/MEMORY.md` does not exist.

If `session_root` does not exist or is empty, skip this section.

### 3. Present Routing Block and Wait

Output the routing block and wait for one free-text reply. **Do not use AskUserQuestion.** Output the routing block as plain text — do not wrap it in a fenced code block and do not add a separator line (`---`) before it.

**Free-text and search:** If the user types text that doesn't match a routing action, interpret it as a natural-language filter — match against name, title, handle, status, inbox count, or any session field. Accept plain descriptions like `has inbox`, `updated by nivi`, `created by me`, `paused`, `completed this week`. Re-display the filtered table with `(filtered by '<query>')` and re-show the routing block. If no sessions match and the text looks like intent rather than a filter, proceed naturally. Keywords `mine`, `all`, `backlog`, `index`, `status` are handled directly (see Step 2).

**Parse combinations freely.** A single reply may include multiple signals — session number, mode, modifiers, inbox dispositions. Examples: `1`, `resume 1`, `1 planning`, `resume session reviewed work 2`, `start release`, `2 yes 4 skip`. Infer intent; speak up only if genuinely ambiguous.

**Shared across all project types** (defined once — the per-type blocks below add only their type-specific `Start / Resume` lines and inputs):

Every routing block ends with this same **Search by** section — append it to whichever type block you render:
```
  Search by:
    mine             — show only your sessions
    all              — include completed sessions
    full             — show all columns (adds out count + created date)
    status <value>   — filter by in-progress / paused / completed
    <text>           — search name or title, or describe a filter (e.g. "has inbox", "updated by nivi")
```

Every type also accepts these same inputs (in addition to its type-specific ones):
- Number or session name alone (`1`, `<name>`) → resume; `resume <n>` / `resume <name>` → resume
- `mine` → filter to sessions where @created-by or @updated-by matches current user; re-display and re-show routing
- `all` → re-display including completed sessions; re-show routing
- `full` → re-display the table with the full 8-column set (adds `out` count + `created` date); re-show routing
- `status <value>` → filter to that status; re-display and re-show routing
- Any other text → natural-language filter; match against name, title, handle, status, inbox count, or any field; re-display with `(filtered by '<query>')` and re-show routing

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

Then output the routing block — the type-specific `Start / Resume` lines, followed by the shared **Search by** block:
```
  Start / Resume:
    resume <n>       — resume by number
    start <plugin>   — start a session for a plugin
    new plugin       — create a brand new plugin
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `start <plugin-name>` → start that plugin session (new or existing)
- `new plugin` → new plugin creation flow
- Mode modifier (`planning` / `both` / `coding`) → set mode after loading
- `reviewed` → mark plugin reviewed after loading
- `work <n>` / `done <n>` / `backlog <n>` / `keep` → inbox disposition after loading
- Combinations: `resume 1 planning` / `1 reviewed work 2`

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

Then output the routing block — the type-specific `Start / Resume` lines, followed by the shared **Search by** block:
```
  Start / Resume:
    resume <n>       — resume by number (e.g. resume 2)
    start story      — start a new story — you'll give a key or URL
    start cab        — start a new CAB — you'll give story keys
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `start story` → route to new story; if no key in reply, ask "Story key or URL?" as follow-up
- `start story BPT2-XXXX` → route directly with that key
- `start cab` → route to new CAB; if no keys in reply, ask "Story keys? (space-separated)" as follow-up
- `work <n>` on a global inbox `[spawn]` item → route through spawn flow

---

**Personal project:**

If `_inbox.md` has items, show compact summary before the routing line.

Then output the routing block — the type-specific `Start / Resume` lines, followed by the shared **Search by** block:
```
  Start / Resume:
    resume <n>       — resume by number
    start            — start a new session — you'll give it a name
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `start` → route to new personal session; if no name in reply, ask "Session name?" as follow-up
- `start <name>` → route directly with that name

---

**General / unknown project:**

If `_inbox.md` has items, show compact summary before the routing line.

Then output the routing block — the type-specific `Start / Resume` lines, followed by the shared **Search by** block:
```
  Start / Resume:
    resume <n>       — resume by number
    start            — start a new session — you'll give a name and context
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `start` → route to new session; if no name/context in reply, ask "Name and what you're working on?" as follow-up

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

**Security check (repo sessions only):** If `session_root` is inside a repo (not `~/.claude/memory/sessions/`), run the approval-hash check before displaying any session content. Follow the same gate as start-impl.md Step 4: compute `git hash-object`, compare to `~/.claude/memory/sessions/<slug>/<name>.approved-hash`, and require approval on first load or when the file changed since last approval. For local plugin sessions (`session_root` is under `~/.claude/`), skip this check.

Display resume block:
```
Resuming <name>
  Branch:      [branch]
  Mode:        planning          ← show this line ONLY when Mode is planning; omit for coding/both
  Open items (mine, N):
    - [date @handle] item
  Inbox (N items):
    1  [date] <description> — in-progress / pending
  Next steps (mine, N):
    - [date @handle] step
  Loaded memories (N):
    - <name>  [<label>]
  Recent commits (N):
    - [date] <sha> — <subject>
  History:     N entries — last: [condensed one-liner]
```
- **Mode:** show the line only when Mode is `planning` (read-only session — a behavior-changing signal worth surfacing). Omit entirely for `coding`/`both`/absent.
- **Updated by** is intentionally not shown here — it's already in the listing the user just saw.
- **Memory:** do not print a standalone global-memory hint line. The on-demand `load memory [topic]` capability still applies; surface it only if the user asks.
- Omit teammate sections if no items tagged with a different @handle.
- If inbox empty: `Inbox: none`. If history file missing: `History: none`.
- **Loaded memories:** read from the session file's `Loaded memories:` field. Omit the line entirely if the field is absent or empty. If present, append the hint `— say 'reload' to load them back into context` (do not auto-read the files — on-demand rule). On `reload`, read each listed memory file from the resolved project memory root.
- **Recent commits:** read from the session file's `Commits:` field. Show the most recent 3; omit the line entirely if the field is absent or empty.
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
