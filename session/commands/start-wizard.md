---
name: start-wizard
description: Session start — one wizard flow for all zones (Step 2 onward). Loaded by start.md's dispatcher once zone and the config-cascade are resolved, when startFlow == wizard.
---

# Session Start — Wizard Flow (Step 2 onward)

Loaded by `start.md` (the dispatcher) once zone and the config-cascade have been resolved, for **every zone** (`plugin` | `story` | `cab` | `personal` | `general`) when `startFlow == wizard` (the default). Context already in scope: `slug`, `session_root`, `handle`, `zone`, and `filter_mine` (if Step 0's `mine` fast-path set it).

**One file, zone-aware inside — not a per-zone split (acp-ajudd#124, re-entry of halted #121, folds #122).** The wizard works the same way everywhere; the *only* per-zone difference is how many options Step 2 offers and what a `code`/`refine` target looks like. This supersedes the standalone `start-work.md` (deleted — its story/cab logic is folded in below) and the never-built `start-plugin-wizard.md` (not created).

**No listing by default, in any zone.** Unlike the classic flow, this file never renders the sessions table or the inbox as a first move — only a one-line captures-waiting glance (plugin/personal). A full listing is one `search`/`list` away. **Never front data-drift** — if the reconcile/approval-hash checks inside `start-impl.md` surface one during a resume, let it surface there, lightly, after the user has already picked a target.

**Fast-path args never reach this file** — `start.md`'s own Step 0 resolves `code BPT2-XXXX` / a bare key / an existing session name / `refine`/`dispatch`/`capture` directly, skipping Steps 2–3 entirely. This file only runs on a **bare** `/session:start` (no argument).

## Instructions

### 2. Ask: role prompt (zone-aware)

**Captures-waiting glance (plugin/personal only).** Before asking, render the consolidated inbox (`inbox-render.py`, auto-migrates) and count `capture`-type entries — this is a count, not a listing:
```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
RENDER="$ROOT/scripts/inbox-render.py"
if command -v python3 >/dev/null 2>&1 && [ -f "$RENDER" ]; then
  python3 "$RENDER" render --session-root "<session_root>" --slug "<slug>"
fi
```
If any `capture`-type entries exist, show `Captures waiting: N — say "check captures" to read them` right before the prompt below (omit if zero). Story/cab/general zones skip this entirely — they have no consolidated inbox.

**Prompt — options vary by zone only:**

- **story, cab, general** (no inbox; 2 options):
  ```
  refine or code?
  ```
- **plugin, personal** (item-driven inbox; 4 options):
  ```
  refine, code, dispatch, or capture?
  ```

Wait for one free-text reply. **Do not use AskUserQuestion.**

**Infer eagerly before falling back to the plain options** — the whole point of this flow is speed, so don't make the user answer twice when the first reply already carries the answer:
- A bare Jira story key (`BPT2-6429`) or CAB key (`CAB-456`) (story/cab/general zone) → implicit `code` on that key; skip straight to the **code path — story/cab zone** below with it.
- A bare inbox `[id]` (e.g. `acp-ajudd#7`), a list `<n>` (only meaningful after a `search`), or an existing session name (plugin/personal zone) → implicit `code` on that target; skip straight to the **code path — plugin/personal zone** below.
- `code <target>` / `refine <target>` / `cab <keys>` → explicit, skip straight to the matching Step 3 branch with the target already carried.
- `dispatch` / `capture` (plugin/personal only) → skip straight to that role below.
- `search` / `list` → run the on-demand listing for this zone (see the zone's code branch below), then re-ask the same prompt.
- Bare `refine` / `code` / `dispatch` / `capture` → go to the matching Step 3 branch with no target.
- Anything else that doesn't parse → ask once more, the same prompt (do not guess a third way).

---

### 3. Act by role

**`dispatch`** (plugin/personal only) → read `commands/dispatch.md` and run it (sessionless, assume the dispatch role, orient on the inbox). Not offered in story/cab/general — if typed there anyway, note `dispatch is plugin/personal only` and re-ask the Step 2 prompt.

**`capture`** (plugin/personal only) → read `commands/capture.md` and run it (sessionless, assume the capture role, bank ideas). Same zone restriction as `dispatch`.

---

**`refine` path** (any zone):

If no target was already carried in from Step 2, ask:
- story, cab → `story key to refine, or a new topic?`
- plugin, personal → `item id to refine, or a new topic?`
- general → `what are we refining? (a topic)`

Wait for one free-text reply.

- **A story/CAB key, or an item `[id]`** (story/cab/plugin/personal only — general has neither) → read `commands/refine.md` and run its Step 1 **resume** path with that reference (prints status first, applies the status-tiered edit guard for stories, continues refining in place).
- **A topic / free text** → read `commands/refine.md` and run its Step 1 **new** path, passing the topic as the argument. Scopes a brand-new Jira story in *Gathering Requirements* for story/cab; a new `work` entry for plugin/personal; general creates nothing (refine.md's own zone-aware graduation owns each case — this file never branches on the outcome).
- **`search` / `list`** (story/cab/plugin/personal only) → hand straight to `commands/refine.md`'s bare-`refine` path: for story/cab it lists the user's own *Gathering Requirements* stories inline (assignee OR reporter = me); for plugin/personal it lists `refining` `work` entries for the slug. No separate listing logic needed here — refine already owns it. General has no resumable list — any reply there is just a topic.
- **Bare reply / nothing usable** → hand straight to `commands/refine.md`'s bare-`refine` path (same as `search` above — it already asks the topic directly if the list is empty). For general, just ask the topic directly if the reply was empty.

Refine is sessionless — this path never creates a session file, never touches `_active`, and never offers to `code` (acp-ajudd#56).

---

**`code` path — story / cab zone:**

If no target was already carried in from Step 2, ask:
```
story key (e.g. BPT2-6429)? — or new / search
```
Wait for one free-text reply.

- **A story key or CAB key** (`BPT2-6429`, `cab BPT2-6429 BPT2-6430`) → the file decides, same as everywhere else in this plugin:
  - `cab <keys>` / bare `cab <keys>` → route to `/release:create-cab` (new CAB coding session for those stories).
  - A single story key → check whether `<session_root>/<key>.md` exists:
    - **Exists** → read `start-impl.md`, go directly to its **Step 4 (Resume existing)** with that session. Any stale index-vs-file drift surfaces here — via the approval-hash check already built into that step — never before now.
    - **Does not exist** → new kickoff: render the consolidated inbox (`inbox-render.py`, auto-migrates) and check for a `[spawn]` entry whose label matches the key. If found, archive it immediately with stamp `[PICKED UP YYYY-MM-DD — <key>]` to `<session_root>/_inbox_archive.md` (create if needed), then delete its `_inbox/<id>.md` file (acp-ajudd#102). Read `start-impl.md`, then go to its **Step 6** (Establish Session Identity) → **Story — new kickoff** (Step 9): `getJiraIssue` → transition to *In Progress* → create feature branch → epic check → memory scan offer.
- **`new`** → new-story path. This repo has no story yet, but the user wants to code, not scope in Jira first:
  1. Ask only for what's not already inferable from conversation context: **Summary** (short title) — everything else defaults the same way `/story:create` does (Work Allocation Type inferred from context, Expenditures: Opex, Assignee: current user from `user-config.json` → `user.jiraAccountId`, initial status: Ready For Work).
  2. Create the issue via the same two-call pattern `/story:create` uses (`createJiraIssue` for summary + required fields, then immediately `editJiraIssue` for the markdown description) — project `BPT2`, issue type `Story`, cloudId `9de6eb2b-2683-44e6-89ff-c622027e09b4`.
  3. Once the key exists, treat it exactly like a fresh key with no session file above: read `start-impl.md`, go to Step 6 → **Story — new kickoff** (transitions Ready For Work → In Progress as part of that same flow).
- **`search`** → the on-demand listing (the **only** place in this branch that renders one): run the classic flow's Step 2 render calls verbatim —
  ```bash
  ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
  SL="$ROOT/scripts/session-list.py"
  if command -v python3 >/dev/null 2>&1 && [ -f "$SL" ]; then
    python3 "$SL" --session-root "<session_root>" --slug "<slug>" --handle "<handle>" --rebuild-index
  fi
  RENDER="$ROOT/scripts/inbox-render.py"
  if command -v python3 >/dev/null 2>&1 && [ -f "$RENDER" ]; then
    python3 "$RENDER" render --session-root "<session_root>" --slug "<slug>"
  fi
  ```
  Display the sessions-table stdout verbatim (completed sessions stay hidden) and, if the rendered inbox has logical items, the compact inbox summary (layout B, per `references/inbox-convention.md`). Then re-ask `story key (e.g. BPT2-6429)? — or new` (drop `search` from the reprompt).
- **Anything else** → treat as a nudge, not a filter (this flow doesn't support free-text filtering — that's what `search` is for): ask once more, `Story key, or new / search?`.

---

**`code` path — general zone:**

If no target was already carried in from Step 2, ask:
```
name — new session or resume?
```
Wait for one free-text reply.

- Check whether `<session_root>/<name>.md` exists:
  - **Exists** → read `start-impl.md`, go directly to its **Step 4 (Resume existing)** with that session.
  - **Does not exist** → new kickoff: read `start-impl.md`, go to its Step 6 (Establish Session Identity → general). If what the session is for isn't already clear from conversation context, ask "What are we working on?" and a category (Research / Prototype / Training / Other) as that step requires.
- **`search` / `list`** → run the sessions-table render only (`session-list.py`, general zone has no consolidated inbox), display verbatim, then re-ask `name — new session or resume?` (drop `search` from the reprompt).
- **Anything else** → ask once more.

---

**`code` path — plugin / personal zone:**

Sessions are item-driven: a `code` target is either an inbox `work` entry (by list `<n>` or stable `[id]`) that graduates into a fresh session, or an existing in-progress session (by name, or its sessions-table row) that resumes. There is no `new` verb here — new plugin/personal work is scoped first via `refine`, never created-and-coded in one gesture.

If no target was already carried in from Step 2, ask:
```
inbox item # / id / name? — or search
```
Wait for one free-text reply.

**One-of-each advisory (read-only — acp-ajudd#41).** Before acting on the reply below, check `_active` + `_index.md` for an in-progress coding session other than the one about to be started/resumed (no new scan). If one exists, print exactly `Note: coding session '<name>' is already active for this slug — starting here makes two (one-of-each discipline).`, then proceed normally. This is read-only — it never blocks.

- **A `[<id>]` or list `<n>`** (only meaningful after a `search` render, or already known from a handoff/capture) that resolves to a **`work` entry** → graduate it into a fresh session: read `session/commands/start-impl.md` immediately and continue from its **Step 4 → "Work Pickup (plugin / personal only)"** section — maturity guard, injection scan, feature-name derivation, fold, archive-on-consume. `<n>` is the ephemeral list position (only valid right after a `search`); `<id>` is the stable handle — accept either.
- **A name (or `<n>` against the sessions table)** that resolves to an **in-progress session** → resume it: read `session/commands/start-impl.md` immediately and continue from its **Step 4 (Resume existing)** with that session — the same "Plugin session resume" mechanics `start-classic.md` documents (security check, resume block, inbox + reviewed batch — script-rendered via `resume-block.py`, acp-ajudd#123).
- **`search` / `list`** → the on-demand listing (the **only** place in this branch that renders one): run the same Step 2 render calls as above (`session-list.py` + `inbox-render.py`), then display them using `inbox-render.py`'s `pickup` mode — the same script `start-classic.md`'s Plugin/Personal blocks call (acp-ajudd#123) — numbered pickup list (layout B, `[<id>]` before each description, `[spawn]` flagged with ★, `work`-type only, `· <stage>` suffix for `new`/`refining`), plus the captures-waiting glance if any. Then re-ask `inbox item # / id / name?` (drop `search` from the reprompt).
- **Anything else** → ask once more.

<!-- Steps 4–9 (session file writes, Teams chat setup, Establish Session Identity, and everything after a target resolves) live in start-impl.md and are unchanged by this file — the wizard only changes how the target is gathered. -->
