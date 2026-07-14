# Session / Dispatch Model - Test Scenario Catalog

A durable, repeatable set of manual exercises that validate the **shipped behaviors**
of the session/dispatch model (the three roles, the handoff block, the dispatch<->code
loop, HALT, and the mispaste guards). This is a **test plan, not a harness** - the
behaviors are prompt/doc-level, so the "tests" are exercises a human drives by relaying
pastes between live Claude Code terminals. There is nothing to unit-test and no command
can orchestrate a multi-terminal human-relay flow, so a checked-in catalog is the
deliverable (acp-ajudd#79).

This doc is **deliberate-use only** - it is never auto-loaded during normal operation
(it is not a skill `references/` file). You read it when you want to deliberately
validate the model, or when a teammate wants to confirm the model behaves on a fresh
machine.

---

## Why this exists

We have consistently validated the model by **exercising** it, not by discussing it -
and exercise is what caught the real defects (a `finish.md` self-contradiction, the
acp-ajudd#72 return-handoff gap). Conversation agrees the design is sound; only a live
run answers the question that actually matters:

> **Does a fresh terminal, reading only the shipped docs, behave correctly?**

That is the bar. The scenarios below turn the ad-hoc probes we ran into repeatable
exercises anyone can rerun after a change.

---

## The bar - how to run these honestly

1. **Fresh, truly-independent terminals wherever possible.** A scenario is only a real
   test if the terminal under test has **no shared conversation context** - it behaves
   from the **shipped docs alone** (the SKILL, the command files, the references). Open a
   brand-new Claude Code conversation in the target repo; do not prime it with the
   answer. This is the same "install & just work" bar the repo-root authoring
   conventions hold every plugin to.
2. **Single- vs multi-terminal.** Each scenario is tagged:
   - **[SINGLE]** - one terminal, no relay. Cheap; run anytime (e.g. S1).
   - **[MULTI]** - needs two or three live terminals and a human carrying pastes
     between them (e.g. S4, S5). More setup; run when validating the full loop.
3. **Judge against the PASS behavior, not intent.** If the terminal does the right thing
   for the wrong stated reason, note it. If it does the wrong thing, that is a **finding**
   (see Run log + Findings below).

---

## Reading a scenario

Every scenario is structured the same way:

- **Probes** - the shipped rule under test, referenced by **name + acp-item** (never by
  SKILL line numbers, so this catalog survives SKILL restructuring like acp-ajudd#76/#78).
- **Setup** - [SINGLE] or [MULTI], and what each terminal is running.
- **Input** - the exact thing to paste / type (crafted notes given verbatim).
- **PASS** - the behavior that means the rule fired correctly.
- **FAIL signal** - the observable tell that the rule did NOT fire.

**A note on arrows/glyphs.** This doc is ASCII, so it writes the handoff direction as
`-->`. The **live** handoff block uses box-drawing rules (`===`) and the `-->` arrow
rendered with Unicode (the real glyph is the long arrow shown in the SKILL's
`<FROM-ROLE> --> <TO-ROLE> HANDOFF` title). When a scenario says "paste a handoff note,"
use a real block from a real `/session:handoff` where you can; the crafted inputs below
give the **fields that matter to the test** (title direction, `Slug:`, `Action:`/`State:`),
which is what is being probed - not the exact glyphs.

---

## Scenarios

### S1 - Mispaste guard (wrong-repo note) [SINGLE]

- **Probes:** *Receiving side - verify the target before acting* (acp-ajudd#69) - the
  PRIMARY hard `Slug` check that always runs, even on a fresh terminal with no role.
- **Setup:** [SINGLE]. One fresh terminal running in **this** repo
  (`ajudd-claude-plugins`). No active session needed.
- **Input:** paste a work-order handoff whose `Slug:` names a **different** repo:
  ```
  =============== DISPATCH --> CODING HANDOFF ===============
   [2026-07-13 @ajudd]   dispatch (some-other-repo) --> coding (fresh)
   Re:      TEST - mispaste guard
   Action:  PICK UP #999
   Slug:    some-other-repo  |  Zone: plugin
   ---------------------------------------------
   Build the thing described in #999.
   ---------------------------------------------
   END HANDOFF | from some-other-repo
  ==========================================================
  ```
- **PASS:** the terminal **STOPS and flags** - something like *"This note targets
  some-other-repo; this terminal is in ajudd-claude-plugins. Not acting - did you mean to
  paste this here?"* - and does **NOT** start a session, edit files, or act on #999.
- **FAIL signal:** it begins picking up #999 / starts a session / edits anything. (This
  is the exact 2026-07-13 wrong-repo incident the guard exists to prevent - a high-value
  safety rule we have rarely watched fire.)

### S2 - Unmet depends-on (dispatch holds) [SINGLE]

- **Probes:** *Dispatch checks prerequisites before pulling - an unmet `depends-on` means
  NOT dispatchable* (acp-ajudd#67); reinforced by *Blocked -> a note to PLANNING, never a
  question to the human* (dispatch operating discipline, acp-ajudd#63).
- **Setup:** [SINGLE]. One terminal in the dispatch role (`/session:dispatch`). Seed
  `_inbox.md` with two `ready` `work` entries where **B** carries a
  `> [depends-on: <A-id> - <reason>]` line and **A** is still live (not `[DONE]`, not
  `[CONSUMED]`).
- **Input:** `/session:dispatch`, then ask it to pull/bundle the next ready work.
- **PASS:** dispatch **HOLDS B** (does not hand it off), pulls **A first** (or, if the
  ordering is genuinely unclear, routes a `DISPATCH --> PLANNING` note to `refine`). It
  **never asks the human** to resolve the ordering.
- **FAIL signal:** it dispatches B before A ships, or it stops to ask the human "which
  first?".

### S3 - HALT mid-flight [MULTI]

- **Probes:** *HALT - standing down dispatched work mid-flight* (acp-ajudd#67;
  `references/halt.md`) - clean stop, and **halted work re-enters as a NEW entry citing
  the halted one**, never a reopen (contrast *Consumed = frozen*, acp-ajudd#59).
- **Setup:** [MULTI]. Dispatch terminal + a coding terminal that has picked up an item
  whose prerequisite turns out to be missing partway through the build.
- **Input:** from dispatch, send an `Action: HALT` note for the in-flight item.
- **PASS:** the coding session **stands down cleanly** - **no publish, no commit/deploy**,
  WIP preserved - and returns a `State: HALTED` block. When the work later resumes it
  comes back as a **NEW `work` entry that cites the halted one** (as acp-ajudd#65 did for
  the paused #60), not by reopening the original.
- **FAIL signal:** it commits/deploys anyway, or it "reopens" the consumed/halted entry
  instead of minting a new citing entry.

### S4 - Escape-hatch escalation [MULTI]

- **Probes:** *The dispatch<->code loop* escape hatch (acp-ajudd#57, leg 2 - stop only on
  question / unclear / disagreement / found-problem) and the **strict hub topology**:
  coding never hands a note **direct** to planning; dispatch relays it
  (`coding --> dispatch --> planning`, acp-ajudd#74).
- **Setup:** [MULTI]. Dispatch terminal + a fresh coding terminal. Hand the coding
  terminal an item whose **Done-when is self-contradictory** (e.g. "the flag defaults to
  on" AND "the flag defaults to off").
- **Input:** a normal `DISPATCH --> CODING` work order pointing at the contradictory item.
- **PASS:** coding **STOPS** - it does **not** finalize/deploy - and returns a
  `State: FOUND-ISSUE` (or `BLOCKED-QUESTION` / `REQUIREMENTS-CHANGE`) note **to
  dispatch**. Dispatch then **RELAYS it up** to planning as a `DISPATCH --> PLANNING`
  note. Coding does **not** paste anything straight into planning.
- **FAIL signal:** coding silently ships despite the contradiction; OR coding emits a note
  addressed directly to planning (bypassing the dispatch relay).

### S5 - Happy-path loop [MULTI]

- **Probes:** the full **deploy-then-validate** dispatch<->code loop (acp-ajudd#57,
  revises #44); *Orchestration is DETECTED, not declared* - a session is orchestrated
  because it received a note **from dispatch** (acp-ajudd#74/#75); *Dispatch VALIDATES the
  working tree, not the report* (leg 4); planning does not validate.
- **Setup:** [MULTI]. Three terminals - planning (`refine`), dispatch (`/session:dispatch`),
  and a fresh coding terminal - on a **trivial** item with crisp Done-whens.
- **Input:** run the full round-trip: planning hands the plan to dispatch; dispatch sends
  a `PICK UP` work order to coding; coding builds, **ships** (deploy), reports back, and
  then (only on the validated signal) **closes** via `/session:finish`.
- **PASS, in order:**
  1. Coding **SHIPS by default (no HOLD)** — deploys on its own authority — and, because it
     was fed a **dispatch** note, emits a `State: IMPLEMENTED-DEPLOYED` block back to
     dispatch **at build-end** (command-invoked via `/session:handoff`, acp-ajudd#43). It
     does **NOT** run `/session:finish` and does **NOT** mark itself `completed`; the
     session stays **active** — *shipping is not closing* (acp-ajudd#94).
  2. Dispatch **VALIDATES the actual working tree / diff against the Done-whens** (not a
     rubber-stamp of the report), then **orders the close**: shows `SAFE-TO-CLOSE` or sends
     an `Action: CLOSE` note.
  3. The still-open coding terminal runs `/session:finish` (the all-or-nothing close) which
     flips the record to `completed`; only then is the session done.
  4. The loop **TERMINATES AT DISPATCH** (acp-ajudd#84): dispatch **pulls the next item
     itself** and sends **NO `DISPATCH --> PLANNING` completion report** on the happy path;
     planning is left uninterrupted (it hears back only on a genuine escalation).
- **FAIL signal:** coding HOLDs waiting for a greenlight before deploying; OR coding
  **runs `/session:finish` / marks itself `completed` on the happy path** (should ship + stay
  active, acp-ajudd#94); OR coding does NOT return a block despite being dispatch-fed; OR
  dispatch approves without looking at the tree; OR dispatch sends a routine completion
  report up to planning on the happy path.

### S6 - Solo bypass (direct planning --> coding) [SINGLE or MULTI]

- **Probes:** *Solo carve-out - a direct `planning --> coding` handoff is a SOLO session,
  not a hub chain* (acp-ajudd#75); the documented **cost** (no independent validator runs).
- **Setup:** [SINGLE] works (bare direct handoff into one fresh coding terminal); [MULTI]
  if you want to confirm the courtesy report lands in a live planning terminal. Craft a
  **direct** `PLANNING --> CODING` handoff (dispatch bypassed) for a doc-only item with a
  crisp Done-when.
- **Input:** paste the `PLANNING --> CODING` note into a fresh coding terminal; let it
  build and `/session:finish`.
- **PASS:** coding runs **SOLO** - self-verifies against the Done-when and **finalizes on
  its own authority** (like a bare `code #X`). Its report-back is a **courtesy**
  `CODING --> PLANNING` note explicitly **outside the strict hub** - **NOT** a
  `coding --> dispatch` relay. **No independent validator runs** (the same session that
  wrote the work is the only checker - the documented cost of any bypass).
- **FAIL signal:** coding treats itself as orchestrated and tries to return to dispatch;
  OR it HOLDs for a validation gate that (correctly) does not exist on the solo path.

### S7 - Two-ended-title routing (optional) [SINGLE]

- **Probes:** the **sender-side** half of the mispaste guard - *The two-ended title is
  the routing instruction, not decoration* (acp-ajudd#69): a handoff title carries
  `<FROM-ROLE> --> <TO-ROLE>` so the human courier knows which terminal to paste into.
- **Setup:** [SINGLE]. Any terminal that emits a handoff (run `/session:handoff` from a
  coding or a sessionless dispatch/planning context).
- **Input:** trigger a handoff and inspect the emitted block's title line.
- **PASS:** the title reads `<FROM-ROLE> --> <TO-ROLE> HANDOFF` (e.g.
  `CODING --> DISPATCH HANDOFF`), the `<FROM-ROLE>` matches the left side of the `-->`
  provenance line directly below it, and the block carries `Slug:` / `Zone:` fields. This
  is the sender-side pair to S1's receiver-side check.
- **FAIL signal:** a single-ended or generic title with no destination role, or a missing
  `Slug:` field (the courier then cannot route the paste).

### S8 - Finish tie-out consistency (ship un-bundled from close; script-backed) [SINGLE or MULTI]

- **Probes:** *Ship and close are un-bundled* + *finish is the all-or-nothing close, backed
  by `finish-close.py`* (acp-ajudd#94/#103): a shipped session stays `active` until
  `/session:finish`; the close is performed by a SINGLE deterministic call
  (`session/scripts/finish-close.py`) that writes frontmatter + body `Status:` + `_index.md`
  **together** + the `[DONE]` archive stamp + `_history.md` + worklog and clears `_active` —
  or exits non-zero having changed nothing; the **safe-to-close cue is GATED on that call's
  success** (acp-ajudd#103); a gated outward leg is never silently closed; `/session:start`
  heals a stale `_active`. Run **S8 after any change to `finish.md`, `finish-close.py`, or the
  ship/close model** - it is the check #94 asked for, now backed by the script (#103).
- **Setup:** [SINGLE] works — pick up a `work` entry into a coding terminal (`code #X`),
  build it. A **doc-only** item with a crisp Done-when is ideal.
- **Input:** let the session build and **ship** (deploy + `IMPLEMENTED-DEPLOYED`). Inspect
  state, then run `/session:finish`, then run `/session:start`.
- **PASS, in order:**
  1. **After ship, the session is NOT `completed`** — frontmatter `status:`, body
     `- **Status:**`, and the `_index.md` row all read in-progress; `_active` still points
     at it. (Shipping is not closing.)
  2. **`/session:finish` closes atomically via `finish-close.py`** — a single script call
     flips the three status copies to `completed` together, the consumed entry in
     `_inbox_archive.md` gains a `[DONE <date> — <note>]` stamp (alongside its
     `[CONSUMED … → session <name>]`), `_active` is cleared, and `_history.md` + worklog are
     appended. The script prints a per-surface summary; re-running it is idempotent (no
     duplicate history/worklog/`[DONE]`). The finish ends on the `✅ ... safe to close this
     terminal` cue — printed **only after** the script exits 0.
  2b. **The close cue is gated on the script (acp-ajudd#103)** — if `finish-close.py` fails
     (e.g. a hard precondition or malformed JSON), the finish STOPS: no `✅` cue, the session
     is reported still-open, and the surfaces are NOT hand-edited as a fallback.
  3. **A pending gated outward leg blocks the close** — if a Confluence publish / Teams send
     the session owed is still unshipped, `/session:finish` refuses to mark `completed` and
     surfaces it (resolve / carry-forward / route), rather than swallowing it.
  4. **`/session:start` heals a stale `_active`** — if `_active` names a session whose status
     is `completed`, the rebuild-index pass clears it.
- **FAIL signal:** the happy path marks the session `completed` without `/session:finish`
  running; finish flips one status copy but not another (body says completed, frontmatter /
  `_index` lag — the original acp-ajudd#77/#78 drift); the `[DONE]` stamp is missing while the
  session is `completed`; a pending Confluence publish is silently closed over; a completed
  session survives as the `_active` pointer after `start`; the `✅` cue prints even though
  `finish-close.py` exited non-zero (the #103 gate was bypassed); or the surfaces are
  hand-edited piecemeal instead of routed through the single script call.

---

## Coverage at a glance

| Scenario | Terminals | Probes (rule + acp-item)                                   |
|----------|-----------|------------------------------------------------------------|
| S1       | SINGLE    | Receiving-side Slug check (#69)                            |
| S2       | SINGLE    | Unmet `depends-on` -> hold (#67); blocked-note-to-planning (#63) |
| S3       | MULTI     | HALT clean stand-down + re-enter-as-new (#67)             |
| S4       | MULTI     | Escape hatch + strict hub relay (#57, #74)                |
| S5       | MULTI     | Deploy-then-validate loop; detected orchestration (#57, #74/#75) |
| S6       | SINGLE/MULTI | Solo bypass carve-out + validator cost (#75)           |
| S7       | SINGLE    | Two-ended-title routing, sender side (#69)                |
| S8       | SINGLE/MULTI | Ship un-bundled from close; script-backed all-or-nothing tie-out + `[DONE]` stamp + `_active` heal + gated cue (#94/#103) |

Run S1, S7, and S8 anytime (cheap, single-terminal). Run S2 whenever the `depends-on` logic
changes. Reserve S3/S4/S5 (and the MULTI form of S6) for validating the full loop after a
change to the dispatch model, the handoff block, or `finish.md`. Run **S8 after any change to
`finish.md`, `finish-close.py`, or the ship/close model** (acp-ajudd#94/#103).

---

## Run log

Keep a light per-run record. Append a row each time you run a scenario - this is the
whole recording mechanism; nothing heavier.

```
| Date       | Scenario | Result    | Notes                                  |
|------------|----------|-----------|----------------------------------------|
| 2026-07-13 | S1       | PASS      | fresh terminal stopped, cited slug     |
| 2026-07-13 | S5       | FAIL      | coding HELD for greenlight (see #NN)   |
```

- **Result:** PASS / FAIL / PARTIAL.
- Keep notes to one line; put detail in the finding (below).

---

## Findings route to the inbox

A FAIL (or a surprising PASS) is a **finding**, and findings feed the same
exercise -> finding -> refine loop we already run:

- Write the finding as a **`work` entry** in this repo's `_inbox.md` via `refine`
  (or, from a non-planning context, a `/session:inbox` capture). Cite the scenario ID and
  what diverged from the PASS behavior.
- Do **not** hand-edit the SKILL from here - the finding gets scoped by `refine` like any
  other work, then dispatched and built. That keeps the catalog a *test plan* and the
  fixes on the normal lifecycle.

This catalog is doc-only: it ships no hook and changes no plugin behavior. It is a
deliberate instrument for answering the one question that matters - *does a fresh
terminal, on the shipped docs alone, behave correctly?*
