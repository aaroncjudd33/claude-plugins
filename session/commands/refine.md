---
name: refine
description: Analyze-then-record scoping flow — explore the repo and project memories, turn raw requirements or a bug into a well-scoped work record written directly into the record itself (inbox item or Jira story). Graduates zone-aware. Creates no session file.
argument-hint: "[topic, story area, or existing record to resume]"
---

# Session Refine

An **analyze-then-record** flow for scoping work before any code is written. Paste in rough requirements or a bug, ask questions, and have Claude ground the answers in the actual repo and its project memories — writing a well-scoped work record that an implementation session later picks up.

Refine is universal. What the record *is* depends on the repo's system of record (the zone), not on who runs it:

- **Plugin / personal** (item-driven) → an **inbox item** in `_inbox.md`.
- **Work repo (story/cab)** → a **Jira story** (project resolved-or-confirmed, never hardcoded).
- **General** → confirm the target first (Jira story w/ project, or inbox item) — no assumed system of record.

## The model: the record IS the work-in-progress store

Refinement does **not** get its own session file — in any zone. The realization: **the record you're producing is itself where the work-in-progress lives, and it is also the final deliverable.** You create the record early, iterate on it across as many sittings as you need, and when it's matured you mark it **ready** — the single trigger that says "an implementation session can pick this up." A session file is only ever created for *work being done* (a coding session), never for scoping the record.

This is exactly Heber's Jira flow — rough story → iterate → *Ready For Work* — and it is identical in a plugin/personal repo, where **the inbox item is what Jira is**:

| Zone | The record (= WIP store = deliverable) | "still scoping" state | graduation trigger |
|------|----------------------------------------|-----------------------|--------------------|
| plugin / personal | inbox item in `_inbox.md` | `status: refining` | flip to `status: ready` |
| work repo | Jira story | *Gathering Requirements* | transition to *Ready For Work* |
| general | (confirmed at Step 1) | as above, per chosen target | as above |

Both the **write-early** path ("scope some, come back later, keep polishing") and the **one-shot** path ("scope it and mark ready in one sitting") are the same flow — the only difference is how mature the record is when you stop. Create-at-graduation is just the degenerate case where you finish in one sitting.

## Key properties

- **Read-only toward code.** Refine scopes; it does not implement. Writing/editing the *record* (an inbox item under `~/.claude/memory/`, or a Jira story) is not a code edit and is always allowed — the scope-guard hook never gates those paths. If asked to implement, graduate the record and pick it up as a coding session.
- **No session file, no `_active` change.** Refine creates nothing under `<session_root>` and never touches `_active`. A coding session already active stays active *alongside* a refine — refining an item never locks editing. (This is what decoupled refine from the `_active` redesign.)
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
| **general** | anything else | **no assumed system of record** — confirm target at Step 2 |

**Do not warn or block** when refine runs outside a work repo — refine is welcome everywhere; it just graduates to the right kind of record. **Never hardcode the graduation target.** For work repos the Jira **project** is not assumed to be `BPT2` — resolve from context or confirm. For general there is no assumed record at all. When in doubt, ask — don't default.

**New vs resume** (from the argument):
- **An existing record reference** — a `refining` inbox item's `<id>` (e.g. `refine acp-ajudd#12`) or a Jira key (`refine BPT2-6429`) → **resume**: read that record (inbox item body, or `getJiraIssue`) and continue refining it in place from Step 3. Skip Step 2 (the record already exists).
- **A topic / free text** (`refine shopify refund window`) or **nothing** → **new**: proceed to Step 2. If no argument, ask: "What are we refining? (a short topic)".

> **Migrating away from the old model:** older versions wrote a local `refinement-<topic>.md` session file. That file is gone from this flow. Any leftover `refinement-*.md` on disk is harmless legacy — it is still hidden from the default listing and skipped by `session:migrate`; delete it whenever convenient. Nothing new is written there.

### 2. Load Project Memories

Run the equivalent of `/memory:scan` for the repo and surface matching project memories. Offer to load any relevant to the topic. Read-only context — the whole point is to scope using what the team already knows.

### 3. Gather Requirements and Write the Record Early

Invite the user to paste raw requirements, a bug report, notes, or questions — as messy as they like. Ask clarifying questions only where they change scope. Ground every answer in the repo (read), the loaded memories, and git history.

**After the first substantive pass** (enough to name the work and sketch its shape), **create the record immediately** in its "still scoping" state — do not wait for it to be perfect. This is the write-early principle: the record is the WIP store, so the WIP goes into it, where it survives `/clear` and is resumable. (On a **resume**, the record already exists — skip creation and edit it in place.)

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

**C. General → confirm the target, then A or B.**

```
This project has no known system of record. How should this graduate?
  jira <PROJECT>   — create a Jira story in <PROJECT>
  inbox            — write a local inbox item for this repo's slug
```
`jira <PROJECT>` → confirm project as in B, create the story in *Gathering Requirements*. `inbox` → write the item exactly as in A.

### 4. Iterate In Place

As the conversation continues, **keep editing the same record** — this is the WIP store doing its job:
- **Inbox item** → edit the item body in `_inbox.md` (Affected areas, Estimate, Risks, Open questions, Acceptance criteria). Leave `status: refining` until graduation.
- **Jira story** → `editJiraIssue` to update the description; leave it in *Gathering Requirements*.

Aim the report at: **Summary** (one line of what it delivers), **Affected areas** (concrete services/files/tables/endpoints/commands, named from the actual repo), **Estimate** (t-shirt or points *with reasoning*), **Risks / challenges** (the "looks small but isn't" flags), **Open questions / dependencies**, **Draft acceptance criteria** (checkable bullets).

You can stop any time — the record holds everything. Resume later via `refine <id>` / `refine <KEY>` (Step 1 resume path) and keep polishing.

### 5. Graduate — Mark It Ready

Graduation is a **status flip on the record you already created**, not a new artifact. When the report is solid, offer it:

```
Mark ready for pickup?  ready  ·  not yet
```

On `ready`:
- **Inbox item** → change the item's line to `> [type: story · status: ready]`. Nothing else moves — it's already a normal, pickable inbox item.
- **Jira story** → `transitionJiraIssue` to **Ready For Work** (add a short comment noting refinement is complete, per the story plugin's transition convention).

On `not yet` → leave it `refining` / *Gathering Requirements*; it stays resumable.

**Offer to pick it up** (inbox-item graduations only — plugin/personal, or general→inbox). One optional line, never auto — the dev-sitting-there path:

```
Pick it into a coding session now?  pick  ·  leave
```

- **pick** → run the `pick` flow (`start-impl.md` → Item Pickup): derive a feature name (confirm once), fold the item into a new **coding** session, delete it from `_inbox.md`, set `_active` to the new session. This is the point a session file is finally created — because now it's work being done.
- **leave** → the item stays `ready` and pending; a later `/session:start` picks it up like any other.

For **work-repo (Jira) graduations**, do not create a story session here — whoever builds it runs `/session:start BPT2-XXXX` later and picks up context from Jira. A `[scoping]` handoff note via `/session:inbox` is optional.

**Role display (UX only — never gates).** Read `role` from `~/.claude/plugins/user-config.json` → `user.role` if present; it only tailors how the graduation offer is *surfaced* — every option stays reachable regardless:
- `qa-requirements` → lead with the ready/handoff framing; show "pick into a coding session" as a small secondary note.
- `dev` → surface the "pick it up now" continuation prominently, alongside ready.
- absent / any other → show the full menu equally.

Never block, hide, or refuse a capability based on `role` — it is a plain config field, not a boundary. The real boundary is repo write access + source control.

### 6. Done

There is nothing local to clean up — refine left no session file. The record (inbox item or Jira story) carries all the scoping context forward to whoever implements it. Come back to a still-`refining` record any time via `refine <id>` / `refine <KEY>`, or spin additional records from the same exploration.
