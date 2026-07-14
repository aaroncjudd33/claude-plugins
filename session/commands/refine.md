---
name: refine
description: Analyze-then-scope flow — explore the repo and project memories, turn raw requirements or a bug into a well-scoped work entry or Jira story. Graduates zone-aware. Creates no session file.
argument-hint: "[topic, story area, or existing work to resume]"
---

# Session Refine

An **analyze-then-scope** flow for scoping work before any code is written. Paste in rough requirements or a bug, ask questions, and have Claude ground the answers in the actual repo and its project memories — writing well-scoped **work** that an implementation session later picks up.

> **Vocabulary:** `refine`, `work`, `capture`, `stance`, and the `new → refining → ready` lifecycle are *defined* in the Session Skill § Terminology glossary (acp-ajudd#70); this command owns the refine **mechanics** below.

Refine is universal. What the work *is* — a `work` inbox entry or a Jira story — is decided **strictly by the repo's zone**, never by who runs it, and with no override or target picker:

- **Plugin / personal** (item-driven) → a **`work` entry** in `_inbox.md`.
- **Work repo (story/cab)** → a **Jira story** (work's work-repo form; project resolved-or-confirmed, never hardcoded).
- **General** → **no system of record — refine creates nothing.** A general repo has nothing to graduate into; the only thing that can leave a refine here is a `/session:inbox` capture aimed at another slug (a separate concern — see below). Scope verbally, hand off via a capture if needed.

## The model: the work IS the work-in-progress store

Refinement does **not** get its own session file — in any zone. The realization: **the work you're producing is itself where the work-in-progress lives, and it is also the final deliverable.** You create the work early, iterate on it across as many sittings as you need, and when it's matured you mark it **ready** — the single trigger that says "an implementation session can pick this up." A session file is only ever created for *work being done* (a coding session), never for scoping the work.

This is exactly Heber's Jira flow — rough story → iterate → *Ready For Work* — and it is identical in a plugin/personal repo, where **a `work` inbox entry is what a Jira story is**:

| Zone | The work (= WIP store = deliverable) | "still scoping" state | graduation trigger |
|------|--------------------------------------|-----------------------|--------------------|
| plugin / personal | `work` entry in `_inbox.md` | `type: work · status: refining` | flip to `status: ready` |
| work repo | Jira story | *Gathering Requirements* | transition to *Ready For Work* |
| general | none — nothing is created | n/a | n/a (verbal scope; hand off via a `/session:inbox` capture) |

Both the **write-early** path ("scope some, come back later, keep polishing") and the **one-shot** path ("scope it and mark ready in one sitting") are the same flow — the only difference is how mature the work is when you stop. Create-at-graduation is just the degenerate case where you finish in one sitting.

## Key properties

- **Read-only toward code.** Refine scopes; it does not implement. Writing/editing the *work* (a `work` entry under `~/.claude/memory/`, or a Jira story) is not a code edit — refine writes the work freely. If asked to implement, graduate the work and stop — a *separate* `code` gesture by whoever builds it opens the coding session; refine never opens it itself (§ Graduate HARD RULE). (Nothing hard-blocks a code edit either — acp-ajudd#1 removed edit-blocking — but refine's *job* is to scope, not build; keep it that way by convention.)
- **Refine owns in-place requirement edits (acp-ajudd#13).** Editing a `work` entry's body / requirements / acceptance criteria in place is refine's job — that is exactly what the write-early + iterate loop below does. The mirror boundary: a **coding session must NOT** rewrite the requirements of an existing `work` entry or Jira story it (or anyone) picked up. When a coding session finds a requirement needs changing, it hands off — a `/session:inbox` capture, or back to a refine pass — rather than editing the work inline. So requirement changes always flow through refine.
- **Writing your zone's work vs. firing a capture are separate concerns (acp-ajudd#21).** Refine's *work* target is locked by zone (above). Dropping a **capture** into an inbox via `/session:inbox` — a raw inbound entry another session dispositions on read — is independent and available from any context. In a work repo, refine's work is the Jira story, so the only thing refine ever puts in an inbox is a capture (an FYI / handoff aimed at another slug) — never a promoted `refining`/`ready` inbox entry. In plugin/personal the `work` entry refine writes **is** the work: it lives in `_inbox.md` at `status: refining` and matures to `ready` in place — that's a promoted capture, not an inbound capture-for-someone-else, so it's correct, not a violation. There is no `type` axis (`note`/`data`/`story` are gone) — just captures on one lifecycle; don't conflate writing your own work with firing a capture at another slug.
- **No session file, no `_active` change.** Refine creates nothing under `<session_root>` and never touches `_active`. A coding session already active stays active *alongside* a refine, unaffected. (This is what decoupled refine from the `_active` redesign.)
- **Nothing to expire or migrate.** With no session file there is no `refinement-*.md` to sweep, hide, or exclude from `session:migrate`. The work's own history (git for inbox entries, Jira for stories) is the trail.
- **Resumable through the work itself.** A `refining` `work` entry shows up in `/session:start`'s inbox listing as resumable (marked `refining`); a work-repo story in *Gathering Requirements* is a first-class Jira object you reopen with `refine BPT2-XXXX` (or find via `/story:dashboard`).
- **Verify a pasted handoff is for you before acting on it (acp-ajudd#69).** Refine receives `dispatch ──▶ planning` escalations (a blocked/ambiguous item routed up for re-scoping). Before acting on any pasted handoff block, run the receiving-side check — hard `Slug` match against `pwd`, plus a `<to-role>` match against this refine/planning role — and **STOP + flag** on a mismatch. Rule + messages: **Session Skill § Cross-Session Paste Handoff → Receiving side — verify the target before acting**.

## Instructions

### 1. Resolve, Detect Zone, and Decide New-vs-Resume

Run `pwd`, extract the repo slug. Read `handle` per the Session Skill's handle lookup. **Detect the zone** — this decides the work's form in Steps 2–4. Read `~/.claude/plugins/user-config.json` → `paths` and classify the current repo (pwd), same logic as `session:start`:

| Zone | Detection | Produces |
|------|-----------|--------|
| **plugin** | pwd contains `pluginMarketplaceName` | `work` entry in `_inbox.md` (unambiguous — no target confirmation) |
| **personal** | pwd begins with `personalProjectsDir` (fallback: contains `/c/claude/`) | `work` entry in `_inbox.md` (unambiguous — no target confirmation) |
| **work repo (story/cab)** | pwd begins with `workReposDir` (fallback: contains `/dev/`) | Jira story — project resolved-or-confirmed, **never hardcoded** |
| **general** | anything else | **no system of record — nothing is created** (scope verbally; hand off via a `/session:inbox` capture if needed) |

**Do not warn or block** when refine runs outside a work repo — refine is welcome everywhere; it just graduates to the right kind of work for the zone. **The target is strictly the zone — there is no override and no target picker.** For work repos the Jira **project** is not assumed to be `BPT2` — resolve from context or confirm the project (that is the only thing ever confirmed; the *kind* of work is fixed by zone). For general, nothing is created at all.

**One-of-each advisory (read-only — acp-ajudd#41).** After resolving the slug, check `_active` + `_index.md` status for the slug. If an in-progress **coding session** already exists, print exactly this one line and then proceed — refine is sessionless planning, so this never blocks and never changes what refine does:

  `Note: coding session '<name>' is already active for this slug — starting here makes two (one-of-each discipline).`

Read-only, one glance, no monitoring — same category as the captures-waiting glance. It keeps the "one planning + one coding per repo" ceiling (acp-ajudd#30) visible at the planning entry point without any hook (acp-ajudd#1). Omit the line entirely when no coding session is active.

**New, resume, or promote** (from the argument):
- **An existing inbox entry's `<id>`** (e.g. `refine acp-ajudd#12`) → read the entry and branch on its `type`/`status` line:
  - **`type: capture`** → **promote to `work`** (acp-ajudd#62). A capture is raw inbound; refine is where it becomes tracked work. Rewrite its metadata line `> [type: capture]` → `> [type: work · status: refining]` **in place** — preserve the header, `<id>`, and provenance verbatim; only the type/status line changes. Surface it plainly: `Promoted <id> (capture → work, refining) — <one-line summary>`. Then continue scoping from Step 3, editing the same entry. (Skip Step 2's *creation* — the entry already exists — but still run its memory scan for context.)
  - **`type: work · status: refining`** (or legacy `status: refining`) → **resume**: continue refining that entry in place from Step 3 (skip creation; still load memories).
- **A Jira key** (`refine BPT2-6429`) → **resume** (work repo): `getJiraIssue`, then **print the story's status first, every time** (`BPT2-6429 — <status> — <summary>`), then apply the **status-tiered edit guard** below before editing, and continue refining in place from Step 3 (skip creation; still load memories).
- **A topic / free text** (`refine shopify refund window`) → **new**: proceed to Step 2.
- **Nothing (bare `refine`)** → surface what's resumable for the zone, then route:
  - **Plugin / personal** → read `_inbox.md` and **first surface any waiting captures** — this is where the `capture ─▶ refine` loop closes (acp-ajudd#96): the `capture` window fills the hopper, and bare `refine` is where planning drains it. Count `capture`-type entries (`> [type: capture]`; legacy `type: note` / `type: data` / `status: capture` also count — `references/inbox-convention.md` § Inbox Model back-compat) and, if any, show one line before the resumable list:
    ```
    Captures waiting: N — say "check captures" to triage them
    ```
    Omit the line entirely when the count is zero; reading/dispositioning them stays on request (promote → `work` at `refining`, or discard/absorb/feed — `references/inbox-convention.md` § Captures inbound). Then list the slug's `refining` inbox entries (from `_inbox.md`); resume one (`refine <id>`) or scope new (`refine <topic>`). If there are no captures and no `refining` work, ask: "What are we refining? (a short topic)".
  - **Work repo** → **list your *Gathering Requirements* stories inline** so no key need be memorized. Run this JQL (assignee OR reporter = me — verified status string `Gathering Requirements`, id 581):
    ```
    project = <PROJECT> AND status = "Gathering Requirements" AND (assignee = currentUser() OR reporter = currentUser()) ORDER BY updated DESC
    ```
    (`<PROJECT>` resolved-or-confirmed per the zone rule — default `defaults.jiraProject`, never hardcoded `BPT2`.) Present:
    ```
    Gathering Requirements (yours, resumable):
      1  BPT2-6541 — <summary>   — updated MM-DD
    Reopen one (refine <n> / refine BPT2-XXXX), or scope new: refine <new topic>
    ```
    `refine <n>` / `refine BPT2-XXXX` resumes that story (the Jira-key resume path above — status printed first, guard applied). If the list is empty, ask the topic directly, then scope new.

**Status-tiered edit guard (work repo — warn, never hard-block; acp-ajudd#55).** When resuming a Jira story, the status you just printed does double duty as index **and** guard — status is the only state consulted; there is no new field and no hook. Gate the *edit*, keyed on the story's current status (strings verified against the BPT2 workflow — `story/skills/story/SKILL.md`):
- ***Gathering Requirements*** (the refine zone) → edit freely, **no warning**.
- ***Ready For Work*** → editing is allowed, but **warn once** before the first edit: `BPT2-XXXX is Ready For Work — it's graduated and someone may be about to pick it up. Keep editing requirements? (yes / leave it)`. On `yes`, proceed for the rest of the session (warn only once).
- ***In Progress* or beyond** (In Progress, Ready for Code Review, Ready For Test, QA In-Progress, Ready for UAT, Failed Testing, Blocked, Done, Cancelled, Released) → **do not silently edit.** This is the existing "locked mid-build" rule from `/story:update`: warn and require an **explicit flip back to *Gathering Requirements*** first — `BPT2-XXXX is <status> — changing requirements now alters an in-flight/closed story. Transition it back to Gathering Requirements to refine? (yes, flip it back / cancel)`. On `yes`, `transitionJiraIssue` → *Gathering Requirements* (id 581), then edit. On `cancel`, make no change. This is a **confirm prompt, not an enforced gate** (acp-ajudd#1) — no hook.

> **Migrating away from the old model:** older versions wrote a local `refinement-<topic>.md` session file. That file is gone from this flow. Any leftover `refinement-*.md` on disk is harmless legacy — it is still hidden from the default listing and skipped by `session:migrate`; delete it whenever convenient. Nothing new is written there.

### 2. Load Project Memories

Run the equivalent of `/memory:scan` for the repo and surface matching project memories. Offer to load any relevant to the topic. Read-only context — the whole point is to scope using what the team already knows.

### 3. Gather Requirements and Write the Work Early

Invite the user to paste raw requirements, a bug report, notes, or questions — as messy as they like. Ask clarifying questions only where they change scope. Ground every answer in the repo (read), the loaded memories, and git history.

**After the first substantive pass** (enough to name the work and sketch its shape), **create the work immediately** in its "still scoping" state — do not wait for it to be perfect. This is the write-early principle: the work is the WIP store, so the WIP goes into it, where it survives `/clear` and is resumable. (On a **resume**, the work already exists — skip creation and edit it in place.)

**Free rein, but never silent (acp-ajudd#5).** Writing the work is not gated by any propose→approve step — a `work` entry / Jira story is captured requirements, not code, so you write it the way you'd write a session file: without asking. The one rule that survives is *visibility* — the instant you write it, **say so in the conversation** with a plain confirmation line so the user can read and validate the work after the fact:
```
Wrote inbox item <id> (refining) — <one-line summary>          ← plugin / personal
Created <KEY> in Gathering Requirements — <one-line summary>   ← work repo (Jira)
```

**A. Plugin / personal → a `work` entry at `status: refining`.**

Issue a stable ID (`python3 <session>/scripts/inbox-id.py next --slug <slug> --handle <handle>` — on a box without `python3`, use `python`), then append a self-contained `work` entry to `~/.claude/memory/sessions/<slug>/_inbox.md` (create with header `# Inbox — <slug>` if needed). Use the **exact `_inbox.md` header format** the `/session:inbox` write uses, plus the `> [type: work · status: refining]` line and a freeform body carrying the refinement report. The provenance surrogate is the command itself (there is no originating session): `from <slug> / refine (<zone>)`, with `<zone>` as the `source-type`:

```markdown
## <id> · [YYYY-MM-DD @<handle>] from <slug> / refine (<zone>) — <Summary>
> [type: work · status: refining]

**Affected areas:** <from report>
**Estimate:** <from report, with reasoning>
**Risks / challenges:** <from report>
**Open questions / dependencies:** <from report>

### Acceptance criteria
- [ ] <from report>
```

**B. Work repo → Jira story in *Gathering Requirements*.**

Resolve the Jira project first — do **not** assume `BPT2`: default from `~/.claude/plugins/user-config.json` → `defaults.jiraProject` (plus any repo-level hint), then confirm `Create in project <PROJECT>? (yes / different <KEY>)`. Then invoke `/story:create` with the confirmed project, baking the refinement report into the story (Summary → story summary; Affected areas, Risks, Estimate, Dependencies, Acceptance Criteria → description via `editJiraIssue` per the Atlassian markdown quirk). **Create it in a pre-implementation refinement status** — `Gathering Requirements` (the Jira analog of `refining`) — not `Ready For Work` yet. Do not create a story *session* — refining is not work being done.

**C. General → nothing is created.**

A general repo has no system of record, so refine writes **nothing** here — no `work` entry, no Jira story, no prompt asking which. Scope the work in the conversation and, if it needs to go somewhere, hand it off with a `/session:inbox` capture to a repo that does have a system of record. State this plainly rather than offering a target choice:
```
This is a general repo — no system of record, so refine won't create anything here.
Scope it in the conversation; to hand it off, drop a /session:inbox capture to a target repo.
```

### 4. Iterate In Place

As the conversation continues, **keep editing the same work** — this is the WIP store doing its job:
- **`work` entry** → edit its body in `_inbox.md` (Affected areas, Estimate, Risks, Open questions, Acceptance criteria). Leave `type: work · status: refining` until graduation.
- **Jira story** → `editJiraIssue` to update the description; leave it in *Gathering Requirements*.

Update freely and as often as the refinement needs — no per-edit approval, no one-entry cap (a single refine session may create/update several `work` entries). After each substantive edit, surface it plainly (`Updated <id> — <what changed>`) so the work write is never silent.

Aim the report at: **Summary** (one line of what it delivers), **Affected areas** (concrete services/files/tables/endpoints/commands, named from the actual repo), **Estimate** (t-shirt or points *with reasoning*), **Risks / challenges** (the "looks small but isn't" flags), **Open questions / dependencies**, **Draft acceptance criteria** (checkable bullets).

You can stop any time — the work holds everything. Resume later via `refine <id>` / `refine <KEY>` (Step 1 resume path) and keep polishing.

### 5. Graduate — Mark It Ready

Graduation is a **status flip on the work you already created**, not a new artifact. When the report is solid, offer it:

```
Mark ready for pickup?  ready  ·  not yet
```

On `ready`:
- **`work` entry** → change its metadata line to `> [type: work · status: ready]`. Nothing else moves — it's already a normal, pickable `work` entry. Surface it: `Marked <id> ready for pickup.`
- **Jira story** → `transitionJiraIssue` to **Ready For Work** (add a short comment noting refinement is complete, per the story plugin's transition convention). Surface it: `Transitioned <KEY> → Ready For Work.`

On `not yet` → leave it `refining` / *Gathering Requirements*; it stays resumable.

**Refine never marks work complete (acp-ajudd#42).** Refine is a planning/sessionless flow: its highest disposition is **`ready`** (inbox) / **Ready For Work** (Jira) — *scoped, ready to build*, not built. It may create, update, promote, leave-refining, backlog, or discard a `work` entry freely, but it **never** writes a completion stamp (`[DONE]` / "shipped" / *Done*) — that authority belongs only to a coding session's `/session:finish`. If a refine read decides a capture should not be built as-is, that is a **planning disposition** (§ Disposition & completion in `references/inbox-convention.md`): drop it with a `[DISPOSITIONED … — <fate>]` archive or backlog it — never `[DONE]`.

**HARD RULE — refine ends at "ready" and STOPS; it never offers to `code` (acp-ajudd#56).** Graduation is refine's terminus. Once the work is `ready` / *Ready For Work*, **confirm that and stop** — do **not** present, suggest, or offer "pick it up now?" / "open a coding session?" / "start coding this?" / any graduation-as-next-step prompt. This holds in **every** zone and is **most** important in a work repo, where the refiner (e.g. Heber) is typically **not** the developer: the refiner's deliverable is the scoped work/handoff, full stop. Crossing into a coding session is always a **separate, deliberate `code` gesture by whoever builds it** — reachable only by explicitly invoking `code`, never surfaced here. In-place graduation stays *possible* in the model (acp-ajudd#1: unpoliced), but it is **invisible and unoffered** from the refine UX.

So a refine terminus reads, in full:

```
Marked <id> ready for pickup.        ← plugin / personal
Transitioned <KEY> → Ready For Work. ← work repo (Jira)
```

and nothing more about coding. If the user *themselves* says "and let's build it now," that is their own `code` gesture — hand off / point them at `code <work>`; refine still does not create the session file.

(There is no `role` logic in refine — the terminus reads the same way to everyone. Security is the repo zone plus source-control write access, never a config-field role.)

### 6. Done

There is nothing local to clean up — refine left no session file. The work (a `work` entry or Jira story) carries all the scoping context forward to whoever implements it. Come back to a still-`refining` work any time via `refine <id>` / `refine <KEY>`, or spin additional `work` entries from the same exploration.
