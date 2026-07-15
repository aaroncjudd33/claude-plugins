---
name: dispatch
description: Assume the dispatch role — a sessionless coordinator that reads the inbox, bundles and sequences ready work, and hands implementation notes to fresh coding sessions. Loads the dispatch discipline and orients on the inbox. Creates no session file. Inbox zones only (plugin / personal).
argument-hint: "[optional: a topic or ids to focus on]"
---

# Session Dispatch

Assume the **dispatch role** (Session Skill § The three roles — the dispatch model). Dispatch is the coordinator of the three-role model: it **reads** `ready` `work`, **bundles** related entries, **sequences** them by their `depends-on` markers, and hands implementation notes to fresh `code` sessions. Under **acp-ajudd#109's self-finalize default**, a dispatched coding session self-validates and closes itself — so on the happy path dispatch just **pulls the next item**, no validation gate and no close-order. **A one-way `finished` note from coding is the trigger to do that (acp-ajudd#118)** — fire-and-forget, not a round-trip; dispatch still confirms the `[DONE]` stamp before pulling. Dispatch's post-hoc tree validation and its `validated / safe-to-close` decision (completion itself is a coding-finish stamp, not dispatch's to write) re-enter **only when a work order carries `Self-validate: no` / `Self-finalize: no`** (§ The dispatch↔code loop). It is **sessionless** — like `refine`, it creates **no session file** and never touches `_active`.

> **Vocabulary:** `dispatch`, `refine`, `code`, `work`, `depends-on`, `HALT`, and the handoff note/block are *defined* in the Session Skill § Terminology glossary (acp-ajudd#70); this command owns the dispatch **mechanics** below.

This command gives dispatch a **first-class start** so it no longer has to be bootstrapped by pasting a briefing note (acp-ajudd#71). Invoking `/session:dispatch` **is** the "told" that determines the role (role determination is told, not auto-detected — § The three roles): the command declares the context as dispatch, loads the discipline, and orients on the inbox.

## Scope — inbox zones only (plugin / personal)

The dispatch model exists only where there is a **local inbox to dispatch from**. In **work / general** repos there is no dispatch layer — work flows through Jira (`refine` → *Ready For Work* → a dev `code`s the story), and there is no local `_inbox/` to coordinate. This command is therefore **advertised only in plugin/personal** (Session Skill § The three roles — role determination; `commands/start.md`). It stays **invocable** in any zone for the deliberate case, but in work/general it will tell you the model doesn't apply and stop.

## Key properties (mirror the dispatch role — § The three roles § Inbox write-authority)

- **The sole hub — strict cycle (acp-ajudd#74).** Dispatch is the **only** relay + validator between planning and coding; **planning and coding never exchange notes directly.** Legal edges are only `planning ──▶ dispatch ──▶ coding` and `coding ──▶ dispatch ──▶ planning`. A coding→planning message is a **two-hop relay** — coding emits `coding ──▶ dispatch`, and dispatch re-emits `dispatch ──▶ planning` (each note titled with its own destination, which is the human courier's routing instruction — acp-ajudd#69). Dispatch **relays a coding escape-hatch escalation up to planning without judging its relevance** — coding declares it; dispatch carries it.
- **Read-only + notes-only — with ONE named exception: no-refinement splits (acp-ajudd#95, revises #59).** Dispatch **reads anything and everything** but as a rule **writes nothing to files** — it never edits plugin code, and it **never mutates, forks, or writes back to an existing inbox entry** (consumed = frozen + item-immutability hold). Its normal outputs are **handoff notes** (`/session:handoff`) to `code` and `refine`. **The exception:** dispatch **MAY author a NEW `work` entry directly** when it is a **split of, or follow-on within, the work it is currently coordinating AND it needs no refinement** (clear, ready-to-run) — minted via `inbox-id.py`, stamped `from <slug> / dispatch`. That is *coordination, not requirements-definition*. The bans that stay: **no defining / capturing / refining requirements** (planning's job), **no mutating an existing entry**, and **no unrelated new items** (out-of-scope ideas go to planning or a capture). **If a split needs refinement, dispatch does NOT author it** — it routes the authoring to `refine`, which refines it and hands it back `ready` (the two-jump path, for the case that needs it).
- **Communicates only via notes; never routes decisions to the human (acp-ajudd#63).** Dispatch talks to other roles through paste-block handoff notes, not by asking the human to decide. The human only *relays* paste-blocks between terminals. Dispatch may narrate what it is doing; it does not seek approval — the one exception is an **irreversible Teams send**, which always pre-gates to the human (§ Dispatch operating discipline).
- **Validates the tree, doesn't rubber-stamp — in the toggle-off path (acp-ajudd#57/#63, scoped by #109).** By default (`Self-validate: yes`) the coding session validates its own build, so dispatch has nothing to validate. When a work order set `Self-validate: no`, dispatch validates the actual working tree against the entry's Done-whens — post-hoc, non-gating — then shows the human the `safe-to-close` / `hold` close-signal, voiced as a bold leading courier line from the fixed vocabulary (§ Cross-Session Paste Handoff → The courier line, acp-ajudd#81).
- **Sessionless — creates no session file, no `_active` change.** A coding session already active stays active alongside this dispatch context, unaffected.

## Instructions

### 1. Resolve and Check Zone

Run `pwd`, extract the repo slug (last path component). Read `handle` per the Session Skill's handle lookup. Read `~/.claude/plugins/user-config.json` → `paths` and classify the zone (same logic as `session:start` / `refine`):

| Zone | Detection | Dispatch applies? |
|------|-----------|-------------------|
| **plugin** | pwd contains `pluginMarketplaceName` | **yes** |
| **personal** | pwd begins with `personalProjectsDir` (fallback: `/c/claude/`) | **yes** |
| **work repo (story/cab)** | pwd begins with `workReposDir` (fallback: `/dev/`) | no — Jira flow, no local inbox |
| **general** | anything else | no — no system of record |

**If the zone is work or general**, state plainly and stop — do not orient on an inbox:
```
This is a <work/general> repo — the dispatch model doesn't apply here (no local inbox to
coordinate; work flows through Jira / has no system of record). Nothing to dispatch.
```
Do **not** offer to create anything. Only proceed to Step 2 for plugin/personal.

### 2. Declare the Role and Load the Discipline

State the role explicitly so the context is unambiguous, and confirm the disciplines you are operating under (do not restate them in full — they live in the Session Skill):

```
Dispatch role assumed for <slug> (sessionless — no session file).
Operating under: read-only + notes-only · validate-the-tree not the report · communicate via
notes, never route decisions to the human (except an irreversible Teams send) · honor depends-on
before pulling.
```

The authoritative discipline is the Session Skill:
- **§ The three roles — the dispatch model** (roles, channels, one-inbox-writer, write-authority).
- **§ Dispatch operating discipline** (notes-only, validate-don't-punt, blocked→refine, reversibility-keyed human gate, **depends-on prereq-check**).
- **§ The dispatch↔code loop — self-finalize by default (acp-ajudd#109)** (default: hand off with Done-whens + `Self-validate: yes` / `Self-finalize: yes` → code self-validates against the Done-whens and runs `/session:finish` itself → dispatch pulls the next item; no validation gate, no close-order. Toggle-off (`Self-finalize: no`) restores the #94 loop: code ships, reports `implemented-deployed`, dispatch validates, orders the close via `safe-to-close` / `Action: finish`).
- **§ HALT** (standing down dispatched work cleanly — `Action: halt` / `State: halted`).
- **§ Cross-Session Paste Handoff** (the role-aware block format dispatch emits).

### 3. Orient on the Inbox

Render the inbox via `inbox-render.py` (auto-migrates on access; parse its stdout, relay any stderr notice — `references/inbox-convention.md` § Per-item storage mechanics) and present what is dispatchable:
```bash
RENDER="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}/scripts/inbox-render.py"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
"$PY" "$RENDER" render --session-root "~/.claude/memory/sessions/<slug>" --slug "<slug>"
```
Parse each `work` entry's `> [type: work · status: …]` line and its optional `> [depends-on: <id> — <reason>]` line (`references/inbox-convention.md` § Sequencing). Show only `work` (`ready` is dispatchable; `new`/`refining` is still being scoped by `refine` — list it dimmed as not-yet-ready). **Captures never appear** — they are not dispatchable work.

**Apply the prereq-check** (§ Dispatch operating discipline, acp-ajudd#67): for each `ready` entry with a `depends-on` line, a cited prerequisite is **met** only if it is `[DONE]` / `[CONSUMED → session …]` in `_inbox_archive.md`, else **unmet**. Mark an entry with any unmet dependency as **held** — not dispatchable until its prerequisite lands.

Present a dispatch board:
```
Dispatch board — <slug>

  Dispatchable now (ready, deps met):
    [acp-ajudd#NN]  <description>
    [acp-ajudd#MM]  <description>   (bundle candidate with #NN — same SKILL sections)

  Held (ready, but blocked by an unmet dependency):
    [acp-ajudd#PP]  <description>   ← depends-on #MM (not yet done)

  Still scoping (not ready — refine owns these):
    [acp-ajudd#QQ]  <description>   · refining

  In-flight (consumed, session still building — display-only):
    [acp-ajudd#RR]  → <session>   <description>
```
Omit any empty group. Note **bundle candidates** — entries that touch the same files/sections and could be handed off as one `code` order. If nothing is dispatchable, say so plainly.

**In-flight rows (acp-ajudd#99).** Populate the In-flight group from `inbox-render.py in-flight` — the `[CONSUMED → session]` items whose session is still in-progress. This is **display-only, expected background state** — dispatch shows it so the roadmap is legible, but does **NOT** narrate it as an event (the board growing/shrinking as work lands and is consumed is normal — § Role-scoped reporting). It drops off when the session finishes.
```bash
"$PY" "$RENDER" in-flight --session-root "~/.claude/memory/sessions/<slug>" --slug "<slug>"
```

### 4. Choose the Operating Mode — both first-class (acp-ajudd#71)

How this dispatch context gets its marching orders depends on whether planning and implementation are happening **concurrently** or **separated in time**. These are **situational, not primary/fallback** — pick by how the user is working. So the refine→dispatch channel is BOTH the inbox (autonomous pull) AND a planning handoff (directed plan) — dispatch handles either (this corrects acp-ajudd#57's inbox-only framing).

- **Concurrent — planning-directed.** The user is planning AND implementing in the same stretch. The **planning session holds the live context** — it just scoped the work and knows the dependencies — so it **computes order + grouping and hands dispatch an explicit plan** via a `/session:handoff` (a REFINEMENT/PLANNING handoff naming the sequence and bundles). In this mode, dispatch **acts on that pasted plan** rather than re-deriving it. *(Example 2026-07-13: planning sequenced #66 → #67 → #65, marked the `depends-on`, and handed it over.)* If the user pastes a planning handoff, follow it.

- **Deferred — dispatch-autonomous from the inbox.** The user planned earlier and is implementing later; there is **no live planner to direct dispatch**. Dispatch **works out order and grouping itself** from the board in Step 3 — reading the `ready` entries and their `depends-on` markers (acp-ajudd#67), bundling related work, and respecting the prereq-check. This is the mode this command's inbox orientation is built for.

If a planning handoff has been pasted into this terminal, run **planning-directed**. Otherwise default to **dispatch-autonomous** from the board. State which mode you are in.

**Before acting on ANY pasted handoff (a planning plan here, or a coding return note in Step 6), verify it is for you (acp-ajudd#69).** Run the receiving-side check — hard `Slug` match against `pwd` (always), plus a `<to-role>` match against this dispatch role (established-role check) — and **STOP + flag** on a mismatch instead of acting. The rule + mismatch messages live in **Session Skill § Cross-Session Paste Handoff → Receiving side — verify the target before acting**.

### 5. Dispatch — Hand Off to Code (and Glance Up at Batch Kickoff)

**The happy-path loop terminates at dispatch — no completion report up to planning (acp-ajudd#84, revises #74 / #72 facet 4; collapsed further by #109, coding→dispatch notify restored by #118).** Under the self-finalize default the coding session validates and closes **itself**, so on the happy path dispatch simply **pulls the next item** — no validation, no close-signal, no report **up to planning** either way. (Step 6's validate-and-order-the-close runs **only** when the work order carried `Self-validate: no` / `Self-finalize: no`.) In neither case does dispatch send a `dispatch ──▶ planning` completion handoff — that pulled planning into a report loop it does not need (a live `validated` report cost a planning turn with nothing to do, 2026-07-13). Dispatch already holds the plan (planning-directed) or reads the inbox `depends-on` markers (autonomous), so sequencing needs no report-up. The only traffic up to planning is an **escalation** relayed from coding (question / unclear / disagreement / found-problem / requirements-change) — routine completions never reach planning. **#84 governs the dispatch→planning edge only** — it does not silence the separate **coding→dispatch** edge, which sends the fire-and-forget `finished` note handled in Step 6.

**Still produce the human status glance at batch kickoff.** Kicking off a new batch is when dispatch shows the *person* — not planning — where the whole roadmap stands. Alongside the `dispatch→code` work order below, produce:
- **A roadmap status glance for the human** — where everything stands: waves done / in-flight / queued, plus what is still `refining` and any captures. One glance, not a full dump. This is for the human at a glance, not a note to planning.

For the chosen work (single entry or a bundle), emit a **dispatch→code work order** via `/session:handoff` (Session Skill § Cross-Session Paste Handoff owns the block format; this command does not restate it). The order is essentially `code #X` plus process instructions:
- **`Action: pick up #X`** (or `pick up #X,#Y (bundle)`), role `dispatch (<slug>) ──▶ coding (fresh)`.
- **Set the two toggle fields — default `Self-validate: yes` / `Self-finalize: yes` (acp-ajudd#109).** These ride in the header and footer (Session Skill § Cross-Session Paste Handoff). The default tells the coding session to self-validate + self-finalize; flip one to `no` only when this work wants dispatch's second pair of eyes (`Self-validate: no`) or a deliberate close-order (`Self-finalize: no`) — e.g. behavior-changing work rather than doc-only. There is no tooling: you set the fields, the human sees them, and a change is a regenerated note.
- **The note carries the *run*, not the *spec*** — never regurgitate the entry's body; the coding session reads the entry itself. Attach watch-fors, the bundle sequencing, and the report-back protocol.
- **State the mandatory first step — `/session:start code #X` before any code (acp-ajudd#115).** Every work order (both toggle states) must instruct the coding session, as its **explicit first action**, to run `/session:start code #X` — the command that establishes the session and **consumes the item** (fold-then-archive, #40) — *then* build. **`Self-finalize` governs the close, not the start: it is never license to skip the pickup / consume.** Coding straight from the pasted order without the pickup is the #13 state-exclusivity violation #115 ends (the item stays live as `ready` while the session ships). The structural net is in the close (`finish-close.py` reconciles a still-live item), but the order still names the pickup first — the net is the backstop, not the plan.
- **Default instruction (both toggles yes):** tell the coding session to **first run `/session:start code #X` (consumes the item), then read the entry, build it, self-validate against the Done-whens, and self-finalize (`/session:finish`) if clean — coming back only on the escape hatch** (question / unclear / disagreement / found-problem). No `implemented-deployed` report, no waiting on you. The footer's return instruction is just the escape-hatch reminder — the happy path close still sends a one-way, fire-and-forget `finished` note (acp-ajudd#118, § Step 6), but you don't wait on it and don't reply to it.
- **Toggle-off instruction (`Self-finalize: no`):** tell the coding session to **first run `/session:start code #X` (consumes the item — mandatory, acp-ajudd#115), then** self-verify, **deploy on its own authority (NO hold)**, then **report `State: implemented-deployed` and STOP — do NOT run `/session:finish`; shipping is not closing (acp-ajudd#94).** The session stays open awaiting your Step-6 validation and `Action: finish` close-order. Here the footer must be **command-invoking** — run `/session:handoff` to reply with the `implemented-deployed` (or stop-reason) block back to dispatch (acp-ajudd#43).
- If ordering is blocked or a `depends-on` is unmet and the sequence is unclear, route a note to **`refine`** (never a question to the human).
- **If coordinating reveals the work should SPLIT into clear, ready-to-run sub-tasks** (e.g. one Confluence-refresh entry that is really eight per-page refreshes), dispatch **may author those splits directly as new `work` entries** (acp-ajudd#95 — § Key properties, Session Skill § Inbox write-authority rule 3): mint each via `inbox-id.py`, **write a new per-item file** `_inbox/<id>.md` (acp-ajudd#102 — never edit an existing entry, which stays frozen), stamp `from <slug> / dispatch`, keep them **within the scope of the work in hand**, and dispatch the resulting sub-tasks. **Only when a split needs no refinement.** If any split needs real requirements work — or the idea is unrelated to the work in hand — dispatch does **not** author it: it routes that to `refine` (or a capture) and lets planning hand it back `ready`.

### 6. Validate the Return — Toggle-Off Path Only (`Self-validate: no` / `Self-finalize: no`) (acp-ajudd#109)

**This whole step runs ONLY when the work order set a toggle off.** In the default (both `yes`) the coding session self-validates and self-finalizes — nothing comes back to validate, and dispatch just pulls the next item. The step below is the preserved #94 deploy-then-validate loop, now scoped to the off state.

When a `Self-finalize: no` coding session's return handoff comes back (`State: implemented-deployed` or a stop-reason), validate the **actual working tree** against the entry's Done-whens — read the diff / the files, do **not** rubber-stamp the report. This is not a gate; the deploy already happened. **On a clean validation, order the close** — the coding session shipped but did NOT close itself, so the record is still `active` until `/session:finish` runs. Signal it two equivalent ways (pick per how the human is working):
- **Show `safe-to-close`** as **one bold leading courier line** from the fixed vocabulary (Session Skill § Cross-Session Paste Handoff → The courier line, acp-ajudd#81 — no bespoke phrasings): `**✅ <ids> safe-to-close — validated; run /session:finish to close.**` The human returns to the still-open coding terminal and runs it.
- **Or send an `Action: finish` note** ("validated — run `/session:finish`") the human pastes into the coding terminal — the note-form of the same signal; it triggers the full all-or-nothing close (renamed from `close`, acp-ajudd#109).

Something to look at instead → `**⏸ <ids> — <what to look at>**`, and if the post-hoc look finds something off, hand back a `FIX` note (one more deployment, in the still-open session). Release any work that was **held** on this entry as a dependency once it is `[DONE]` / consumed.

**Wait for the FINISH to be confirmed before releasing the next work order — `Self-finalize: no` path (acp-ajudd#98/#100, scoped by #109).** In the toggle-off path, do not emit the next `pick up` work order (or otherwise treat this entry as done and pull its dependents) until the coding session returns its **`State: finished`** confirmation that `/session:finish` ran — a bare `implemented-deployed` return is a **ship, not a finish** (shipping ≠ closing). A `[DONE]` archive stamp on the entry is the reliable done-signal.

**Default self-finalize path — the fire-and-forget `finished` note is the TRIGGER, the `[DONE]` stamp is the CONFIRMATION (acp-ajudd#118, restores what #109 over-removed).** A dispatch-fed coding session that self-finalizes emits a one-way `coding ──▶ dispatch` `State: finished` block as its terminal output — it does **not** wait for a reply, and dispatch does not reply to it either. Treat the note as the signal to **re-check this entry now** rather than idling until the next inbox scan: confirm the `[DONE]` archive stamp landed (and glance at the tree if the work warrants it — validate-don't-rubber-stamp still holds, just post-hoc and non-blocking), then pull the next item / release any dependents held on it. If a `finished` note never arrives for a dispatch-fed entry (e.g. a fresh terminal that never returns to this one), fall back to sequencing off the inbox / `[DONE]` stamp / `depends-on` markers directly — the note is a convenience trigger, not a hard dependency dispatch blocks on.

### 7. Done — Touch Almost Nothing

Dispatch is read-only + notes-only: it wrote **no** session file, changed **no** `_active`, and **never mutated, edited, or consumed** an existing inbox entry. Its outputs were handoff notes (relayed by the human) plus — **only** in the named-exception case (acp-ajudd#95) — a **new** `work` entry that is a clear, no-refinement split of the work it was coordinating (minted via `inbox-id.py`, stamped `from <slug> / dispatch`). Where a `work` entry needed *refinement*, it stayed hands-off and routed the authoring to `refine`. The dispatch context stays alive and lean to drive the next item.
