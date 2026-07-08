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
| `refine [topic]` | `/session:start refine shopify refund` | refinement flow (Step 4 → Refine) |
| `BPT2-XXXX` (Jira story key) | `/session:start BPT2-6429` | story session |
| `CAB-XXXX` (CAB key) | `/session:start CAB-9260` | cab session |
| `cab BPT2-XXXX [...]` | `/session:start cab BPT2-6429 BPT2-6430` | new CAB for those stories |
| Existing session name | `/session:start release` | resume that session (any type, incl. legacy plugin-named + feature sessions) |

**Fast-path flow:**
1. Run `pwd`, extract slug, read `~/.claude/plugins/user-config.json` (same as Step 1). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).
2. If arg is `mine`: set `filter_mine = true`, fall through to Step 1 — full discovery with mine filter.
2a. If arg is `refine` or `refine <topic>`: resolve `session_root`/`handle` (step 1 above), then go directly to Step 4 → **Refine — enter refinement flow**, passing any `<topic>` as the refine argument. Skip Steps 1–3.
3. Derive session type and target name from the arg (story key → type=story, name=BPT2-XXXX; CAB key → type=cab; any other bare token → treat as a session NAME to resume).
4. Check whether `<session_root>/<name>.md` exists:
   - **Exists + plugin session** → go directly to the Plugin session resume path in Step 4 (no start-impl.md read needed).
   - **Exists + other type** → read start-impl.md, go directly to Step 4 (Resume existing) with that session.
   - **Does not exist + story/cab** → new kickoff: before Step 6, check `<session_root>/_inbox.md` for a `[spawn]` entry whose label matches the target name. If found, archive it immediately with stamp `[PICKED UP YYYY-MM-DD — <target-name>]` to `<session_root>/_inbox_archive.md` (creating the archive file if needed). Read start-impl.md, then go to Step 6.
   - **Does not exist + plugin/personal** → do NOT blank-create. These types are item-driven: fall through to Step 1 (full discovery + inbox flow) so the name can be picked from the inbox or started via `new <description>`.
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

**Free-text and search:** If the user types text that doesn't match a routing action, interpret it as a natural-language filter — match against name, title, handle, status, inbox count, or any session field. Accept plain descriptions like `has inbox`, `updated by nivi`, `created by me`, `paused`, `completed this week`. Re-display the filtered table with `(filtered by '<query>')` and re-show the routing block. If no sessions match and the text looks like intent rather than a filter, proceed naturally. Keywords `mine`, `all`, `backlog`, `index`, `status`, `refine` are handled directly (see Step 2 and the refine entry in the shared inputs below).

**Parse combinations freely.** A single reply may include multiple signals — session number, modifiers, inbox dispositions. Examples: `1`, `resume 1`, `resume session reviewed work 2`, `start release`, `2 yes 4 skip`. Infer intent; speak up only if genuinely ambiguous.

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
- `refine [topic]` → enter the **refinement** flow (analyze-then-record; `commands/refine.md`). Applies to every type — `session:start` is the front door to refine. Refine creates **no session file**; it writes the work directly into the record (an inbox item for plugin/personal, a Jira story for work repos). With a topic (`refine shopify refund window`) → scope new work directly. With an existing record reference (`refine acp-ajudd#12`, `refine BPT2-6429`) → resume refining that record in place. Bare `refine` → surface resumable **`refining` records** for the slug (for plugin/personal, the `refining` inbox items; for work repos, stories in *Gathering Requirements* via `/story:dashboard`), then resume one or start new. Direct `/session:refine` and this verb converge on the same flow. The record target is **strictly the zone — no override, no target picker**: plugin/personal → inbox item (unambiguous); work repo → Jira story (project resolved-or-confirmed, not assumed `BPT2`); general → **no record created** (a general repo has no system of record; only a `/session:inbox` note can leave). Graduation = flipping the record to `ready` / *Ready For Work*. See Step 4 → **Refine — enter refinement flow**.
- Any other text → natural-language filter; match against name, title, handle, status, inbox count, or any field; re-display with `(filtered by '<query>')` and re-show routing

---

**Plugin project:**

Sessions are **item-driven**: new work always starts from an inbox item — there are no blank or plugin-named sessions. The sessions table (above) lists in-progress feature sessions to `resume`; the consolidated inbox below is what you `pick` from.

**Show the consolidated inbox.** The items were read in Step 2 from `<session_root>/_inbox.md` (the canonical inbox for this slug). List them numbered, before the routing block, using **layout B** (description-first, provenance dim on a second line — full spec in `references/inbox-convention.md`). Show each item's stable `[<id>]` before its description; flag `[spawn]` entries with ★:
```
Inbox — pick up or describe new work (N):
  1  [acp-ajudd#7]  <description>
     ↳ <slug> / <session> (<source-type>) · MM-DD
  2  [acp-ajudd#12]  <description>  · refining
     ↳ <slug> / refine (<zone>) · MM-DD
  3  [acp-ajudd#5]  ★ [spawn] <label>
     ↳ <slug> / <session> (<source-type>) · MM-DD
```
Rendering rules: the leading `N` is the ephemeral in-view position (for `pick <n>`); `[<id>]` (parsed from the `## <id> · [date...]` header) is the permanent handle — reference items by ID, not position. `pick` accepts either. Omit `[<id>]` for legacy items without one. Drop `<slug>` when it equals the current repo slug (only cross-repo origins show it); omit `(<source-type>)` for legacy items that lack it; tolerate spaced or unspaced `/` in the source. **Status marker:** parse the `> [status: …]` line under each header (legacy `> [type: … · status: …]` still parses — the `type` word is ignored; missing line → `status: ready`). Append `· refining` after the description for `status: refining` items, so still-being-scoped work is visually distinct from pickable `ready` work; `ready` items get no suffix (it's the default). **The pickup list shows only promoted captures — `status: refining` / `status: ready`** (including spawns, which are `ready`). Un-promoted `status: capture` items **never appear here** — they aren't work to grab yet; they surface only via the captures-waiting glance below (acp-ajudd#10, § Captures inbound). If there are no promoted captures: `Inbox: none — describe new work with 'new <description>'`.

**Captures-waiting glance (acp-ajudd#10, § Captures inbound).** From the same Step 2 `_inbox.md` read, count un-promoted captures — items at `status: capture` (legacy lines without a modern status also read as `capture` — see `references/inbox-convention.md` § Item Model back-compat). If any exist, show a single line right after the pickup list — one glance, not monitoring:
```
Captures waiting: N — say "check captures" to read them
```
Omit the line entirely when the count is zero. Reading them is **only** on the user's request (`check captures`, or "read the capture from `<repo>`") — never auto-open them here. On that request, follow the read → disposition → archive flow in `references/inbox-convention.md` § Captures inbound: disposition each capture — **promote** (→ `refining`), **discard**, **absorb into the current session**, or **feed a refinement** — the three non-promote fates **archive** the capture.

Then output the routing block — the type-specific `Start / Resume` lines, followed by the shared **Search by** block:
```
  Start / Resume:
    resume <n>        — resume an in-progress session (table number above)
    pick <n>          — start a session from inbox item <n>
    new <description> — start a session for new work (adds it to the inbox, then picks it up)
    refine [topic]    — scope work first (analyze-then-record → inbox item); lists resumable refinements
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `pick <n>` → create a feature-named session from inbox item <n>. Reads start-impl.md, goes to Step 4 (new session): derive a feature name (confirmed once), fold the item body into the new session, then archive-on-consume — remove the item from the live `_inbox.md` after appending a `[CONSUMED …]` copy to `_inbox_archive.md` (fold-then-archive — the session plus the archived copy is the trail; acp-ajudd#40). **If the item is not fully scoped — `status: capture` or `status: refining`** (parsed from its `> [status: …]` line — legacy `type:` tolerated and ignored; keyed on status, *not* on origin), warn and confirm first: `[<id>] is not fully scoped (status: <capture|refining>) — pick it up anyway? You'll scope AND build; refine first if it's big. (yes / leave it)`. A `ready` item (the default) is picked with no warning. **Never blocks** — a capable coding session decides based on size.
- `new <description>` → append `<description>` as a new item to `<session_root>/_inbox.md` with a `> [status: ready]` line (a quick-captured task is immediately pickable — see `references/inbox-convention.md` § Item Model), then immediately run the same `pick` flow on it — one creation path, no separate ad-hoc branch. (Scaffolding a brand-new plugin is just `new build the <x> plugin`: it creates a feature session, and the plugin folder/marketplace work happens inside it.)
- `resume <n>` / `<n>` / `<name>` → resume an existing in-progress session.
- `reviewed` → mark plugin reviewed after loading (when the resumed session targets a plugin).
- Combinations: `resume 2 reviewed` / `pick 3`.

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
Rendering rules: drop `<slug>` when it equals the current repo slug; omit `(<type>)` for legacy items; tolerate spaced/unspaced `/`. **List promoted captures only — `status: refining` / `status: ready`** — exclude un-promoted `status: capture` items; they surface via the captures-waiting glance below, never as pickable work. Full inbox handling (work/done/backlog/keep) happens at Step 5.

**Captures-waiting glance (acp-ajudd#10, § Captures inbound).** From the `_inbox.md` read, count un-promoted `status: capture` items; if any, show `Captures waiting: N — say "check captures" to read them` once (omit if zero). Read/disposition them only on request (promote / discard / absorb / feed → the three non-promote fates archive), per `references/inbox-convention.md` § Captures inbound.

Then output the routing block — the type-specific `Start / Resume` lines, followed by the shared **Search by** block:
```
  Start / Resume:
    resume <n>       — resume by number (e.g. resume 2)
    start story      — start a new story — you'll give a key or URL
    start cab        — start a new CAB — you'll give story keys
    refine [topic]   — scope work first (analyze-then-record → Jira story, project confirmed); lists resumable refinements
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `start story` → route to new story; if no key in reply, ask "Story key or URL?" as follow-up
- `start story BPT2-XXXX` → route directly with that key
- `start cab` → route to new CAB; if no keys in reply, ask "Story keys? (space-separated)" as follow-up
- `work <n>` on a global inbox `[spawn]` item → route through spawn flow

---

**Personal project:**

Identical model to plugin (per design — plugin and personal behave the same). Sessions are item-driven: new work starts from an inbox item, never blank.

**Show the consolidated inbox.** Items were read in Step 2 from `<session_root>/_inbox.md` (canonical inbox for this personal project's slug). List numbered using **layout B** (description-first, provenance dim below — see `references/inbox-convention.md`), stable `[<id>]` before each description, `[spawn]` flagged with ★:
```
Inbox — pick up or describe new work (N):
  1  [<id>]  <description>
     ↳ <slug> / <session> (<source-type>) · MM-DD
  2  [<id>]  <description>  · refining
     ↳ <slug> / refine (<zone>) · MM-DD
```
Rendering rules: `N` is ephemeral position (for `pick <n>`); `[<id>]` (from the `## <id> · [date...]` header) is the permanent handle — reference by ID; `pick` accepts either; omit `[<id>]` for legacy items. Drop `<slug>` when it equals the current repo slug; omit `(<source-type>)` for legacy items; tolerate spaced/unspaced `/`. **Status marker:** parse the `> [status: …]` line under each header (legacy `> [type: … · status: …]` still parses — `type` ignored; missing → `status: ready`); append `· refining` for `status: refining` items; `ready` gets no suffix. **Pickup list is promoted captures only — `status: refining` / `status: ready`** — exclude un-promoted `status: capture` items; they surface via the captures-waiting glance, not here. See plugin block above for the full rule. If empty: `Inbox: none — describe new work with 'new <description>'`.

**Captures-waiting glance (acp-ajudd#10, § Captures inbound).** Identical to the plugin block: from the Step 2 `_inbox.md` read, count un-promoted `status: capture` items; if any, show `Captures waiting: N — say "check captures" to read them` once after the pickup list (omit if zero). Read/disposition them only on request, per `references/inbox-convention.md` § Captures inbound.

Then output the routing block — the type-specific `Start / Resume` lines, followed by the shared **Search by** block:
```
  Start / Resume:
    resume <n>        — resume an in-progress session (table number above)
    pick <n>          — start a session from inbox item <n>
    new <description> — start a session for new work (adds it to the inbox, then picks it up)
    refine [topic]    — scope work first (analyze-then-record → inbox item); lists resumable refinements
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `pick <n>` (or `pick <id>`) → create a feature-named session from inbox item <n> / the item with stable id `<id>` (same fold-then-archive flow as plugin: Step 4 → start-impl.md; the item's `<id>` is preserved in the folded provenance block). Same `refining` warn/confirm as plugin — keyed on the item's `status`, not its origin.
- `new <description>` → issue a stable ID (`inbox-id.py next --slug <slug> --handle <handle>`), append to `<session_root>/_inbox.md` with the `## <id> · [date...]` header plus a `> [status: ready]` line, then run the same `pick` flow.
- `resume <n>` / `<n>` / `<name>` → resume an existing in-progress session.

---

**General / unknown project:**

If `_inbox.md` has items, show a compact summary of the promoted captures (`status: refining` / `status: ready`) before the routing line. Exclude un-promoted `status: capture` items; if any exist, show one line `Captures waiting: N — say "check captures" to read them` (captures-waiting glance — acp-ajudd#10; read/disposition only on request, per `references/inbox-convention.md` § Captures inbound).

Then output the routing block — the type-specific `Start / Resume` lines, followed by the shared **Search by** block:
```
  Start / Resume:
    resume <n>       — resume by number
    start            — start a new session — you'll give a name and context
    refine [topic]   — scope work first (analyze-then-record; general repo = no record created, scope only); lists resumable refinements
```

**Type-specific accepted inputs** (plus the shared inputs above):
- `start` → route to new session; if no name/context in reply, ask "Name and what you're working on?" as follow-up

---

### 4. Act on User's Reply

Once the user replies, act immediately. **Do not read start-impl.md first** for the plugin resume path below.

**One-of-each advisory (read-only — acp-ajudd#41).** Before acting on a **coding-session** action (`pick` / `new` / `resume`), reuse the in-progress sessions already gathered in Step 2 (or `_active` + `_index.md` status — do **not** run a new scan). If an in-progress **coding session other than the one about to be started or resumed** already exists for this slug, print exactly this one line, then proceed normally:

  `Note: coding session '<name>' is already active for this slug — starting here makes two (one-of-each discipline).`

This is **read-only** — it never blocks, prompts, or asks; it just surfaces the fact once. Same "one glance, no monitoring" spirit as the captures-waiting glance (acp-ajudd#10, § Captures inbound), and it keeps the honor-system "one planning + one coding per repo" invariant (acp-ajudd#30) visible without a hook (acp-ajudd#1). It does **not** apply to the Refine path below — refine is sessionless planning and carries its own advisory in `commands/refine.md`.

---

**Refine — enter refinement flow** (any type; triggered by `refine` / `refine <topic>`):

The `session:start` refine verb and the direct `/session:refine` command converge — both run `commands/refine.md`, which owns the analyze-then-record flow and the zone-aware graduation. Refine creates **no session file** — the work-in-progress lives in the record it produces (a `refining` inbox item for plugin/personal, a *Gathering Requirements* Jira story for work repos), so "resumable refinements" are those `refining` records, not any `refinement-*.md` file. Handle the reply:

- **`refine <topic>`** → scope new work on `<topic>` directly: read `commands/refine.md` and run it from Step 1, passing `<topic>` as the argument.
- **`refine <record>`** (an inbox item `<id>` like `acp-ajudd#12`, or a Jira key like `BPT2-6429`) → resume refining that existing record: read `commands/refine.md` and run its Step 1 resume path with the reference.
- **bare `refine`** → first surface resumable `refining` records for the slug, then route:
  1. **Plugin / personal:** list the `refining` inbox items already read from `<session_root>/_inbox.md` in Step 2 — the items whose `> [status: refining]` line marks them still-being-scoped (legacy `> [type: … · status: refining]` still parses; missing status → `ready`, so those are NOT listed here). Present:
     ```
     Refining (resumable):
       1  [acp-ajudd#12]  <summary>   — last touched MM-DD
     Resume one (refine <id> / <n>), or scope new: refine <new topic>
     ```
     **Work repo:** point at the story tooling instead — refining stories are Jira objects: "Your in-refinement stories are in *Gathering Requirements* — see `/story:dashboard`, or `refine BPT2-XXXX` to reopen one." 
  2. **`refine <id>` / `<n>`** → resume that record (Step 1 resume path). **`refine <new topic>`** → scope new. If there are no `refining` records, skip the list and ask the topic directly ("What are we refining? (a short topic)"), then scope new.

Either path lands in `commands/refine.md` — the front door and the direct command share one implementation.

---

**Plugin session — resume existing:**

Run **three reads in parallel:**
- Read `<session_root>/<name>.md`
- ```bash
  wc -l < "<session_root>/_history.md" 2>/dev/null && tail -n 1 "<session_root>/_history.md" 2>/dev/null || echo "0"
  ```
- Read the inbox fresh — **plugin / personal → the canonical `<session_root>/_inbox.md`** (item-driven; there is no per-session `_inbox_<name>.md`); **story / cab / general → `<session_root>/_inbox_<name>.md`** (skip if file does not exist). Count by `## <id>` header lines; skip the `> [status: …]` metadata line (legacy `> [type: … · status: …]` tolerated). **Split by status:** promoted captures (`status: refining` / `status: ready`) feed the Inbox pickup list + reviewed batch below; un-promoted `status: capture` items are counted only for the **captures-waiting** line and never listed as pickable (§ Captures inbound, acp-ajudd#10).

**Security check (repo sessions only):** If `session_root` is inside a repo (not `~/.claude/memory/sessions/`), run the approval-hash check before displaying any session content. Follow the same gate as start-impl.md Step 4: compute `git hash-object`, compare to `~/.claude/memory/sessions/<slug>/<name>.approved-hash`, and require approval on first load or when the file changed since last approval. For local plugin sessions (`session_root` is under `~/.claude/`), skip this check.

Display resume block:
```
Resuming <name>
  Branch:      [branch]
  Open items (mine, N):
    - [date @handle] item
  Inbox (N items):          ← layout B; provenance dim below each item (see inbox-convention.md); promoted captures only (refining/ready)
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

**Plugin / personal — `pick <n>` or `new <description>`** (item-driven session creation):
- `new <description>`: first **issue a stable ID** (home slug = current slug, namespaced by handle), then append the description as a new item to `<session_root>/_inbox.md` using the standard header format (`## <id> · [YYYY-MM-DD @<handle>] from <slug>/start (<type>) — <description>`, where `<type>` is the current repo's session type), then treat it exactly like `pick` on that just-written item:
  ```bash
  IDT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}/scripts/inbox-id.py"
  if command -v python3 >/dev/null 2>&1; then python3 "$IDT" next --slug "<slug>" --handle "<handle>"; else python "$IDT" next --slug "<slug>" --handle "<handle>"; fi   # e.g. acp-ajudd#7, increments the counter
  ```
  (Fallback `<acronym>-<handle>#?` if python3/script unavailable — never block. See `references/inbox-convention.md` § Stable IDs.)
- `pick <n>` (or `pick <id>`): read `session/commands/start-impl.md` immediately and continue from Step 4 there (New session path). `<n>` is the ephemeral list position shown in Step 3; `<id>` (e.g. `acp-ajudd#3`) is the stable handle — accept either. start-impl.md derives the feature name, folds the item body into the new session (preserving its `<id>` in the provenance block), and archive-on-consumes the item — a `[CONSUMED …]` copy to `_inbox_archive.md`, then removed from the live `_inbox.md`. The retired ID is never reused.

**All other cases** — read `session/commands/start-impl.md` immediately, then continue from Step 4 there:
- Work / story / cab / general session (resume or new)
- Any case requiring a follow-up question (story key, session name)

<!-- Steps 4–9 for new sessions and non-plugin types are in start-impl.md -->
