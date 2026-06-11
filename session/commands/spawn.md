---
name: spawn
description: Stage a new linked session from the current one — writes a [spawn] inbox entry with full context so the next /session:start can pick it up and run with it. Current session is unchanged.
---

# Session Spawn

Prepares a handoff for a new session by writing a `[spawn]` entry to the global `_inbox.md`. Your active session does not change. The spawned entry appears in the global inbox the next time anyone runs `/session:start` on this project — clearly marked and ready to kick off.

**Typical use:** You finish a planning or investigation session and want to hand off to an implementation session — same project, new scope, connected history.

## Instructions

### 1. Identify Current Session

Read current session from conversation context (the most recent `session:start` output — "Resuming `<name>`"). Do NOT read `_active`.

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).

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

If the spawn `Type` is `plugin` or if the `Label` matches an existing session name in `session_root`, write to `<session_root>/_inbox_<label>.md` (create if needed with header `# Inbox — <label>`).

Otherwise (target session does not exist yet), append to `<session_root>/_inbox.md` (global — surfaces at the next `/session:start` for anyone to pick up; create if needed with header `# Inbox — <slug>`).

```markdown
## [YYYY-MM-DD @<handle>] from <slug> / <current-session-name> [spawn] — <label>
- **Type:** <story / cab / plugin / personal / general>
- **linked_sessions:** <current-session-name>
- **Next step:** <concrete first action for the person picking this up>
- **Context:**
  - <finding or decision bullet>
  - <finding or decision bullet>
  - ...
```

Do **not** write `_active` or modify the current session file in any way.

### 5. Confirm to User

Print:

```
Spawned: <label>
  Type:       <type>
  Links to:   <current-session-name>
  Next step:  <next step>
  Context:    <N bullets>

Wrote to global inbox. The next /session:start on this project will surface it as ready to pick up.
Current session unchanged.
```

---

## How Pickup Works (for reference)

When `/session:start` is run and the global inbox is shown, `[spawn]` entries are flagged with ★ and listed as "ready to start" rather than resume. Picking one up runs the full new-session kickoff (Jira story creation, branch, etc.) with the linked context block pre-loaded so the person starting it immediately sees findings and next step from the parent session.
