---
name: start
description: Start a working session. Loads last session context and routes into the right workflow.
---

# Session Start

Begin a working session. Establishes session identity, Teams chat, and routes into the right workflow.

## Instructions

### 0. Fast-Path Argument Check

If arguments were passed to `/session:start`, attempt to resolve them before running the full discovery flow.

**Two verbs — `refine` (planning, sessionless) and `code` (coding session).** The mode is never something you set; it is **read from the file you're touching** — a target with no session file is **work** you're still scoping (planning/refining), a target that already has a session file is *coding*. `code` and `refine` just name which side you're on. (`new`, `resume`, and `pick` are retired — folded into these two.)

**Detect arg type** (checked in order):

| Pattern | Example | Resolves to |
|---------|---------|-------------|
| `mine` | `/session:start mine` | full discovery flow with mine filter |
| `refine [target]` | `/session:start refine shopify refund` | refinement flow (Step 4 → Refine); **sessionless — never creates a session file** |
| `code <target>` | `/session:start code BPT2-6429` | coding session on `<target>` — the file decides: a **`work` entry** graduates into a fresh session, an existing **session** resumes |
| `BPT2-XXXX` (Jira story key) | `/session:start BPT2-6429` | coding session on that story (bare key = implicit `code`) |
| `CAB-XXXX` (CAB key) | `/session:start CAB-9260` | coding session on that CAB (bare key = implicit `code`) |
| `code cab BPT2-XXXX [...]` | `/session:start code cab BPT2-6429 BPT2-6430` | new CAB coding session for those stories (bare `cab BPT2-…` also accepted) |
| Existing session name | `/session:start release` | coding session — resume it (bare name = implicit `code`; any type, incl. legacy plugin-named + feature sessions) |

**Fast-path flow:**
1. Run `pwd`, extract slug, read `~/.claude/plugins/user-config.json` (same as Step 1). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).
2. If arg is `mine`: set `filter_mine = true`, fall through to Step 1 — full discovery with mine filter.
2a. If arg is `refine` or `refine <target>`: resolve `session_root`/`handle` (step 1 above), then go directly to Step 4 → **Refine — enter refinement flow**, passing any `<target>` as the refine argument. Skip Steps 1–3.
2b. If arg is `code`, `code <target>`, or `code cab <keys>` (or bare `cab <keys>`): resolve `session_root`/`handle`, strip the `code` verb, and treat `<target>` exactly as a bare token in step 3 below (`code cab <keys>` / `cab <keys>` → new CAB kickoff). Skip Steps 1–3.
3. Derive session type and target name from the arg (story key → type=story, name=BPT2-XXXX; CAB key → type=cab; `cab <keys>` / `code cab <keys>` → new CAB; any other bare token → the `code` target — a session NAME to resume, or a `work` entry to graduate).
4. Check whether `<session_root>/<name>.md` exists (**this existence check IS "the file decides"** — a session file present means resume-coding; absent means graduate-work or kickoff):
   - **Exists + plugin session** → go directly to the Plugin session resume path in Step 4 (no start-impl.md read needed).
   - **Exists + other type** → read start-impl.md, go directly to Step 4 (Resume existing) with that session.
   - **Does not exist + story/cab** → new kickoff: before Step 6, check `<session_root>/_inbox.md` for a `[spawn]` entry whose label matches the target name. If found, archive it immediately with stamp `[PICKED UP YYYY-MM-DD — <target-name>]` to `<session_root>/_inbox_archive.md` (creating the archive file if needed). Read start-impl.md, then go to Step 6.
   - **Does not exist + plugin/personal** → do NOT blank-create. These types are item-driven: fall through to Step 1 (full discovery + inbox flow) so the target can be `code`d from the inbox, or scoped fresh via `refine <topic>`.
5. Skip Steps 2, 3 entirely — no session listing, no inbox counts, no routing block. (Plugin/personal "does not exist" falls through and does NOT skip — it runs the full flow.)

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

1. **Render the listing — run the retention prune, then the list script, and display the list stdout verbatim:**
   ```bash
   ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
   # Retention prune (acp-ajudd#50) — archive completed sessions >6mo BEFORE listing, so the
   # table reflects the pruned set. Idempotent, fail-safe, and never touches in-progress/paused.
   if command -v python3 >/dev/null 2>&1 && [ -f "$ROOT/scripts/session-archive.py" ]; then
     python3 "$ROOT/scripts/session-archive.py" --session-root "<session_root>" --slug "<slug>"
   fi
   SL="$ROOT/scripts/session-list.py"
   if command -v python3 >/dev/null 2>&1 && [ -f "$SL" ]; then
     python3 "$SL" --session-root "<session_root>" --slug "<slug>" --handle "<handle>" --rebuild-index
   fi
   ```
   The prune runs first and completes before the listing (and before any commit a later step such as `migrate` might make). If it prints a `Retention: archived …` line, relay it to the user before the table so an archival is never silent.
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

**Index rebuild — automatic (acp-ajudd#49).** `_index.md` is a derived render cache, gitignored in repo-based sessions and **not committed** — so its absence (e.g. on a fresh clone or after `git pull`) is the **normal case, not an error**. The `--rebuild-index` flag above makes `session-list.py` derive any missing rows straight from the committed session files and silently persist the rebuilt cache, so the listing is always correct with no committed index. The manual `index` command is now rarely needed; if the user types `index`, just re-run the script (it re-derives and re-persists).

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

**Free-text and search:** If the user types text that doesn't match a routing action, interpret it as a natural-language filter — match against name, title, handle, status, inbox count, or any session field. Accept plain descriptions like `has inbox`, `updated by nivi`, `created by me`, `paused`, `completed this week`. Re-display the filtered table with `(filtered by '<query>')` and re-show the routing block. If no sessions match and the text looks like intent rather than a filter, proceed naturally. Keywords `mine`, `all`, `backlog`, `index`, `status`, `refine`, `code` are handled directly (see Step 2 and the `refine`/`code` entries in the shared inputs below).

**Parse combinations freely.** A single reply may include multiple signals — session number, modifiers, inbox dispositions. Examples: `1`, `code 1`, `code reviewed-work 2`, `code release`, `2 yes 4 skip`. A bare number or session name alone is treated as `code` it. Infer intent; speak up only if genuinely ambiguous.

**Shared across all project types** (defined once — the per-type blocks below add only their type-specific `Refine / Code` lines and inputs):

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
- Number or session name alone (`1`, `<name>`) → `code` it (the file decides — resume if it's an in-progress session, graduate if it's a `work` entry)
- `code <target>` → enter a **coding session** on `<target>` (see the `code` entry below)
- `mine` → filter to sessions where @created-by or @updated-by matches current user; re-display and re-show routing
- `all` → re-display including completed sessions; re-show routing
- `full` → re-display the table with the full 8-column set (adds `out` count + `created` date); re-show routing
- `status <value>` → filter to that status; re-display and re-show routing
- `refine [target]` → enter the **refinement** flow (analyze-then-record; `commands/refine.md`) — **planning, sessionless: it never creates a session file**. Applies to every type — `session:start` is the front door to refine. It writes **work** directly into it (a `work` entry for plugin/personal, a Jira story for work repos). With a topic (`refine shopify refund window`) → scope new work directly (folds in the old `new`: this is how new work begins — scope the work first). With an existing work reference (`refine acp-ajudd#12`, `refine BPT2-6429`) → resume refining that work in place (a `capture` given as target is promoted to `work`). Bare `refine` → surface resumable **`refining` work** for the slug (for plugin/personal, the `refining` `work` entries; for work repos, stories in *Gathering Requirements* via `/story:dashboard`), then resume one or start new. Direct `/session:refine` and this verb converge on the same flow. The target is **strictly the zone — no override, no target picker**: plugin/personal → a `work` entry (unambiguous); work repo → Jira story (project resolved-or-confirmed, not assumed `BPT2`); general → **nothing created** (a general repo has no system of record; only a `/session:inbox` capture can leave). Graduation = flipping the work to `ready` / *Ready For Work* — and **refine stops there; it never offers to `code`** (that is a separate, deliberate gesture). See Step 4 → **Refine — enter refinement flow**.
- `code <target>` → enter a **coding session** on `<target>` (`commands/start-impl.md` owns the mechanics). **The file decides what happens** — one verb, two outcomes: if `<target>` already has a **session file** (an in-progress session by name, or its sessions-table `#`) → **resume** it; if `<target>` is **work** (a plugin/personal `work` entry by list `<n>` or stable `[id]`; a work-repo Jira `KEY`) → **graduate** it into a *fresh* coding session — Jira story → *In Progress*, `work` entry → consume/fold-archive (a session file is born). `code` not-fully-scoped work (`new`/`refining`) **warns but never blocks** (acp-ajudd#1) — you scope as you build. This folds in the old `resume` (session) and `pick` (work). Direct `/session:start code <target>` and the fast-path share this path.
- Any other text → natural-language filter; match against name, title, handle, status, inbox count, or any field; re-display with `(filtered by '<query>')` and re-show routing

---

**Plugin project:**

Sessions are **item-driven**: new work always starts from a `work` entry in the inbox — there are no blank or plugin-named sessions. The sessions table (above) lists in-progress feature sessions to `code` (resume); the consolidated inbox below holds the `work` you `code` (graduate) and any `capture`s awaiting disposition. Scoping new work first is `refine`.

**Show the consolidated inbox.** The items were read in Step 2 from `<session_root>/_inbox.md` (the canonical inbox for this slug). List them numbered, before the routing block, using **layout B** (description-first, provenance dim on a second line — full spec in `references/inbox-convention.md`). Show each item's stable `[<id>]` before its description; flag `[spawn]` entries with ★:
```
Inbox — code work, or refine new work (N):
  1  [acp-ajudd#7]  <description>
     ↳ <slug> / <session> (<source-type>) · MM-DD
  2  [acp-ajudd#12]  <description>  · refining
     ↳ <slug> / refine (<zone>) · MM-DD
  3  [acp-ajudd#5]  ★ [spawn] <label>
     ↳ <slug> / <session> (<source-type>) · MM-DD
```
Rendering rules: the leading `N` is the ephemeral in-view position (for `code <n>`); `[<id>]` (parsed from the `## <id> · [date...]` header) is the permanent handle — reference items by ID, not position. `code` accepts either. Omit `[<id>]` for legacy items without one. Drop `<slug>` when it equals the current repo slug (only cross-repo origins show it); omit `(<source-type>)` for legacy items that lack it; tolerate spaced or unspaced `/` in the source. **Type / status marker (acp-ajudd#62):** parse the `> [type: … · status: …]` line under each header (legacy `> [status: …]` and older `> [type: story/note/data · …]` still parse — see `references/inbox-convention.md` § Inbox Model back-compat; missing line → `type: work · status: ready`). **The pickup list shows only `work`** (`status: new` / `refining` / `ready`, including spawns which are `ready`); append `· <stage>` after the description for `new`/`refining` work so still-being-scoped work is visually distinct from pickable `ready` work (`ready` gets no suffix — it's the default). **`capture`-type entries never appear here** — they aren't work to grab; they surface only via the captures-waiting glance below (acp-ajudd#10, § Captures inbound). If there is no `work`: `Inbox: none — scope new work with 'refine <topic>'`.

**Captures-waiting glance (acp-ajudd#10, § Captures inbound).** From the same Step 2 `_inbox.md` read, count `capture`-type entries (a legacy `> [status: capture]` line, or an old `type: note`/`type: data`, also reads as a `capture` — see `references/inbox-convention.md` § Inbox Model back-compat). If any exist, show a single line right after the pickup list — one glance, not monitoring:
```
Captures waiting: N — say "check captures" to read them
```
Omit the line entirely when the count is zero. Reading them is **only** on the user's request (`check captures`, or "read the capture from `<repo>`") — never auto-open them here. On that request, follow the read → disposition → archive flow in `references/inbox-convention.md` § Captures inbound: disposition each capture — **promote** (→ `refining`), **discard**, **absorb into the current session**, or **feed a refinement** — the three non-promote fates **archive** the capture.

Then output the routing block — the type-specific `Refine / Code` lines, followed by the shared **Search by** block:
```
  Refine / Code:
    refine [target]   — scope work → a `work` entry (planning, sessionless; never a session file)
                        bare = new work · refine <n|id> = edit an existing entry
    code <n|id|name>  — open a coding session (the file decides):
                        a `work` entry (by list <n> / [id]) graduates into a fresh session ·
                        an in-progress session (by name, or its table #) resumes
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `code <n>` / `code <id>` where the target is a **`work` entry** → graduate it into a fresh feature-named coding session. Reads start-impl.md, goes to Step 4 (new session): derive a feature name (confirmed once), fold the entry body into the new session, then archive-on-consume — remove the entry from the live `_inbox.md` after appending a `[CONSUMED …]` copy to `_inbox_archive.md` (fold-then-archive — the session plus the archived copy is the trail; acp-ajudd#40). `<n>` is the ephemeral inbox list position; `<id>` is the stable handle (e.g. `acp-ajudd#3`) — accept either. **If the work is not fully scoped — `status: new` or `refining`** (parsed from its `> [type: work · status: …]` line — keyed on status, *not* on origin), warn and confirm first: `[<id>] is not fully scoped (status: <new|refining>) — code it anyway? You'll scope AND build; refine first if it's big. (yes / leave it)`. A `ready` entry (the default) codes with no warning. **Never blocks** — a capable coding session decides based on size. (A `capture`-type entry isn't in this list — `code` a capture only after it's promoted to `work`.)
- `code <n>` / `code <name>` where the target is an **in-progress session** → resume it (the Plugin session resume path in Step 4). `<n>` is the sessions-table row; `<name>` is the feature name. A bare number that matches a row in **both** the sessions table and the inbox is the only genuinely ambiguous case — ask which; otherwise infer.
- `refine [target]` → scope work first (see shared inputs). **New plugin work begins here** — `refine build the <x> plugin` creates the `work` entry; `code` it when it's ready (the plugin folder/marketplace scaffolding then happens inside that coding session). Sessionless — creates no session file.
- `<n>` / `<name>` alone → `code` it (shorthand for the above).
- `reviewed` → mark plugin reviewed after loading (when the resumed session targets a plugin).
- Combinations: `code 2 reviewed` / `code acp-ajudd#12`.

---

**Work project:**

If `_inbox.md` has logical items, show compactly before the routing line using **layout B** (description-first, provenance dim below — see `references/inbox-convention.md`). Flag `[spawn]` entries with ★:
```
Global inbox (N items):
  ★ [spawn] <label>
     ↳ <slug> / <session> (<type>) · MM-DD — ready to start
  1  <description>
     ↳ <slug> / <session> (<type>) · MM-DD
```
Rendering rules: drop `<slug>` when it equals the current repo slug; omit `(<type>)` for legacy entries; tolerate spaced/unspaced `/`. **List `work` only — `status: new` / `refining` / `ready`** — exclude `capture`-type entries; they surface via the captures-waiting glance below, never as pickable work. Full inbox handling (work/done/backlog/keep) happens at Step 5.

**Captures-waiting glance (acp-ajudd#10, § Captures inbound).** From the `_inbox.md` read, count `capture`-type entries; if any, show `Captures waiting: N — say "check captures" to read them` once (omit if zero). Read/disposition them only on request (promote / discard / absorb / feed → the three non-promote fates archive), per `references/inbox-convention.md` § Captures inbound.

Then output the routing block — the type-specific `Refine / Code` lines, followed by the shared **Search by** block:
```
  Refine / Code:
    refine [target]     — scope a Jira story (Gathering Requirements; planning, sessionless)
                          bare = list your in-refinement stories · refine BPT2-XXXX = reopen one
    code <n|KEY>        — open a coding session (the file decides):
                          a story KEY graduates (→ In Progress) or resumes its session ·
                          <n> resumes an in-progress session by table row
    code cab BPT2-XXXX… — open a new CAB coding session for those stories
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `code <KEY>` (e.g. `code BPT2-6429`) → open a coding session on that story — the file decides: a session already exists → resume it; no session yet → graduate the story (transition to *In Progress*, create the feature branch, kickoff). If no key in the reply after a bare `code`, ask "Story key or URL?" as follow-up.
- `code <n>` → resume the in-progress session on sessions-table row `<n>`.
- `code cab BPT2-XXXX [...]` → new CAB coding session for those stories (routes to `/release:create-cab`); if no keys in the reply, ask "Story keys? (space-separated)" as follow-up. Bare `cab BPT2-…` is accepted as a synonym.
- `refine [target]` → scope a story first (see shared inputs) — creates/edits a Jira story in *Gathering Requirements*; never a session file. **New story work Heber hands over is already refined upstream — you'll mostly just `code BPT2-XXXX`.**
- `code <n>` on a global inbox `[spawn]` item → route through the spawn flow.

---

**Personal project:**

Identical model to plugin (per design — plugin and personal behave the same). Sessions are item-driven: new work starts from a `work` entry in the inbox, never blank.

**Show the consolidated inbox.** Entries were read in Step 2 from `<session_root>/_inbox.md` (canonical inbox for this personal project's slug). List numbered using **layout B** (description-first, provenance dim below — see `references/inbox-convention.md`), stable `[<id>]` before each description, `[spawn]` flagged with ★:
```
Inbox — code work, or refine new work (N):
  1  [<id>]  <description>
     ↳ <slug> / <session> (<source-type>) · MM-DD
  2  [<id>]  <description>  · refining
     ↳ <slug> / refine (<zone>) · MM-DD
```
Rendering rules: `N` is ephemeral position (for `code <n>`); `[<id>]` (from the `## <id> · [date...]` header) is the permanent handle — reference by ID; `code` accepts either; omit `[<id>]` for legacy entries. Drop `<slug>` when it equals the current repo slug; omit `(<source-type>)` for legacy entries; tolerate spaced/unspaced `/`. **Type / status marker (acp-ajudd#62):** parse the `> [type: … · status: …]` line under each header (legacy `> [status: …]` / older `type: story/note/data` still parse; missing → `type: work · status: ready`); the **pickup list shows only `work`** — append `· <stage>` for `new`/`refining` work; `ready` gets no suffix; **`capture`-type entries are excluded** — they surface via the captures-waiting glance, not here. See plugin block above for the full rule. If there is no `work`: `Inbox: none — scope new work with 'refine <topic>'`.

**Captures-waiting glance (acp-ajudd#10, § Captures inbound).** Identical to the plugin block: from the Step 2 `_inbox.md` read, count `capture`-type entries; if any, show `Captures waiting: N — say "check captures" to read them` once after the pickup list (omit if zero). Read/disposition them only on request, per `references/inbox-convention.md` § Captures inbound.

Then output the routing block — the type-specific `Refine / Code` lines, followed by the shared **Search by** block (identical to the plugin block):
```
  Refine / Code:
    refine [target]   — scope work → a `work` entry (planning, sessionless; never a session file)
                        bare = new work · refine <n|id> = edit an existing entry
    code <n|id|name>  — open a coding session (the file decides):
                        a `work` entry (by list <n> / [id]) graduates into a fresh session ·
                        an in-progress session (by name, or its table #) resumes
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `code <n>` / `code <id>` where the target is a **`work` entry** → graduate it into a feature-named coding session (same fold-then-archive flow as plugin: Step 4 → start-impl.md; the entry's `<id>` is preserved in the folded provenance block). Same `new`/`refining` warn/confirm as plugin — keyed on the entry's `status`, not its origin. Never blocks.
- `code <n>` / `code <name>` where the target is an **in-progress session** → resume it. Same both-lists disambiguation as plugin (ask only on a genuinely ambiguous bare number).
- `refine [target]` → scope work first (see shared inputs) — **new personal work begins here**; creates/edits a `work` entry, never a session file.
- `<n>` / `<name>` alone → `code` it (shorthand for the above).

---

**General / unknown project:**

If `_inbox.md` has entries, show a compact summary of the `work` (`status: new` / `refining` / `ready`) before the routing line. Exclude `capture`-type entries; if any exist, show one line `Captures waiting: N — say "check captures" to read them` (captures-waiting glance — acp-ajudd#10; read/disposition only on request, per `references/inbox-convention.md` § Captures inbound).

Then output the routing block — the type-specific `Refine / Code` lines, followed by the shared **Search by** block:
```
  Refine / Code:
    refine [topic]   — scope work verbally (a general repo has no system of record; planning, sessionless)
    code [name]      — open a coding session (the file decides):
                       a name with no session yet → new kickoff · an existing session → resume
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `code <name>` → open a coding session named `<name>` — the file decides: no session file with that name → new kickoff (if no name/context in the reply, ask "Name and what you're working on?" as follow-up); existing session → resume it.
- `code <n>` → resume the in-progress session on sessions-table row `<n>`.
- `refine [topic]` → scope verbally (see shared inputs); a general repo creates **no work entry** — the only outbound is a `/session:inbox` capture to another slug.

---

### 4. Act on User's Reply

Once the user replies, act immediately. **Do not read start-impl.md first** for the plugin resume path below.

**One-of-each advisory (read-only — acp-ajudd#41).** Before acting on a **`code`** action (whether it graduates a record or resumes a session), reuse the in-progress sessions already gathered in Step 2 (or `_active` + `_index.md` status — do **not** run a new scan). If an in-progress **coding session other than the one about to be started or resumed** already exists for this slug, print exactly this one line, then proceed normally:

  `Note: coding session '<name>' is already active for this slug — starting here makes two (one-of-each discipline).`

This is **read-only** — it never blocks, prompts, or asks; it just surfaces the fact once. Same "one glance, no monitoring" spirit as the captures-waiting glance (acp-ajudd#10, § Captures inbound), and it keeps the honor-system "one planning + one coding per repo" invariant (acp-ajudd#30) visible without a hook (acp-ajudd#1). It does **not** apply to the Refine path below — refine is sessionless planning and carries its own advisory in `commands/refine.md`.

---

**Refine — enter refinement flow** (any type; triggered by `refine` / `refine <topic>`):

The `session:start` refine verb and the direct `/session:refine` command converge — both run `commands/refine.md`, which owns the analyze-then-record flow and the zone-aware graduation. Refine creates **no session file** — the work-in-progress lives in the work it produces (a `refining` `work` entry for plugin/personal, a *Gathering Requirements* Jira story for work repos), so "resumable refinements" are those `refining` `work` entries, not any `refinement-*.md` file. Handle the reply:

- **`refine <topic>`** → scope new work on `<topic>` directly: read `commands/refine.md` and run it from Step 1, passing `<topic>` as the argument.
- **`refine <target>`** (a `work` entry `<id>` like `acp-ajudd#12`, or a Jira key like `BPT2-6429`) → resume refining that existing work: read `commands/refine.md` and run its Step 1 resume path with the reference. (A `capture` given here is promoted to `work` first.)
- **bare `refine`** → first surface resumable `refining` work for the slug, then route:
  1. **Plugin / personal:** list the `refining` `work` entries already read from `<session_root>/_inbox.md` in Step 2 — the entries whose `> [type: work · status: refining]` line marks them still-being-scoped (legacy `> [status: refining]` still parses; missing type/status → `type: work · status: ready`, so those are NOT listed here). Present:
     ```
     Refining (resumable):
       1  [acp-ajudd#12]  <summary>   — last touched MM-DD
     Resume one (refine <id> / <n>), or scope new: refine <new topic>
     ```
     **Work repo:** hand straight to `commands/refine.md` — its bare-`refine` path **lists your *Gathering Requirements* stories inline** (assignee OR reporter = me), so no story key need be memorized; pick one to reopen (prints its status first) or `refine <new topic>` to scope new. (refine.md owns the JQL + the status-tiered edit guard — acp-ajudd#55.)
  2. **`refine <id>` / `<n>`** → resume that work (Step 1 resume path). **`refine <new topic>`** → scope new. If there is no `refining` work, skip the list and ask the topic directly ("What are we refining? (a short topic)"), then scope new.

Either path lands in `commands/refine.md` — the front door and the direct command share one implementation.

---

**Plugin session — resume existing:**

Run **three reads in parallel:**
- Read `<session_root>/<name>.md`
- ```bash
  wc -l < "<session_root>/_history.md" 2>/dev/null && tail -n 1 "<session_root>/_history.md" 2>/dev/null || echo "0"
  ```
- Read the inbox fresh — **plugin / personal → the canonical `<session_root>/_inbox.md`** (item-driven; there is no per-session `_inbox_<name>.md`); **story / cab / general → `<session_root>/_inbox_<name>.md`** (skip if file does not exist). Count by `## <id>` header lines; skip the `> [type: … · status: …]` metadata line (legacy `> [status: …]` tolerated). **Split by type (acp-ajudd#62):** `work` (`status: new` / `refining` / `ready`) feeds the Inbox pickup list + reviewed batch below; `capture`-type entries are counted only for the **captures-waiting** line and never listed as pickable (§ Captures inbound, acp-ajudd#10).

**Security check (repo sessions only):** If `session_root` is inside a repo (not `~/.claude/memory/sessions/`), run the approval-hash check before displaying any session content. Follow the same gate as start-impl.md Step 4: compute `git hash-object`, compare to `~/.claude/memory/sessions/<slug>/<name>.approved-hash`, and require approval on first load or when the file changed since last approval. For local plugin sessions (`session_root` is under `~/.claude/`), skip this check.

Display resume block:
```
Resuming <name>
  Branch:      [branch]
  Open items (mine, N):
    - [date @handle] item
  Inbox (N items):          ← layout B; provenance dim below each entry (see inbox-convention.md); `work` only (new/refining/ready)
    1  <description> — in-progress / pending
       ↳ <slug> / <session> (<type>) · MM-DD
  Captures waiting: N — say "check captures" to read them   ← omit line if none; captures-waiting glance (acp-ajudd#10, § Captures inbound)
  Next steps (mine, N):
    - [date @handle] step
  Loaded memories (N):
    - <name>  [<label>]
  Recent commits (N):
    - [date] <sha> — <subject>
  History:     N entries — last: [condensed one-liner]
```
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
- **in-progress done** (bucket 1 — COMPLETION): archive with `[DONE YYYY-MM-DD]` stamp, remove from inbox, remove matching `[inbox] <item>` from Open items. Valid because this resume enters a coding session closing work it built.
- **in-progress keep**: no change.
- **pending work**: add `[in-progress — <session-name>, YYYY-MM-DD]` immediately after the `## [date]...` header; add `[inbox] <short desc>` to Open items.
- **pending done**: archive with `[DONE YYYY-MM-DD]` stamp. **`done` is a completion act (bucket 1) — reserve it for work that was actually built.** If you are only judging a pending item obsolete/superseded (not implementing it), that is a **planning disposition, not completion**: use **backlog** (defer) or drop it with a bucket-3 `[DISPOSITIONED YYYY-MM-DD — superseded]` archive — never `[DONE]`. See `references/inbox-convention.md` § Disposition & completion.
- **backlog** (bucket 3 — planning disposition): move to `_backlog_<name>.md` (create if needed), remove from inbox.
- **pending keep**: leave as-is.
- **reviewed yes**: update `Plugin reviewed: <current-version>` in session file.

Write state:
- `<session_root>/<name>.md` — updated-by `@<handle>`, updated date = today, Status = in-progress, Open items = post-inbox state.
- `~/.claude/memory/sessions/<slug>/_active` — session name (plain text).
- `_index.md` — find line starting with `<name> | ` and replace (or append): `<name> | @<created-by> | <created-date> | @<handle> | <today> | in-progress | <title-or-dash>`.

Read `<plugin_root>/.claude-plugin/plugin.json` and `<plugin_root>/skills/<plugin>/SKILL.md` in parallel. Ask what needs to change.

---

**Plugin / personal — `code <n>` / `code <id>` on a `work` entry** (item-driven session creation — graduation):

`code` a **`work` entry** graduates it into a fresh coding session. Read `session/commands/start-impl.md` immediately and continue from Step 4 there (New session path). `<n>` is the ephemeral list position shown in Step 3; `<id>` (e.g. `acp-ajudd#3`) is the stable handle — accept either. start-impl.md derives the feature name, folds the entry body into the new session (preserving its `<id>` in the provenance block), and archive-on-consumes the entry — a `[CONSUMED …]` copy to `_inbox_archive.md`, then removed from the live `_inbox.md`. The retired ID is never reused.

> **No `new` verb.** New plugin/personal work is not created-and-coded in one gesture (that would be coding-without-scoped-work). Scope it first with `refine <topic>` — which mints the stable ID and writes the `work` entry to `_inbox.md` — then `code` that work when it's ready. If the user insists on going straight to code on a brand-new idea, run `refine` to lay down the `work` entry first, then `code` it (a still-`refining` entry codes with the warn, per the shared `code` input).

**All other cases** — read `session/commands/start-impl.md` immediately, then continue from Step 4 there:
- Work / story / cab / general `code` action (the file decides: resume an existing session, or graduate/kickoff when none exists)
- Any case requiring a follow-up question (story key, session name)

<!-- Steps 4–9 for new sessions and non-plugin types are in start-impl.md -->
