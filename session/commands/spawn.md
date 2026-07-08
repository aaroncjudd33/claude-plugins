---
name: spawn
description: Stage a new linked session from the current one — writes a [spawn] inbox entry with full context so the next /session:start can pick it up and run with it. Current session is unchanged.
---

# Session Spawn

Prepares a handoff for a new session by writing a `[spawn]` entry to the global `_inbox.md`. Your active session does not change. The spawned entry appears in the global inbox the next time anyone runs `/session:start` on this project — clearly marked and ready to kick off.

**Typical use:** You finish an investigation and want to hand off follow-on scope to a new implementation session — same project, new scope, connected history.

## Instructions

### 1. Identify Current Session

Read current session from conversation context (the most recent `session:start` output — "Resuming `<name>`"). Do NOT read `_active` to *select* the session (context is authoritative for which session is current).

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).

**Session guard (command-level enforcement — acp-ajudd#1).** `spawn` stages a handoff *from* the current session, so a session must exist. If no current session is in the conversation context **and** `~/.claude/memory/sessions/<slug>/_active` does not exist, **stop cleanly** — there is no source session to spawn from:

```
No session established for <slug>. Run /session:start first.
```

(The `_active` check here is existence-only, for the guard — it does not override conversation context when a current session *is* present.) Editing files is never blocked; the session commands are what require a session. (`start` / `refine` and read-only views are exempt.)

### 2. Determine Label and Type

If the user provided a label (e.g. `/session:spawn shopify-fix`), use it. Otherwise ask: "Short label for this spawn? (e.g. shopify-fix, enrollment-investigation)"

Then ask for the session type as a plain routing line — output and wait:

```
Type:  story  ·  plugin  ·  personal  ·  general  ·  cab
```

Parse the reply as the type. Free text also accepted (e.g. "it's a story session").

No Jira story, branch, or CAB needs to exist yet — those are created at pickup time via `/session:start`.

### 3. Collect Handoff Context

Ask for context source as a plain routing line — output and wait:

```
Context:  auto-derive  ·  describe
```

- **auto-derive:** derive a handoff summary from the current conversation — key findings, decisions made, rejected options, open questions, concrete next step. Cap at ~10 bullets.
- **describe:** ask as follow-up: "Describe the context the spawned session should inherit:" — use the user's description as-is.

### 4. Write Spawn Entry to Inbox

Pick the target inbox by zone — a spawn must land where `/session:start` will actually surface it:

- **plugin / personal (item-driven):** always the consolidated `<session_root>/_inbox.md` (create with header `# Inbox — <slug>` if needed). These slugs have exactly ONE inbox; `/session:start` reads it and flags `[spawn]` entries with ★. A per-label `_inbox_<label>.md` would never surface — do NOT write one for these types (there is no per-session inbox in the item-driven model).
- **story / cab / general:** if the `Label` matches an existing session name in `session_root`, append to that session's `<session_root>/_inbox_<label>.md` (create with header `# Inbox — <label>`); otherwise (target session does not exist yet) append to the global `<session_root>/_inbox.md` (create with header `# Inbox — <slug>`).

**Issue a stable ID first** (home slug = the inbox's slug = current `<slug>`; namespaced by `<handle>`): `python3 <session>/scripts/inbox-id.py next --slug <slug> --handle <handle>` — prepend `<id> · ` to the header. Fallback `<acronym>-<handle>#?` if unavailable; never block. See `references/inbox-convention.md` § Stable IDs.

```markdown
## <id> · [YYYY-MM-DD @<handle>] from <slug> / <current-session-name> (<current-type>) [spawn] — <label>
> [status: ready]
- **Type:** <story / cab / plugin / personal / general>
- **linked_sessions:** <current-session-name>
- **Next step:** <concrete first action for the person picking this up>
- **Context:**
  - <finding or decision bullet>
  - <finding or decision bullet>
  - ...
```

`<current-type>` in the header is the **source** (current) session's type — provenance (`source-type`) for where the spawn came from. It may differ from the `- **Type:**` bullet, which is the *session type to create* when someone picks this up.

**The `> [status: ready]` line** is the capture status line (see `references/inbox-convention.md` § Item Model): a spawn is a **promoted capture** at `status: ready` — staged and pickable the moment it's written — tagged `[spawn]`. There is no type axis on a capture. Do not confuse the capture's `status` with the `- **Type:**` bullet (the session type to create) — they are different axes and both are correct as written. Derive `<current-type>` from the current session's `type:` frontmatter / `- **Type:**` bullet.

Do **not** write `_active` or modify the current session file in any way.

### 5. Confirm to User

Surface the write (free rein, never silent — acp-ajudd#5): the spawn entry is written in Step 4 without any propose→approve step, then reported here. Lead with the stable `<id>`. Print:

```
Spawned: [<id>] <label>
  Type:       <type>
  Links to:   <current-session-name>
  Next step:  <next step>
  Context:    <N bullets>

Wrote inbox item <id> to the <target> inbox (the consolidated <slug> inbox for plugin/personal; <label>'s inbox for a matching story/cab/general session). The next /session:start on this project will surface it as ready to pick up.
Current session unchanged.
```

---

## How Pickup Works (for reference)

When `/session:start` is run and the global inbox is shown, `[spawn]` entries are flagged with ★ and listed as "ready to start" rather than resume. Picking one up runs the full new-session kickoff (Jira story creation, branch, etc.) with the linked context block pre-loaded so the person starting it immediately sees findings and next step from the parent session.
