---
name: refine
description: Analyze-then-record scoping flow — explore the repo and project memories, turn raw requirements or a bug into a well-scoped work record written directly into the record itself (inbox item or Jira story). Graduates zone-aware. Creates no session file.
argument-hint: "[topic, story area, or existing record to resume]"
---

# Session Refine

An **analyze-then-record** flow for scoping work before any code is written. Paste in rough requirements or a bug, ask questions, and have Claude ground the answers in the actual repo and its project memories — writing a well-scoped work record that an implementation session later picks up.

Refine is universal. What the record *is* is decided **strictly by the repo's zone** — never by who runs it, and with no override or target picker:

- **Plugin / personal** (item-driven) → an **inbox item** in `_inbox.md`.
- **Work repo (story/cab)** → a **Jira story** (project resolved-or-confirmed, never hardcoded).
- **General** → **no system of record — refine creates no record.** A general repo has nothing to graduate into; the only thing that can leave a refine here is a `/session:inbox` mailbox note (a separate axis — see below). Scope verbally, hand off via a note if needed.

## The model: the record IS the work-in-progress store

Refinement does **not** get its own session file — in any zone. The realization: **the record you're producing is itself where the work-in-progress lives, and it is also the final deliverable.** You create the record early, iterate on it across as many sittings as you need, and when it's matured you mark it **ready** — the single trigger that says "an implementation session can pick this up." A session file is only ever created for *work being done* (a coding session), never for scoping the record.

This is exactly Heber's Jira flow — rough story → iterate → *Ready For Work* — and it is identical in a plugin/personal repo, where **the inbox item is what Jira is**:

| Zone | The record (= WIP store = deliverable) | "still scoping" state | graduation trigger |
|------|----------------------------------------|-----------------------|--------------------|
| plugin / personal | inbox item in `_inbox.md` | `status: refining` | flip to `status: ready` |
| work repo | Jira story | *Gathering Requirements* | transition to *Ready For Work* |
| general | none — no record is created | n/a | n/a (verbal scope; hand off via a `/session:inbox` note) |

Both the **write-early** path ("scope some, come back later, keep polishing") and the **one-shot** path ("scope it and mark ready in one sitting") are the same flow — the only difference is how mature the record is when you stop. Create-at-graduation is just the degenerate case where you finish in one sitting.

## Key properties

- **Read-only toward code.** Refine scopes; it does not implement. Writing/editing the *record* (an inbox item under `~/.claude/memory/`, or a Jira story) is not a code edit — refine writes the record freely. If asked to implement, graduate the record and pick it up as a coding session. (Nothing hard-blocks a code edit either — acp-ajudd#1 removed edit-blocking — but refine's *job* is to scope, not build; keep it that way by convention.)
- **Refine owns in-place requirement edits (acp-ajudd#13).** Editing a record's body / requirements / acceptance criteria in place is refine's job — that is exactly what the write-early + iterate loop below does. The mirror boundary: a **coding session must NOT** rewrite the requirements of an existing inbox item or Jira story it (or anyone) picked up. When a coding session finds a requirement needs changing, it hands off — a `/session:inbox` note, or back to a refine pass — rather than editing the record inline. So requirement changes always flow through refine.
- **Record vs. mailbox are separate axes.** Refine's *record* target is locked by zone (above). The **mailbox** (`type: note` / `type: data` via `/session:inbox`) is independent and available from any context. In a work repo, refine's record is the Jira story, so the only thing refine ever puts in an inbox is a mailbox note — never a `type: story` record. In plugin/personal the inbox `type: story` item **is** the record (not a mailbox message) — correct, not a violation. Never touch the mailbox axis when locking the record target.
- **No session file, no `_active` change.** Refine creates nothing under `<session_root>` and never touches `_active`. A coding session already active stays active *alongside* a refine, unaffected. (This is what decoupled refine from the `_active` redesign.)
- **Nothing to expire or migrate.** With no session file there is no `refinement-*.md` to sweep, hide, or exclude from `session:migrate`. The record's own history (git for inbox items, Jira for stories) is the trail.
- **Resumable through the record itself.** A `refining` inbox item shows up in `/session:start`'s inbox listing as resumable (marked `refining`); a work-repo story in *Gathering Requirements* is a first-class Jira object you reopen with `refine BPT2-XXXX` (or find via `/story:dashboard`).

## Instructions

### 1. Resolve, Detect Zone, and Decide New-vs-Resume

Run `pwd`, extract the repo slug. Read `handle` per the Session Skill's handle lookup. **Detect the zone** — this decides the record type in Steps 2–4. Read `~/.claude/plugins/user-config.json` → `paths` and classify the current repo (pwd), same logic as `session:start`:

| Zone | Detection | Record |
|------|-----------|--------|
| **plugin** | pwd contains `pluginMarketplaceName` | inbox item in `_inbox.md` (unambiguous — no target confirmation) |
| **personal** | pwd begins with `personalProjectsDir` (fallback: contains `/c/claude/`) | inbox item in `_inbox.md` (unambiguous — no target confirmation) |
| **work repo (story/cab)** | pwd begins with `workReposDir` (fallback: contains `/dev/`) | Jira story — project resolved-or-confirmed, **never hardcoded** |
| **general** | anything else | **no system of record — no record is created** (scope verbally; hand off via a `/session:inbox` note if needed) |

**Do not warn or block** when refine runs outside a work repo — refine is welcome everywhere; it just graduates to the right kind of record for the zone. **The target is strictly the zone — there is no override and no target picker.** For work repos the Jira **project** is not assumed to be `BPT2` — resolve from context or confirm the project (that is the only thing ever confirmed; the *kind* of record is fixed by zone). For general, no record is created at all.

**New vs resume** (from the argument):
- **An existing record reference** — a `refining` inbox item's `<id>` (e.g. `refine acp-ajudd#12`) or a Jira key (`refine BPT2-6429`) → **resume**: read that record (inbox item body, or `getJiraIssue`) and continue refining it in place from Step 3. Skip Step 2 (the record already exists).
- **A topic / free text** (`refine shopify refund window`) or **nothing** → **new**: proceed to Step 2. If no argument, ask: "What are we refining? (a short topic)".

> **Migrating away from the old model:** older versions wrote a local `refinement-<topic>.md` session file. That file is gone from this flow. Any leftover `refinement-*.md` on disk is harmless legacy — it is still hidden from the default listing and skipped by `session:migrate`; delete it whenever convenient. Nothing new is written there.

### 2. Load Project Memories

Run the equivalent of `/memory:scan` for the repo and surface matching project memories. Offer to load any relevant to the topic. Read-only context — the whole point is to scope using what the team already knows.

### 3. Gather Requirements and Write the Record Early

Invite the user to paste raw requirements, a bug report, notes, or questions — as messy as they like. Ask clarifying questions only where they change scope. Ground every answer in the repo (read), the loaded memories, and git history.

**After the first substantive pass** (enough to name the work and sketch its shape), **create the record immediately** in its "still scoping" state — do not wait for it to be perfect. This is the write-early principle: the record is the WIP store, so the WIP goes into it, where it survives `/clear` and is resumable. (On a **resume**, the record already exists — skip creation and edit it in place.)

**Free rein, but never silent (acp-ajudd#5).** Writing the record is not gated by any propose→approve step — an inbox item / Jira story is captured requirements, not code, so you write it the way you'd write a session file: without asking. The one rule that survives is *visibility* — the instant you write it, **say so in the conversation** with a plain confirmation line so the user can read and validate the record after the fact:
```
Wrote inbox item <id> (refining) — <one-line summary>          ← plugin / personal
Created <KEY> in Gathering Requirements — <one-line summary>   ← work repo (Jira)
```

**A. Plugin / personal → inbox item at `status: refining`.**

Issue a stable ID (`python3 <session>/scripts/inbox-id.py next --slug <slug> --handle <handle>`), then append a self-contained item to `~/.claude/memory/sessions/<slug>/_inbox.md` (create with header `# Inbox — <slug>` if needed). Use the **exact `_inbox.md` format `new` / `/session:inbox` write** — same header, plus the `> [type: story · status: refining]` line and a freeform body carrying the refinement report. The provenance surrogate is the command itself (there is no originating session): `from <slug> / refine (<zone>)`, with `<zone>` as the `source-type`:

```markdown
## <id> · [YYYY-MM-DD @<handle>] from <slug> / refine (<zone>) — <Summary>
> [type: story · status: refining]

**Affected areas:** <from report>
**Estimate:** <from report, with reasoning>
**Risks / challenges:** <from report>
**Open questions / dependencies:** <from report>

### Acceptance criteria
- [ ] <from report>
```

**B. Work repo → Jira story in *Gathering Requirements*.**

Resolve the Jira project first — do **not** assume `BPT2`: default from `~/.claude/plugins/user-config.json` → `defaults.jiraProject` (plus any repo-level hint), then confirm `Create in project <PROJECT>? (yes / different <KEY>)`. Then invoke `/story:create` with the confirmed project, baking the refinement report into the story (Summary → story summary; Affected areas, Risks, Estimate, Dependencies, Acceptance Criteria → description via `editJiraIssue` per the Atlassian markdown quirk). **Create it in a pre-implementation refinement status** — `Gathering Requirements` (the Jira analog of `refining`) — not `Ready For Work` yet. Do not create a story *session* — refining is not work being done.

**C. General → no record is created.**

A general repo has no system of record, so refine writes **nothing** here — no inbox item, no Jira story, no prompt asking which. Scope the work in the conversation and, if it needs to go somewhere, hand it off with a `/session:inbox` mailbox note to a repo that does have a record. State this plainly rather than offering a target choice:
```
This is a general repo — no system of record, so refine won't create a record here.
Scope it in the conversation; to hand it off, drop a /session:inbox note to a target repo.
```

### 4. Iterate In Place

As the conversation continues, **keep editing the same record** — this is the WIP store doing its job:
- **Inbox item** → edit the item body in `_inbox.md` (Affected areas, Estimate, Risks, Open questions, Acceptance criteria). Leave `status: refining` until graduation.
- **Jira story** → `editJiraIssue` to update the description; leave it in *Gathering Requirements*.

Update freely and as often as the refinement needs — no per-edit approval, no one-record cap (a single refine session may create/update several records). After each substantive edit, surface it plainly (`Updated <id> — <what changed>`) so the record write is never silent.

Aim the report at: **Summary** (one line of what it delivers), **Affected areas** (concrete services/files/tables/endpoints/commands, named from the actual repo), **Estimate** (t-shirt or points *with reasoning*), **Risks / challenges** (the "looks small but isn't" flags), **Open questions / dependencies**, **Draft acceptance criteria** (checkable bullets).

You can stop any time — the record holds everything. Resume later via `refine <id>` / `refine <KEY>` (Step 1 resume path) and keep polishing.

### 5. Graduate — Mark It Ready

Graduation is a **status flip on the record you already created**, not a new artifact. When the report is solid, offer it:

```
Mark ready for pickup?  ready  ·  not yet
```

On `ready`:
- **Inbox item** → change the item's line to `> [type: story · status: ready]`. Nothing else moves — it's already a normal, pickable inbox item. Surface it: `Marked <id> ready for pickup.`
- **Jira story** → `transitionJiraIssue` to **Ready For Work** (add a short comment noting refinement is complete, per the story plugin's transition convention). Surface it: `Transitioned <KEY> → Ready For Work.`

On `not yet` → leave it `refining` / *Gathering Requirements*; it stays resumable.

**Offer to pick it up** (inbox-item graduations only — plugin / personal). One optional line, never auto — the dev-sitting-there path:

```
Pick it into a coding session now?  pick  ·  leave
```

- **pick** → run the `pick` flow (`start-impl.md` → Item Pickup): derive a feature name (confirm once), fold the item into a new **coding** session, delete it from `_inbox.md`, set `_active` to the new session. This is the point a session file is finally created — because now it's work being done.
- **leave** → the item stays `ready` and pending; a later `/session:start` picks it up like any other.

For **work-repo (Jira) graduations**, do not create a story session here — whoever builds it runs `/session:start BPT2-XXXX` later and picks up context from Jira. A `[scoping]` handoff note via `/session:inbox` is optional.

(There is no `role` logic in refine — the graduation offer is shown the same way to everyone. Security is the repo zone plus source-control write access, never a config-field role.)

### 6. Done

There is nothing local to clean up — refine left no session file. The record (inbox item or Jira story) carries all the scoping context forward to whoever implements it. Come back to a still-`refining` record any time via `refine <id>` / `refine <KEY>`, or spin additional records from the same exploration.
