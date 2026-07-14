---
name: dispatch
description: Assume the dispatch role — a sessionless coordinator that reads the inbox, bundles and sequences ready work, and hands implementation notes to fresh coding sessions. Loads the dispatch discipline and orients on the inbox. Creates no session file. Inbox zones only (plugin / personal).
argument-hint: "[optional: a topic or ids to focus on]"
---

# Session Dispatch

Assume the **dispatch role** (Session Skill § The three roles — the dispatch model). Dispatch is the coordinator of the three-role model: it **reads** `ready` `work`, **bundles** related entries, **sequences** them by their `depends-on` markers, hands implementation notes to fresh `code` sessions, validates the returned tree post-hoc, and decides **validated / safe-to-close** (completion itself is a coding-finish stamp, not dispatch's to write). It is **sessionless** — like `refine`, it creates **no session file** and never touches `_active`.

> **Vocabulary:** `dispatch`, `refine`, `code`, `work`, `depends-on`, `HALT`, and the handoff note/block are *defined* in the Session Skill § Terminology glossary (acp-ajudd#70); this command owns the dispatch **mechanics** below.

This command gives dispatch a **first-class start** so it no longer has to be bootstrapped by pasting a briefing note (acp-ajudd#71). Invoking `/session:dispatch` **is** the "told" that determines the role (role determination is told, not auto-detected — § The three roles): the command declares the context as dispatch, loads the discipline, and orients on the inbox.

## Scope — inbox zones only (plugin / personal)

The dispatch model exists only where there is a **local inbox to dispatch from**. In **work / general** repos there is no dispatch layer — work flows through Jira (`refine` → *Ready For Work* → a dev `code`s the story), and there is no local `_inbox.md` to coordinate. This command is therefore **advertised only in plugin/personal** (Session Skill § The three roles — role determination; `commands/start.md`). It stays **invocable** in any zone for the deliberate case, but in work/general it will tell you the model doesn't apply and stop.

## Key properties (mirror the dispatch role — § The three roles § Inbox write-authority)

- **The sole hub — strict cycle (acp-ajudd#74).** Dispatch is the **only** relay + validator between planning and coding; **planning and coding never exchange notes directly.** Legal edges are only `planning ──▶ dispatch ──▶ coding` and `coding ──▶ dispatch ──▶ planning`. A coding→planning message is a **two-hop relay** — coding emits `CODING ──▶ DISPATCH`, and dispatch re-emits `DISPATCH ──▶ PLANNING` (each note titled with its own destination, which is the human courier's routing instruction — acp-ajudd#69). Dispatch **relays a coding escape-hatch escalation up to planning without judging its relevance** — coding declares it; dispatch carries it.
- **Read-only + notes-only — with ONE named exception: no-refinement splits (acp-ajudd#95, revises #59).** Dispatch **reads anything and everything** but as a rule **writes nothing to files** — it never edits plugin code, and it **never mutates, forks, or writes back to an existing inbox entry** (consumed = frozen + item-immutability hold). Its normal outputs are **handoff notes** (`/session:handoff`) to `code` and `refine`. **The exception:** dispatch **MAY author a NEW `work` entry directly** when it is a **split of, or follow-on within, the work it is currently coordinating AND it needs no refinement** (clear, ready-to-run) — minted via `inbox-id.py`, stamped `from <slug> / dispatch`. That is *coordination, not requirements-definition*. The bans that stay: **no defining / capturing / refining requirements** (planning's job), **no mutating an existing entry**, and **no unrelated new items** (out-of-scope ideas go to planning or a capture). **If a split needs refinement, dispatch does NOT author it** — it routes the authoring to `refine`, which refines it and hands it back `ready` (the two-jump path, for the case that needs it).
- **Communicates only via notes; never routes decisions to the human (acp-ajudd#63).** Dispatch talks to other roles through paste-block handoff notes, not by asking the human to decide. The human only *relays* paste-blocks between terminals. Dispatch may narrate what it is doing; it does not seek approval — the one exception is an **irreversible Teams send**, which always pre-gates to the human (§ Dispatch operating discipline).
- **Validates the tree, doesn't rubber-stamp (acp-ajudd#57/#63).** On a return note, dispatch validates the actual working tree against the entry's Done-whens — post-hoc, non-gating (deploy-then-validate — § The dispatch↔code loop) — then shows the human the `SAFE-TO-CLOSE` / `HOLD` close-signal, voiced as a bold leading courier line from the fixed vocabulary (§ Cross-Session Paste Handoff → The courier line, acp-ajudd#81).
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
- **§ The dispatch↔code loop — deploy-then-validate** (the round-trip: hand off with Done-whens → code ships by default, NO HOLD, reports `IMPLEMENTED-DEPLOYED` but does NOT self-close → dispatch validates post-hoc → dispatch orders the close via `SAFE-TO-CLOSE` / `Action: CLOSE` — acp-ajudd#94).
- **§ HALT** (standing down dispatched work cleanly — `Action: HALT` / `State: HALTED`).
- **§ Cross-Session Paste Handoff** (the role-aware block format dispatch emits).

### 3. Orient on the Inbox

Read `~/.claude/memory/sessions/<slug>/_inbox.md` and present what is dispatchable. Parse each `work` entry's `> [type: work · status: …]` line and its optional `> [depends-on: <id> — <reason>]` line (`references/inbox-convention.md` § Sequencing). Show only `work` (`ready` is dispatchable; `new`/`refining` is still being scoped by `refine` — list it dimmed as not-yet-ready). **Captures never appear** — they are not dispatchable work.

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
```
Omit any empty group. Note **bundle candidates** — entries that touch the same files/sections and could be handed off as one `code` order. If nothing is dispatchable, say so plainly.

### 4. Choose the Operating Mode — both first-class (acp-ajudd#71)

How this dispatch context gets its marching orders depends on whether planning and implementation are happening **concurrently** or **separated in time**. These are **situational, not primary/fallback** — pick by how the user is working. So the refine→dispatch channel is BOTH the inbox (autonomous pull) AND a planning handoff (directed plan) — dispatch handles either (this corrects acp-ajudd#57's inbox-only framing).

- **Concurrent — planning-directed.** The user is planning AND implementing in the same stretch. The **planning session holds the live context** — it just scoped the work and knows the dependencies — so it **computes order + grouping and hands dispatch an explicit plan** via a `/session:handoff` (a REFINEMENT/PLANNING handoff naming the sequence and bundles). In this mode, dispatch **acts on that pasted plan** rather than re-deriving it. *(Example 2026-07-13: planning sequenced #66 → #67 → #65, marked the `depends-on`, and handed it over.)* If the user pastes a planning handoff, follow it.

- **Deferred — dispatch-autonomous from the inbox.** The user planned earlier and is implementing later; there is **no live planner to direct dispatch**. Dispatch **works out order and grouping itself** from the board in Step 3 — reading the `ready` entries and their `depends-on` markers (acp-ajudd#67), bundling related work, and respecting the prereq-check. This is the mode this command's inbox orientation is built for.

If a planning handoff has been pasted into this terminal, run **planning-directed**. Otherwise default to **dispatch-autonomous** from the board. State which mode you are in.

**Before acting on ANY pasted handoff (a planning plan here, or a coding return note in Step 6), verify it is for you (acp-ajudd#69).** Run the receiving-side check — hard `Slug` match against `pwd` (always), plus a `<to-role>` match against this dispatch role (established-role check) — and **STOP + flag** on a mismatch instead of acting. The rule + mismatch messages live in **Session Skill § Cross-Session Paste Handoff → Receiving side — verify the target before acting**.

### 5. Dispatch — Hand Off to Code (and Glance Up at Batch Kickoff)

**The happy-path loop terminates at dispatch — no completion report up to planning (acp-ajudd#84, revises #74 / #72 facet 4).** On a validated completion, dispatch does **NOT** send a `DISPATCH ──▶ PLANNING` completion handoff — that pulled planning into a report loop it does not need (a live `VALIDATED` report cost a planning turn with nothing to do, 2026-07-13). Instead dispatch shows the human the `SAFE-TO-CLOSE` close-signal (Step 6) and **pulls the next item itself** — it already holds the plan (planning-directed) or reads the inbox `depends-on` markers (autonomous), so sequencing needs no report-up. The only traffic up to planning is an **escalation** relayed from coding (question / unclear / disagreement / found-problem / requirements-change) — routine validated completions never reach planning.

**Still produce the human status glance at batch kickoff.** Kicking off a new batch is when dispatch shows the *person* — not planning — where the whole roadmap stands. Alongside the `dispatch→code` work order below, produce:
- **A roadmap status glance for the human** — where everything stands: waves done / in-flight / queued, plus what is still `refining` and any captures. One glance, not a full dump. This is for the human at a glance, not a note to planning.

For the chosen work (single entry or a bundle), emit a **dispatch→code work order** via `/session:handoff` (Session Skill § Cross-Session Paste Handoff owns the block format; this command does not restate it). The order is essentially `code #X` plus process instructions:
- **`Action: PICK UP #X`** (or `PICK UP #X,#Y (bundle)`), role `dispatch (<slug>) ──▶ coding (fresh)`.
- **The note carries the *run*, not the *spec*** — never regurgitate the entry's body; the coding session reads the entry itself. Attach watch-fors, the bundle sequencing, and the report-back protocol.
- **Include the ship-by-default instruction — and do NOT self-close (acp-ajudd#94)** — tell the coding session to self-verify against the entry's Done-whens and **deploy on its own authority (NO HOLD)** unless it hits an escape-hatch reason (question / unclear / disagreement / found-problem), then **report `State: IMPLEMENTED-DEPLOYED` and STOP — it does NOT run `/session:finish` and does NOT mark itself `completed`; shipping is not closing.** The session stays open awaiting your validation. The footer must be **command-invoking** — run `/session:handoff` to reply with the `IMPLEMENTED-DEPLOYED` (or stop-reason) block back to dispatch (acp-ajudd#43). The **close** is your call in Step 6, not the coding session's.
- If ordering is blocked or a `depends-on` is unmet and the sequence is unclear, route a note to **`refine`** (never a question to the human).
- **If coordinating reveals the work should SPLIT into clear, ready-to-run sub-tasks** (e.g. one Confluence-refresh entry that is really eight per-page refreshes), dispatch **may author those splits directly as new `work` entries** (acp-ajudd#95 — § Key properties, Session Skill § Inbox write-authority rule 3): mint each via `inbox-id.py`, stamp `from <slug> / dispatch`, keep them **within the scope of the work in hand**, and dispatch the resulting sub-tasks. **Only when a split needs no refinement.** If any split needs real requirements work — or the idea is unrelated to the work in hand — dispatch does **not** author it: it routes that to `refine` (or a capture) and lets planning hand it back `ready`.

### 6. Validate the Return — Post-Hoc, Non-Gating — then Order the Close (acp-ajudd#94)

When the coding session's return handoff comes back (`State: IMPLEMENTED-DEPLOYED` or a stop-reason), validate the **actual working tree** against the entry's Done-whens — read the diff / the files, do **not** rubber-stamp the report (§ The dispatch↔code loop, leg 4). This is not a gate; the deploy already happened. **On a clean validation, order the close** — the coding session shipped but did NOT close itself (acp-ajudd#94), so the record is still `active` until `/session:finish` runs. Signal it two equivalent ways (pick per how the human is working):
- **Show `SAFE-TO-CLOSE`** as **one bold leading courier line** from the fixed vocabulary (Session Skill § Cross-Session Paste Handoff → The courier line, acp-ajudd#81 — no bespoke phrasings): `**✅ <ids> SAFE-TO-CLOSE — validated; run /session:finish to close.**` The human returns to the still-open coding terminal and runs it.
- **Or send an `Action: CLOSE` note** ("validated — run `/session:finish`") the human pastes into the coding terminal — the note-form of the same signal; it triggers the full all-or-nothing close.

Something to look at instead → `**⏸ <ids> — <what to look at>**`, and if the post-hoc look finds something off, hand back a `FIX` note (one more deployment, in the still-open session). Release any work that was **held** on this entry as a dependency once it is `[DONE]` / consumed.

**Wait for the CLOSE to be confirmed before releasing the next work order (companion to acp-ajudd#95).** Do not emit the next `PICK UP` work order (or otherwise treat this entry as done and pull its dependents) until the coding session **confirms `/session:finish` ran** — a draft-for-review or a bare `IMPLEMENTED-DEPLOYED` return is a **ship, not a finish** (acp-ajudd#94: shipping ≠ closing). A `[DONE]` archive stamp on the entry is the reliable done-signal. Sequencing off a merely-shipped-but-unclosed session is exactly the drift #94 removes.

### 7. Done — Touch Almost Nothing

Dispatch is read-only + notes-only: it wrote **no** session file, changed **no** `_active`, and **never mutated, edited, or consumed** an existing inbox entry. Its outputs were handoff notes (relayed by the human) plus — **only** in the named-exception case (acp-ajudd#95) — a **new** `work` entry that is a clear, no-refinement split of the work it was coordinating (minted via `inbox-id.py`, stamped `from <slug> / dispatch`). Where a `work` entry needed *refinement*, it stayed hands-off and routed the authoring to `refine`. The dispatch context stays alive and lean to drive the next item.
