---
name: refine
description: Ephemeral story-refinement session — explore the repo and project memories, turn raw requirements into a well-scoped Jira story with analysis, estimate, and risks. Local-only, never committed, auto-expires.
argument-hint: "[topic or story area]"
---

# Session Refine

A throwaway **refinement** session for shaping a story before any code is written. Paste in rough requirements, ask questions, and have Claude ground the answers in the actual repo and its project memories — producing a structured refinement report that becomes a Jira story. Read-only by design; nothing it touches is ever committed.

Use it for upfront scoping — whether you're writing requirements (Heber's "refinement") or a developer sizing work before picking it up.

## Key properties

- **Read-only:** runs in `Mode: planning` — no code edits. If asked to implement, route the work to a story/session inbox instead.
- **Ephemeral:** the session file lives only at `~/.claude/memory/sessions/<slug>/refinement-<topic>.md`. It is **never** migrated to the repo (`session:migrate` skips `refinement-*.md`) and **hidden** from the default `session:start` listing.
- **Retained, then auto-expires:** kept locally so you can revisit recent thinking; refine sessions untouched for **30 days** are purged automatically at the start of Step 0.
- **Does not become a story session.** Its job ends when the story is written. The analysis rides into the Jira story itself, so whoever builds it gets the context fresh from Jira.

## Instructions

### 0. Sweep expired refine sessions

Run `pwd`, extract the repo slug. Purge stale refine sessions for this slug (untouched > 30 days):

```bash
find ~/.claude/memory/sessions/<slug>/ -maxdepth 1 -name 'refinement-*.md' -mtime +30 -print -delete 2>/dev/null
```

If any were purged, note it briefly ("Cleaned N expired refine session(s)").

### 1. Resolve and Name

Refine sessions are **always local** — `session_root = ~/.claude/memory/sessions/<slug>/` regardless of whether the repo has been migrated (they never go in the repo). Read `handle` per the Session Skill's handle lookup.

Derive a short kebab name from the argument (e.g. `refinement-shopify-refund-window`). If no argument, ask: "What are we refining? (a short topic)".

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
- **Story:** none   ← set to the BPT2 key once the story is created
- **Last worked on:** [today @<handle>] refine kickoff
```

Write `~/.claude/memory/sessions/<slug>/_active` with `refinement-<topic>` so checkpoint/resume work normally.

### 3. Load Project Memories

Run the equivalent of `/memory:scan` for the repo and surface matching project memories. Offer to load any that look relevant to the topic. This is read-only context — the whole point is to scope using what the team already knows.

### 4. Gather Requirements

Invite the user to paste raw requirements, notes, or questions — as messy as they like. Ask clarifying questions only where it changes the scope. Use the repo (read), the loaded memories, and git history to ground every answer.

### 5. Build the Refinement Report

As the conversation progresses, keep the **Refinement report** fields in the session file current. Aim for:

- **Summary** — one line of what the story delivers.
- **Affected areas** — concrete services/files/tables/endpoints it touches, named from the actual repo.
- **Estimate** — t-shirt (S/M/L/XL) or points, **with the reasoning** (what makes it that size).
- **Risks / challenges** — the "looks small but isn't" flags; coupling, migrations, unknowns.
- **Open questions / dependencies** — what must be answered or unblocked first.
- **Draft acceptance criteria** — checkable bullets.

Update the report on each `session:checkpoint` like any other session.

### 6. Graduate to a Story

When the report is solid, offer: **"Create the story now? (yes / not yet)"**

On yes, invoke `/story:create` and **bake the refinement report into the story** — the report's Summary becomes the story summary; Affected areas, Risks, Estimate, Dependencies, and Acceptance Criteria go into the description (use `editJiraIssue` for markdown formatting per the Atlassian quirks). Record the resulting key in the session file's `- **Story:** BPT2-XXXX` field and the `Last worked on` line.

Do **not** create a story session here. Whoever builds it runs `/session:start` later and picks up the context from Jira. If a handoff note is useful, write a `[scoping]` entry to that story's inbox via `/session:inbox`.

### 7. Done

The refine session stays local and hidden. You can come back to it (`/session:start` → type `refinement` to list them, or resume by name), spin additional stories from the same exploration, or just let it auto-expire in 30 days. It is never committed and never shared.
