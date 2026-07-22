---
name: start-wizard
description: Session start — one wizard flow for all zones (Step 2 onward). Loaded by start.md's dispatcher after the role-prompt reply is already in hand and session_root/handle have just been resolved, when startFlow == wizard.
---

# Session Start — Wizard Flow (Step 2 onward)

Loaded by `start.md` (the dispatcher) for **every zone** (`plugin` | `story` | `cab` | `personal` | `general`) when `startFlow == wizard` (the default) — **after** the zone-aware role prompt has already been asked and answered in `start.md` Step 1a, and `session_root`/`handle` have just been resolved in Step 1b (acp-ajudd#127). Context already in scope: `slug`, `session_root`, `handle`, `zone`, `filter_mine` (if Step 0's `mine` fast-path set it), and the reply.

**One file, zone-aware inside — not a per-zone split (acp-ajudd#124, re-entry of halted #121, folds #122).** The wizard works the same way everywhere; the *only* per-zone difference is how many options the role prompt offers and what a `code`/`refine` target looks like. This supersedes the standalone `start-work.md` (deleted — its story/cab logic is folded in below) and the never-built `start-plugin-wizard.md` (not created).

**No listing before the role is picked; the relevant chunk renders once it is (acp-ajudd#128).** Step 1 (the role prompt in `start.md`) stays a lean, un-rendered ask — no table, no inbox, before the user has even said `refine` or `code`. But a bare `code`/`refine` reaching Step 3 below with no target is not answered with a bare question into a void either: the file renders the relevant menu chunk first — the in-progress sessions list and/or the pickable inbox items, whichever apply to the zone — *then* asks. `search`/`list` still exists as an explicit refresh, not the only way to ever see the list (that was the over-minimization #128 corrects — #126/#127 stayed intact: still no AskUserQuestion, still no auto-resuming a target from inference). **Never front data-drift** — if the reconcile/approval-hash checks inside `start-impl.md` surface one during a resume, let it surface there, lightly, after the user has already picked a target.

**Fast-path args never reach this file** — `start.md`'s own Step 0 resolves `code BPT2-XXXX` / a bare key / an existing session name / `refine`/`dispatch`/`capture` directly, skipping Steps 2–3 entirely. This file only runs on a **bare** `/session:start` (no argument).

**On `code` with no explicit target, always render the list then ask — never infer (acp-ajudd#126, #128).** Every ask in this file — every target-gathering ask in Step 3 below — is plain free-text; **never AskUserQuestion**, no exceptions. And when `code` reaches Step 3 with no target already carried in from Step 2, the render-then-ask sequence must always fire: **never auto-infer the target from the current git branch** (or any other environmental signal) and silently resume it. The rendered sessions list marks a current-git-branch session with `(current branch)` — one highlighted row among the rest, never the only thing shown and never auto-selected; resuming it still requires the user's own reply, same as any other row. The "the file decides" existence-check auto-resolve applies only to a fast-path arg (`code BPT2-XXXX`) that skipped this file entirely — never to a bare `code` answered inside the wizard.

**The Step 2 role prompt already fired in `start.md` (acp-ajudd#127) — this file starts from the reply.** `start.md`'s Step 1a asks the zone-aware prompt (`refine or code?` / `refine, code, dispatch, or capture?`) right after resolving zone + startFlow, *before* `session_root`/`handle` are resolved and before this file is even read. By the time this file loads (Step 1b), the reply is already in hand and `session_root`/`handle` have just been resolved. This file's job starts with the captures-waiting glance and eager inference below — never re-print the prompt.

## Instructions

### 2. Process the Reply (zone-aware)

**Captures-waiting glance (plugin/personal only).** First thing this file does — render the consolidated inbox (`inbox-render.py`, auto-migrates) and count `capture`-type entries — this is a count, not a listing:
```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
RENDER="$ROOT/scripts/inbox-render.py"
if command -v python3 >/dev/null 2>&1 && [ -f "$RENDER" ]; then
  python3 "$RENDER" render --session-root "<session_root>" --slug "<slug>"
fi
```
If any `capture`-type entries exist, show `Captures waiting: N — say "check captures" to read them` before acting on the reply (omit if zero). **Omit it here too when the reply is bare `code` with no target** — the plugin/personal code-path render (Step 3 below) shows the pickup list, whose own trailing line already carries this count; printing it twice in the same turn is noise, not a second signal. Story/cab/general zones skip this entirely — they have no consolidated inbox.

**Infer eagerly before falling back to the plain options** — the whole point of this flow is speed, so don't make the user answer twice when the first reply already carries the answer:
- A bare Jira story key (`BPT2-6429`) or CAB key (`CAB-456`) (story/cab/general zone) → implicit `code` on that key; skip straight to the **code path — story/cab zone** below with it.
- A bare inbox `[id]` (e.g. `acp-ajudd#7`), a list `<n>` (only meaningful after a `search`), or an existing session name (plugin/personal zone) → implicit `code` on that target; skip straight to the **code path — plugin/personal zone** below.
- `code <target>` / `refine <target>` / `cab <keys>` → explicit, skip straight to the matching Step 3 branch with the target already carried.
- `release <target>` (story/cab zone only — acp-ajudd#158) → explicit, skip straight to the **release path — story/cab zone** below with the target already carried. `cab <keys>` / `code cab <keys>` are still accepted (they route into the same code-path CAB handling as always) — `release` is just the new primary spelling.
- `dispatch` / `capture` (plugin/personal only) → skip straight to that role below.
- `search` / `list` → run the on-demand listing for this zone (see the zone's code branch below), then re-ask the same role prompt (the zone-aware ask from `start.md` Step 1a).
- Bare `refine` / `code` / `release` / `dispatch` / `capture` → go to the matching Step 3 branch with no target.
- Anything else that doesn't parse → ask once more, the same role prompt (do not guess a third way).

---

### 3. Act by role

**`dispatch`** (plugin/personal only) → read `commands/dispatch.md` and run it (sessionless, assume the dispatch role, orient on the inbox). Not offered in story/cab/general — if typed there anyway, note `dispatch is plugin/personal only` and re-ask the same role prompt (from `start.md` Step 1a).

**`capture`** (plugin/personal only) → read `commands/capture.md` and run it (sessionless, assume the capture role, bank ideas). Same zone restriction as `dispatch`.

---

**`refine` path** (any zone):

**If no target was already carried in from Step 2, do not ask a bare question first — hand straight to `commands/refine.md`'s bare-`refine` path** (its Step 1 "Nothing (bare `refine`)" branch, acp-ajudd#128). That path renders the relevant refining chunk itself before asking anything, so the wizard's own ask no longer needs to precede it:
- **story, cab** → lists the user's own *Gathering Requirements* stories inline (assignee OR reporter = me) — `Gathering Requirements (yours, resumable): …`; asks the topic directly only if that list is empty.
- **plugin, personal** → shows the captures-waiting glance (if any), then the resumable `refining` `work` entries for the slug — `Refining (resumable): …`; asks the topic directly only if there's nothing to resume.
- **general** → no list exists (no system of record) — asks the topic directly (`What are we refining? (a short topic)`).

From whatever it shows, the user resumes a target (`refine <id>` / `<n>` / `BPT2-XXXX`) or scopes new (`refine <new topic>`) — `refine.md` owns the reply from that point on; this file does not re-branch on it.

**If a target WAS already carried in from Step 2** (a key, an item `[id]`, or a topic caught by eager inference), skip the chunk and act directly:
- **A story/CAB key, or an item `[id]`** (story/cab/plugin/personal only — general has neither) → read `commands/refine.md` and run its Step 1 **resume** path with that reference (prints status first, applies the status-tiered edit guard for stories, continues refining in place).
- **A topic / free text** → read `commands/refine.md` and run its Step 1 **new** path, passing the topic as the argument. Scopes a brand-new Jira story in *Gathering Requirements* for story/cab; a new `work` entry for plugin/personal; general creates nothing (refine.md's own zone-aware graduation owns each case — this file never branches on the outcome).

Refine is sessionless — this path never creates a session file, never touches `_active`, and never offers to `code` (acp-ajudd#56).

---

**`code` path — story / cab zone:**

If no target was already carried in from Step 2, **render the coding menu chunk before asking** — script-rendered, in one shell call (this is data to look at, not an inference to act on: never skip the ask itself by auto-resuming the current branch's story instead, acp-ajudd#126):
```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
SL="$ROOT/scripts/session-list.py"
CURBR=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if command -v python3 >/dev/null 2>&1 && [ -f "$SL" ]; then
  python3 "$SL" --session-root "<session_root>" --slug "<slug>" --handle "<handle>" --rebuild-index --current-branch "$CURBR"
fi
RENDER="$ROOT/scripts/inbox-render.py"
if command -v python3 >/dev/null 2>&1 && [ -f "$RENDER" ]; then
  python3 "$RENDER" render --session-root "<session_root>" --slug "<slug>"
fi
```
Display the sessions-table stdout verbatim (completed sessions stay hidden; a row on the current git branch is marked `(current branch)` — **one highlighted row among the rest, never the only thing shown and never auto-picked**, acp-ajudd#128) and, if the rendered inbox has logical items, the compact inbox summary (layout B, per `references/inbox-convention.md`). Then ask:
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
- **`search`** → re-run the render above (refresh) and re-display, then re-ask `story key (e.g. BPT2-6429)? — or new` (drop `search` from the reprompt).
- **Anything else** → treat as a nudge, not a filter (this flow doesn't support free-text filtering — that's what `search` is for): ask once more, `Story key, or new / search?`.

---

**`release` path — story / cab zone only (acp-ajudd#158):**

`release` is the primary verb for CAB work — symmetric with `code`'s "the file decides" behavior, scoped to CAB targets specifically. Not offered in plugin/personal/general (mirrors `dispatch`/`capture`'s zone restriction — if typed there anyway, note `release is story/cab only` and re-ask the same role prompt from `start.md` Step 1a).

If no target was already carried in from Step 2, ask directly (no separate render needed beyond what `code`'s render above would show — reuse it if already on screen this turn):
```
story key(s) to start a new CAB, or an existing CAB-XXXX to resume?
```
Wait for one free-text reply.

- **One or more story keys** (`BPT2-6429`, `BPT2-6429 BPT2-6430`) → new CAB kickoff: route to `/release:create-cab` for those stories, same mechanics `start-classic.md`'s Work project `cab <keys>` handling already documents (session-vs-lite choice before routing, per `references/lite-mode.md`). Read `start-impl.md`, go to **Step 9 → "CAB — new"**.
- **A single `CAB-XXXX` key** → resolves exactly like `code CAB-XXXX`: check whether `<session_root>/<CAB-XXXX>.md` exists — **exists** → read `start-impl.md`, go directly to its **Step 4 (Resume existing)**; **does not exist** (e.g. a lite CAB with no session file) → the lite-resume check in `start-impl.md`'s **CAB — resume** section handles it.
- **Anything else** → ask once more, `Story key(s), or an existing CAB-XXXX?`.

`cab <keys>` / `code cab <keys>` remain accepted as documented legacy synonyms wherever they were accepted before this change — this section only adds `release` as the new primary entry point, it does not remove the old ones.

---

**`code` path — general zone:**

If no target was already carried in from Step 2, **render the sessions table before asking** — script-rendered (general zone has no consolidated inbox, so this is the only call needed):
```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
SL="$ROOT/scripts/session-list.py"
CURBR=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if command -v python3 >/dev/null 2>&1 && [ -f "$SL" ]; then
  python3 "$SL" --session-root "<session_root>" --slug "<slug>" --handle "<handle>" --rebuild-index --current-branch "$CURBR"
fi
```
Display its stdout verbatim (a row on the current git branch is marked `(current branch)` — one highlighted row among the rest, never auto-picked, acp-ajudd#128). Then ask:
```
name — new session or resume?
```
Wait for one free-text reply.

- Check whether `<session_root>/<name>.md` exists:
  - **Exists** → read `start-impl.md`, go directly to its **Step 4 (Resume existing)** with that session.
  - **Does not exist** → new kickoff: read `start-impl.md`, go to its Step 6 (Establish Session Identity → general). If what the session is for isn't already clear from conversation context, ask "What are we working on?" and a category (Research / Prototype / Training / Other) as that step requires.
- **`search` / `list`** → re-run the render above and re-display, then re-ask `name — new session or resume?` (drop `search` from the reprompt).
- **Anything else** → ask once more.

---

**`code` path — plugin / personal zone:**

Sessions are item-driven: a `code` target is either an inbox `work` entry (by list `<n>` or stable `[id]`) that graduates into a fresh session, or an existing in-progress session (by name, or its sessions-table row) that resumes. There is no `new` verb here — new plugin/personal work is scoped first via `refine`, never created-and-coded in one gesture.

If no target was already carried in from Step 2, **render the coding menu chunk before asking** — script-rendered, both calls together (this supersedes the standalone Step 2 captures-glance for this turn — its count is already folded into the pickup list's trailing line, so don't print it twice, acp-ajudd#128):
```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
SL="$ROOT/scripts/session-list.py"
CURBR=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if command -v python3 >/dev/null 2>&1 && [ -f "$SL" ]; then
  python3 "$SL" --session-root "<session_root>" --slug "<slug>" --handle "<handle>" --rebuild-index --current-branch "$CURBR"
fi
IR="$ROOT/scripts/inbox-render.py"
if command -v python3 >/dev/null 2>&1 && [ -f "$IR" ]; then
  python3 "$IR" pickup --session-root "<session_root>" --slug "<slug>" --current-slug "<slug>"
fi
```
Display both stdouts verbatim, sessions table first — the same numbered pickup list `start-classic.md`'s Plugin/Personal blocks show (acp-ajudd#123): layout B, `[<id>]` before each description, `[spawn]` flagged with ★, `work`-type only, `· <stage>` suffix for `new`/`refining`, plus the trailing captures-waiting glance if any. **A row on the current git branch is marked `(current branch)` in the sessions table — one highlighted row among the rest, never the only thing shown and never auto-picked** (acp-ajudd#126/#128). Then ask:
```
inbox item # / id / name? — or search
```
Wait for one free-text reply.

**One-of-each advisory (read-only — acp-ajudd#41).** Before acting on the reply below, check `_active` + `_index.md` for an in-progress coding session other than the one about to be started/resumed (no new scan). If one exists, print exactly `Note: coding session '<name>' is already active for this slug — starting here makes two (one-of-each discipline).`, then proceed normally. This is read-only — it never blocks.

- **A `[<id>]` or list `<n>`** (the just-rendered list, or already known from a handoff/capture) that resolves to a **`work` entry** → graduate it into a fresh session: read `session/commands/start-impl.md` immediately and continue from its **Step 4 → "Work Pickup (plugin / personal only)"** section — maturity guard, injection scan, feature-name derivation, fold, archive-on-consume. `<n>` is the ephemeral list position; `<id>` is the stable handle — accept either.
- **A name (or `<n>` against the sessions table)** that resolves to an **in-progress session** → resume it: read `session/commands/start-impl.md` immediately and continue from its **Step 4 (Resume existing)** with that session — the same "Plugin session resume" mechanics `start-classic.md` documents (security check, resume block, inbox + reviewed batch — script-rendered via `resume-block.py`, acp-ajudd#123).
- **`search` / `list`** → re-run the render above (refresh) and re-display, then re-ask `inbox item # / id / name?` (drop `search` from the reprompt).
- **Anything else** → ask once more.

<!-- Steps 4–9 (session file writes, Teams chat setup, Establish Session Identity, and everything after a target resolves) live in start-impl.md and are unchanged by this file — the wizard only changes how the target is gathered. -->
