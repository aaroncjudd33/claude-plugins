---
name: board
description: Show the whole board for this slug — captures + refining + ready + in-progress in one glance. Read-only, sessionless, role-agnostic; callable from any terminal.
---

# Session Board

A **read-only, sessionless, role-agnostic** snapshot of everything in flight for the
current slug — captures awaiting triage, work being refined, work ready to pick up, and
sessions currently in progress. It is the deliberate **opt-in** counterpart to #99's
default role-scoped silence: nobody narrates the board unprompted, but any terminal can
ask to see the whole thing on demand, regardless of which role (`refine` / `dispatch` /
`capture` / a `code` session) is asking.

**Composes existing renderers only — no new rendering logic.** Every section below is
either echoed verbatim from a script (`session-list.py`, `inbox-render.py`) or parsed
with the same type/status logic `session:start`'s Step 3 pickup list already uses
(`references/inbox-convention.md`). This command adds no new inbox-parsing rules and no
new session-state derivation — it just prints all of them together in one place.

**Hard constraints:** no writes, no `_active` change, no side effects, no prompts —
print and stop. Works from any terminal, with or without an active coding session, in
any zone.

## Instructions

### 1. Resolve Location

Run `pwd`, extract the repo slug (last path component). Resolve `session_root`, `handle`,
and `zone` using Path Resolution (`references/path-resolution.md` — core resolution +
§ Zone Detection, the centralized table acp-ajudd#120 established; do not reinvent zone
detection here).

If `session_root` does not exist or is empty, print `No board for <slug> — nothing has
started here yet.` and stop.

### 2. Render the Three Sources (parallel, read-only)

Issue these three calls together — none of them write anything as invoked here:

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python

# 1. Sessions — no --rebuild-index: that flag is what makes session-list.py write
#    _index.md / heal _active / run the encoding+state-exclusivity scan. Board never
#    passes it, so this call is a pure read no matter what shape _index.md is in.
"$PY" "$ROOT/scripts/session-list.py" --session-root "<session_root>" --slug "<slug>" \
  --handle "<handle>" --show all

# 2. Inbox — render() is the single read helper (references/inbox-convention.md
#    § Per-item storage mechanics). Its one side effect — the lazy legacy-inbox
#    migration — already runs on every read in this codebase (start / refine /
#    dispatch / capture / finish / checkpoint / switch / in-flight / search); board
#    doesn't opt out of that shared, idempotent behavior, it just doesn't add any
#    write of its own. Relay any migration notice on stderr, same as everywhere else.
"$PY" "$ROOT/scripts/inbox-render.py" render --session-root "<session_root>" --slug "<slug>"

# 3. In-flight — [CONSUMED -> session] items whose session is still in-progress
#    (acp-ajudd#99). Display-only by construction.
"$PY" "$ROOT/scripts/inbox-render.py" in-flight --session-root "<session_root>" --slug "<slug>"
```

If `python3`/`python` or a script is unavailable, degrade the same way `start`/`in-flight`
already do (session-list fallback: read `_index.md` directly; inbox fallback: read
`_inbox/*.md` / legacy `_inbox.md` directly) — never block on a missing interpreter.

### 3. Parse the Inbox Stream Into Four Groups

Using the **same parsing rules `session:start`'s Step 3 pickup list already applies**
(`references/inbox-convention.md` § Inbox Model, § Provenance Rendering) — do not
introduce new categories or a different back-compat table:

- **Captures** — `> [type: capture]` (legacy `type: note`/`type: data`, legacy
  `status: capture|new|unread` without `type: work`, all read as capture).
- **Refining** — `> [type: work · status: new]` or `status: refining` — work that
  exists but isn't `ready` yet. Show the `· <stage>` suffix (`new` or `refining`) per
  entry, same convention as the pickup list.
- **Ready** — `> [type: work · status: ready]` (including legacy entries with no
  status line at all, which default to `ready`). Flag `[spawn]`-tagged entries with ★.
- No line at all → `type: work · status: ready` (back-compat default, same as
  everywhere else this inbox is read).

Render each group in **layout B** (`references/inbox-convention.md` § Provenance
Rendering) — description first, `[<id>]` before it, provenance dim on the line below,
same-repo slug dropped:
```
  [<id>]  <description>
     ↳ <slug> / <session> (<type>) · MM-DD
```

### 4. Print the Board

Print immediately — no batching, no routing prompt, no wait for a reply. This is a
snapshot, not an interactive flow.

```
Board — <slug>

Captures (N):                                    ← omit heading if zero
  [<id>]  <description>
     ↳ <slug> / <session> (<type>) · MM-DD

Refining (N):                                    ← omit heading if zero
  [<id>]  <description>  · <stage>
     ↳ <slug> / <session> (<type>) · MM-DD

Ready (N):                                       ← omit heading if zero
  [<id>]  ★ [spawn] <description>
     ↳ <slug> / <session> (<type>) · MM-DD

<session-list.py stdout, echoed verbatim>        ← "Sessions in <slug> … N in-progress · N paused · N completed"

In-flight (N):                                   ← omit heading if none; inbox-render.py in-flight stdout, echoed verbatim
  <id>  → <session>   <title>

N captures · N refining · N ready
```

- The sessions block and the in-flight block are **printed verbatim** from their
  scripts' stdout — do not re-derive, re-align, or re-summarize them.
- The trailing tally line covers only what this command itself parsed (captures /
  refining / ready); the sessions script already prints its own
  in-progress/paused/completed tally, so don't duplicate that count here.
- If every group is empty (no captures, no refining, no ready work, no sessions, no
  in-flight rows), print: `Board — <slug>: clean — nothing waiting, nothing in flight.`

Stop here. Board never routes to `refine`, `code`, `dispatch`, or `capture` — it only
answers "what's the state of everything," it never picks a next action for you.
