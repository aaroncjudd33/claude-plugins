---
name: refine
description: Ephemeral analyze-then-record session — explore the repo and project memories, turn raw requirements or a bug into a well-scoped work record. Graduates zone-aware (work repo → BPT2 Jira story; plugin/personal → inbox item). Local-only, never committed, auto-expires.
argument-hint: "[topic or story area]"
---

# Session Refine

A throwaway **refinement** session for scoping work before any code is written. Paste in rough requirements or a bug, ask questions, and have Claude ground the answers in the actual repo and its project memories — producing a structured refinement report that **graduates to a well-scoped work record**. Read-only by design; nothing it touches is ever committed.

Refine is a **universal analyze-then-record flow**. What the record *is* depends on the repo's system of record (the zone), not on who runs it:

- **Work repo (story/cab)** → a **BPT2 Jira story** (record of truth = the Jira story).
- **Plugin / personal** (item-driven) → an **inbox item** in `_inbox.md` (record of truth = the inbox item → git history).

In plugin/personal, refine is the **investigated, heavyweight sibling of `new <description>`**: `new` = quick capture then pick; `refine` = analyze the code first, then write a well-scoped item (and, if you're the dev sitting right there, optionally `pick` it straight into a coding session). Keep the two distinct — refine is not a slower `new`.

Use it for upfront scoping — whether you're writing requirements (Heber's "refinement") or a developer sizing work before picking it up. It is the **investigated front end** to whatever record your repo uses.

## Key properties

- **Read-only:** runs in `Mode: planning` — no code edits. If asked to implement, route the work to a session inbox / story instead.
- **Ephemeral:** the session file lives only at `~/.claude/memory/sessions/<slug>/refinement-<topic>.md`. It is **never** migrated to the repo (`session:migrate` skips `refinement-*.md`) and **hidden** from the default `session:start` listing (surfaced under the `refine` entry point, or via the `refinement`/`all` filter).
- **Retained, then auto-expires:** kept locally so you can revisit recent thinking; refine sessions untouched for **30 days** are purged automatically at the start of Step 0.
- **Does not become a build session.** Its job ends when the work record is created. The analysis rides into the record itself (the Jira story, or the inbox item body), so whoever builds it gets the context fresh.

> **`_active` note (dependency, not a bug to fix here):** Step 2 repoints `_active` to this refinement (planning) session so checkpoint/resume work normally. In always-on zones (plugin/personal) that means code edits stay blocked while the refine session is active — which is correct, since refine is read-only. Cleanly restoring `_active` after a refine detour is owned by the pending **`_active` redesign** (append-to-an-active-list model, so a coding session stays active alongside a planning one) — do **not** build a bespoke restore-on-exit hack here; the redesign would delete it. Until it lands: graduating via **pick** (plugin/personal) moves `_active` forward to the new coding session; otherwise the next `/session:start` / `/session:switch` repoints it.

## Instructions

### 0. Sweep expired refine sessions

Run `pwd`, extract the repo slug. Purge stale refine sessions for this slug (untouched > 30 days):

```bash
find ~/.claude/memory/sessions/<slug>/ -maxdepth 1 -name 'refinement-*.md' -mtime +30 -print -delete 2>/dev/null
```

If any were purged, note it briefly ("Cleaned N expired refine session(s)").

### 1. Resolve, Name, and Detect Zone

Refine sessions are **always local** — `session_root = ~/.claude/memory/sessions/<slug>/` regardless of whether the repo has been migrated (they never go in the repo). Read `handle` per the Session Skill's handle lookup.

Derive a short kebab name from the argument (e.g. `refinement-shopify-refund-window`). If no argument, ask: "What are we refining? (a short topic)".

**Detect the zone** — this decides the graduation target in Step 6. Read `~/.claude/plugins/user-config.json` → `paths` and classify the current repo (pwd), using the same logic as `session:start`:

| Zone | Detection | Graduates to |
|------|-----------|--------------|
| **plugin** | pwd contains `pluginMarketplaceName` | inbox item in `_inbox.md` (unambiguous — no target confirmation) |
| **personal** | pwd begins with `personalProjectsDir` (fallback: contains `/c/claude/`) | inbox item in `_inbox.md` (unambiguous — no target confirmation) |
| **work repo (story/cab)** | pwd begins with `workReposDir` (fallback: contains `/dev/`) | Jira story — **project resolved-or-confirmed, never hardcoded** |
| **general** | anything else | **no assumed system of record** — confirm the target at Step 6 (Jira story w/ project, or inbox item) |

Record the detected zone; Step 6 dispatches on it. **Do not warn or block** when refine is invoked outside a work repo — refine is welcome everywhere; it just graduates to the right kind of record.

**Never hardcode the graduation target.** Only plugin/personal are unambiguous (always an inbox item). For work repos the Jira **project** is not assumed to be `BPT2` — a repo may map to a different project; resolve it from context or confirm before creating. For general repos there is no assumed record at all. **When in doubt, ask — don't default.**

### 2. Create the Refine Session File

Write `<session_root>/refinement-<topic>.md`:

```
---
updated: [today]
---

# Session State — refinement-<topic>

- **Type:** refinement
- **Mode:** planning
- **Name:** refinement-<topic>
- **updated-by:** @<handle>
- **created-by:** @<handle>
- **Zone:** [plugin / personal / work-repo / general]
- **Scope:** ./
- **Status:** in-progress
- **Branch:** [current branch or "n/a"]
- **Refinement report:**
  - Summary:
  - Affected areas:
  - Estimate:
  - Risks / challenges:
  - Open questions / dependencies:
  - Draft acceptance criteria:
- **Record:** none   ← set once graduated: `BPT2-XXXX` (work repo) or `inbox item @ _inbox.md (<slug>)` (plugin/personal)
- **Last worked on:** [today @<handle>] refine kickoff
```

Write `~/.claude/memory/sessions/<slug>/_active` with `refinement-<topic>` so checkpoint/resume work normally (see the `_active` note above for why this is safe and how it unwinds).

### 3. Load Project Memories

Run the equivalent of `/memory:scan` for the repo and surface matching project memories. Offer to load any that look relevant to the topic. This is read-only context — the whole point is to scope using what the team already knows.

### 4. Gather Requirements

Invite the user to paste raw requirements, a bug report, notes, or questions — as messy as they like. Ask clarifying questions only where it changes the scope. Use the repo (read), the loaded memories, and git history to ground every answer.

### 5. Build the Refinement Report

As the conversation progresses, keep the **Refinement report** fields in the session file current. Aim for:

- **Summary** — one line of what the work delivers.
- **Affected areas** — concrete services/files/tables/endpoints/commands it touches, named from the actual repo.
- **Estimate** — t-shirt (S/M/L/XL) or points, **with the reasoning** (what makes it that size).
- **Risks / challenges** — the "looks small but isn't" flags; coupling, migrations, unknowns.
- **Open questions / dependencies** — what must be answered or unblocked first.
- **Draft acceptance criteria** — checkable bullets.

Update the report on each `session:checkpoint` like any other session.

### 6. Graduate — Create the Work Record (zone-aware)

When the report is solid, create the record. The zone (Step 1) decides the output; the user does not pick between commands. But **the target is never hardcoded** — only plugin/personal are unambiguous. For work repos, resolve-or-confirm the Jira project; for general, confirm the record type first. **When in doubt, ask — don't default.** Tailor only *how the offer is surfaced* by `role` (see **Role display** below); the create itself is the same dispatch.

**A. Plugin / personal zone → inbox item in `_inbox.md` (unambiguous — no target confirmation needed).**

Offer: **"Write the inbox item now? (yes / not yet)"**

On yes, append a self-contained item to `~/.claude/memory/sessions/<slug>/_inbox.md` (create with header `# Inbox — <slug>` if needed). **Use the exact same `_inbox.md` item format that `new` and `/session:inbox` write** — refine is the analyzed sibling of `new`, so its item must land as a normal, pickable inbox item (identical header + freeform body); the two commands stay separate but produce the same artifact. The consolidated inbox is the record of truth (git history is the trail):

```markdown
## [YYYY-MM-DD @<handle>] from <slug> / refinement-<topic> (refinement) — <Summary>

**Affected areas:** <from report>
**Estimate:** <from report, with reasoning>
**Risks / challenges:** <from report>
**Open questions / dependencies:** <from report>

### Acceptance criteria
- [ ] <from report>
```

Record `- **Record:** inbox item @ _inbox.md (<slug>)` and update `Last worked on`. Then continue to **Offer to pick it up** below.

**B. Work-repo zone (story/cab) → Jira story, project resolved-or-confirmed (never hardcoded).**

Offer: **"Create the story now? (yes / not yet)"**

On yes, **resolve the Jira project first** — do not assume `BPT2`:
- Default from context: `~/.claude/plugins/user-config.json` → `defaults.jiraProject` (and any repo-level project hint if present).
- **Confirm before creating:** `Create in project <PROJECT>? (yes / different <KEY>)`. Apply an override if given.

Then invoke `/story:create` with the confirmed project and **bake the refinement report into the story** — the report's Summary becomes the story summary; Affected areas, Risks, Estimate, Dependencies, and Acceptance Criteria go into the description (use `editJiraIssue` for markdown formatting per the Atlassian quirks). Record the resulting key in `- **Record:** <PROJECT>-XXXX` and the `Last worked on` line.

Do **not** create a story session here. Whoever builds it runs `/session:start` later and picks up the context from Jira. If a handoff note is useful, write a `[scoping]` entry to that story's inbox via `/session:inbox`.

**C. General zone → no assumed system of record; confirm the target.**

A general repo may have no Jira at all. Do not default. Ask:

```
This project has no known system of record. How should this graduate?
  jira <PROJECT>   — create a Jira story in <PROJECT>
  inbox            — write a local inbox item for this repo's slug
```

- **jira <PROJECT>** → confirm the project as in B, then create the story (baking the report in). Record `Record: <PROJECT>-XXXX`.
- **inbox** → write the item to `~/.claude/memory/sessions/<slug>/_inbox.md` exactly as in A (same `new`/`/session:inbox` format). Record `Record: inbox item @ _inbox.md (<slug>)`, then continue to **Offer to pick it up**.

**Offer to pick it up** (only after an **inbox-item** graduation — A, or C→inbox). One optional line, never auto (the dev-sitting-there path):

```
Pick it into a coding session now?  pick  ·  leave
```

- **pick** → run the `pick` flow (`start-impl.md` → Item Pickup): derive a feature name (confirm once), fold the item into a new **coding** session, delete it from `_inbox.md`, and set `_active` to the new session. This is also what advances `_active` off the planning refine session (see the `_active` note).
- **leave** → the item stays pending; a later `/session:start` picks it up like any other inbox item.

The base flow **ends at "record created."** Spinning up the build session is this single optional offer — not auto-triggered, and never role-gated.

**Role display (UX only — never gates).** Read `role` from `~/.claude/plugins/user-config.json` → `user.role` if present. It only tailors how the graduation offer and its continuation are *surfaced* — every option stays reachable regardless of role:

- `qa-requirements` → lead with the record-created / done framing; show the "pick into a coding session" continuation as a small secondary note (this user typically hands off to a builder).
- `dev` → surface the "pick it up now / continue into a build session" continuation prominently, right alongside record-created.
- **absent / any other value → show the full menu** (record + continuation equally), no tailoring.

Never block, hide, or refuse a capability based on `role`. Role only reorders/emphasizes what's shown. Anyone can set it (it's a plain config field), so it must never be treated as a boundary — the real boundary is repo write access + source control.

### 7. Done

The refine session stays local and hidden. You can come back to it (`/session:start` → `refine` to list them, or resume by name), spin additional records from the same exploration, or just let it auto-expire in 30 days. It is never committed and never shared.
