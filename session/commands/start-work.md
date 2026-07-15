---
name: start-work
description: Session start — lean work-repo flow (Step 2 onward). Loaded by start.md's dispatcher for story/cab zones once zone and the config-cascade are resolved.
---

# Session Start — Work-Repo Lean Flow (Step 2 onward)

Loaded by `start.md` (the dispatcher) once zone and the config-cascade have been resolved, for the **story/cab zone only**. Context already in scope: `slug`, `session_root`, `handle`, `zone` (`story` | `cab`), and `filter_mine` (if Step 0's `mine` fast-path set it). This file exists because the classic flow's dump-everything-then-ask experience is wrong for a work repo (acp-ajudd#121, live 2026-07-15 in virtual-office): a work-repo `/session:start` should be a fast, guided two-step prompt, not a sessions table + inbox + data-drift question. **Fast-path args never reach this file** — `start.md`'s own Step 0 resolves `code BPT2-XXXX` / a bare key / an existing session name directly against `start-impl.md`, skipping Steps 2–3 entirely (see `start.md` Step 0.4). This file only runs on a **bare** `/session:start` (no argument) in a story/cab repo.

**No listing by default.** Unlike the classic flow, this file never renders the sessions table or the inbox as a first move — that only happens on explicit `search`/`list`. **Never front data-drift** (an index-vs-file mismatch, a stale status) — if the reconcile/approval-hash checks inside `start-impl.md` surface one during the resume path below, let it surface there, lightly, after the user has already picked a target; do not add a drift check here.

## Instructions

### 2. Ask: refine or code?

Output exactly:
```
refine or code?
```
Wait for one free-text reply. **Do not use AskUserQuestion.**

**Infer eagerly before falling back to the plain two options** — the whole point of this flow is speed, so don't make the user answer twice when the first reply already carries the answer:
- A bare Jira story key (`BPT2-6429`) or CAB key (`CAB-456`) → **implicit `code`** on that key; skip straight to the Step 3 (code) key-handling below with it.
- `code <key>` / `cab <key>` → same, explicit.
- `refine <anything>` (a key or a topic) → skip straight to Step 3 (refine) with that target.
- `search` / `list` → run the on-demand listing (see Step 3 code branch's `search` handling), then re-ask `refine or code?`.
- Bare `refine` → go to Step 3 (refine) with no target.
- Bare `code` → go to Step 3 (code) with no target.
- Anything else that doesn't parse → ask once more: `refine or code?` (do not guess a third way).

---

### 3. Code path

If no target was already carried in from Step 2, ask:
```
story key (e.g. BPT2-6429)? — or new / search
```
Wait for one free-text reply.

- **A story key or CAB key** (`BPT2-6429`, `cab BPT2-6429 BPT2-6430`) → the file decides, same as everywhere else in this plugin:
  - `cab <keys>` / bare `cab <keys>` → route to `/release:create-cab` (new CAB coding session for those stories) — same as the classic flow's `code cab` input.
  - A single story key → check whether `<session_root>/<key>.md` exists:
    - **Exists** → read `start-impl.md`, go directly to its **Step 4 (Resume existing)** with that session. This is where a stale index-vs-file drift (if any) surfaces — via the approval-hash check already built into that step — never before now.
    - **Does not exist** → new kickoff: render the consolidated inbox (`inbox-render.py`, auto-migrates) and check for a `[spawn]` entry whose label matches the key. If found, archive it immediately with stamp `[PICKED UP YYYY-MM-DD — <key>]` to `<session_root>/_inbox_archive.md` (create if needed), then delete its `_inbox/<id>.md` file (acp-ajudd#102). Read `start-impl.md`, then go to its **Step 6** (Establish Session Identity) → **Story — new kickoff** (Step 9): `getJiraIssue` → transition to *In Progress* → create feature branch → epic check → memory scan offer.

- **`new`** → new-story path. This repo has no story yet, but the user wants to code, not scope in Jira first:
  1. Ask only for what's not already inferable from conversation context: **Summary** (short title) — everything else defaults the same way `/story:create` does (Work Allocation Type inferred from context, Expenditures: Opex, Assignee: current user from `user-config.json` → `user.jiraAccountId`, initial status: Ready For Work).
  2. Create the issue via the same two-call pattern `/story:create` uses (`createJiraIssue` for summary + required fields, then immediately `editJiraIssue` for the markdown description — `createJiraIssue`'s `description` field does not render markdown, `editJiraIssue`'s does) — project `BPT2`, issue type `Story`, cloudId `9de6eb2b-2683-44e6-89ff-c622027e09b4`.
  3. Once the key exists, treat it exactly like a fresh key with no session file above: read `start-impl.md`, go to Step 6 → **Story — new kickoff** (transitions Ready For Work → In Progress as part of that same flow — no separate transition call needed here).

- **`search`** → the on-demand listing (the **only** place in this flow that renders one): run the classic flow's Step 2 render calls verbatim —
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
  Display the sessions-table stdout verbatim (completed sessions stay hidden — no `--show all`/`all` flag is passed, same default as the classic flow) and, if the rendered inbox has logical items, the compact inbox summary (layout B, per `references/inbox-convention.md`) — same rendering rules as the classic flow's Work-project block. Then re-ask `story key (e.g. BPT2-6429)? — or new` (drop `search` from the reprompt — it was just used).

- **Anything else** (free text that isn't a key/`new`/`search`) → treat as a natural-language nudge, not a filter (this flow doesn't support free-text filtering — that's what `search` is for): ask once more, `Story key, or new / search?`.

---

### 3. Refine path

If no target was already carried in from Step 2, ask:
```
story key to refine, or a new topic?
```
Wait for one free-text reply.

- **A story key** (`BPT2-6429`) → read `commands/refine.md` and run its Step 1 **resume** path with that key (prints status first, applies the status-tiered edit guard, continues refining in place).
- **A topic / free text** → read `commands/refine.md` and run its Step 1 **new** path, passing the topic as the argument (scopes a brand-new Jira story in *Gathering Requirements*, project resolved-or-confirmed).
- **`search` / `list`** → hand straight to `commands/refine.md`'s bare-`refine` path, which lists the user's own *Gathering Requirements* stories inline (assignee OR reporter = me) — no separate listing logic needed here, refine already owns it.
- **Bare reply / nothing usable** → hand straight to `commands/refine.md`'s bare-`refine` path (same as `search` above — it already asks the topic directly if the list is empty).

Refine is sessionless — this path never creates a session file, never touches `_active`, and never offers to `code` (acp-ajudd#56).
