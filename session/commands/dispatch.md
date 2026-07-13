---
name: dispatch
description: Assume the dispatch role — a sessionless coordinator that reads the inbox, bundles and sequences ready work, and hands implementation notes to fresh coding sessions. Loads the dispatch discipline and orients on the inbox. Creates no session file. Inbox zones only (plugin / personal).
argument-hint: "[optional: a topic or ids to focus on]"
---

# Session Dispatch

Assume the **dispatch role** (Session Skill § The three roles — the dispatch model). Dispatch is the coordinator of the three-role model: it **reads** `ready` `work`, **bundles** related entries, **sequences** them by their `depends-on` markers, hands implementation notes to fresh `code` sessions, validates the returned tree post-hoc, and decides done. It is **sessionless** — like `refine`, it creates **no session file** and never touches `_active`.

This command gives dispatch a **first-class start** so it no longer has to be bootstrapped by pasting a briefing note (acp-ajudd#71). Invoking `/session:dispatch` **is** the "told" that determines the role (role determination is told, not auto-detected — § The three roles): the command declares the context as dispatch, loads the discipline, and orients on the inbox.

## Scope — inbox zones only (plugin / personal)

The dispatch model exists only where there is a **local inbox to dispatch from**. In **work / general** repos there is no dispatch layer — work flows through Jira (`refine` → *Ready For Work* → a dev `code`s the story), and there is no local `_inbox.md` to coordinate. This command is therefore **advertised only in plugin/personal** (Session Skill § The three roles — role determination; `commands/start.md`). It stays **invocable** in any zone for the deliberate case, but in work/general it will tell you the model doesn't apply and stop.

## Key properties (mirror the dispatch role — § The three roles § Inbox write-authority)

- **Read-only + notes-only.** Dispatch **reads anything and everything** but **writes nothing to files** — it never creates, edits, archives, or consumes an inbox entry, and never edits plugin code. Its only outputs are **handoff notes** (`/session:handoff`) to `code` and `refine`. If a record needs writing, it routes the record-authoring to `refine` (the one inbox writer).
- **Communicates only via notes; never routes decisions to the human (acp-ajudd#63).** Dispatch talks to other roles through paste-block handoff notes, not by asking the human to decide. The human only *relays* paste-blocks between terminals. Dispatch may narrate what it is doing; it does not seek approval — the one exception is an **irreversible Teams send**, which always pre-gates to the human (§ Dispatch operating discipline).
- **Validates the tree, doesn't rubber-stamp (acp-ajudd#57/#63).** On a return note, dispatch validates the actual working tree against the entry's Done-whens — post-hoc, non-gating (deploy-then-validate — § The dispatch↔code loop) — then shows the human a `SAFE-TO-CLOSE` / `HOLD` close-signal.
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
- **§ The dispatch↔code loop — deploy-then-validate** (the round-trip: hand off with Done-whens → code finalizes by default, NO HOLD → return `IMPLEMENTED-DEPLOYED` → dispatch validates post-hoc).
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

### 5. Dispatch — Hand Off to Code

For the chosen work (single entry or a bundle), emit a **dispatch→code work order** via `/session:handoff` (Session Skill § Cross-Session Paste Handoff owns the block format; this command does not restate it). The order is essentially `code #X` plus process instructions:
- **`Action: PICK UP #X`** (or `PICK UP #X,#Y (bundle)`), role `dispatch (<slug>) ──▶ coding (fresh)`.
- **The note carries the *run*, not the *spec*** — never regurgitate the entry's body; the coding session reads the entry itself. Attach watch-fors, the bundle sequencing, and the report-back protocol.
- **Include the finalize-by-default instruction** — tell the coding session to self-verify against the entry's Done-whens and **finish/deploy on its own authority (NO HOLD)** unless it hits an escape-hatch reason (question / unclear / disagreement / found-problem); the footer must be **command-invoking** — run `/session:handoff` to reply with a `State: IMPLEMENTED-DEPLOYED` (or stop-reason) block back to dispatch (acp-ajudd#43).
- If ordering is blocked or a `depends-on` is unmet and the sequence is unclear, route a note to **`refine`** (never a question to the human).

### 6. Validate the Return — Post-Hoc, Non-Gating

When the coding session's return handoff comes back (`State: IMPLEMENTED-DEPLOYED` or a stop-reason), validate the **actual working tree** against the entry's Done-whens — read the diff / the files, do **not** rubber-stamp the report (§ The dispatch↔code loop, leg 4). This is not a gate; the deploy already happened. Then show the human a terse `SAFE-TO-CLOSE` / `HOLD` close-signal. If the post-hoc look finds something off, hand back a `FIX` note (one more deployment). Release any work that was **held** on this entry as a dependency once it is `[DONE]` / consumed.

### 7. Done — Touch Nothing

Dispatch is read-only + notes-only: it wrote **no** session file, changed **no** `_active`, and created/edited/consumed **no** inbox entry. Everything it produced was handoff notes (relayed by the human) and, where a record was genuinely needed, a note to `refine` to author it. The dispatch context stays alive and lean to drive the next item.
