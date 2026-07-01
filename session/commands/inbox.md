---
name: inbox
description: Route a work item to another session's inbox. The single hub for all cross-session handoffs — scope guards in checkpoint, finish, and commit invoke this same logic.
argument-hint: "[target-session]"
---

# Session: Inbox

Route a work item to a target session's inbox and record it in the source session's outbox. All cross-session routing flows through here.

## Instructions

### 0. Resolve Context

Run `pwd`, extract slug, resolve `session_root` and `handle` using Path Resolution (see Session Skill).

Determine the current session name from conversation context (most recent "Resuming `<name>`" or "Switching to `<name>`" line). If no session is active, source attribution uses `from <slug>` only — warn: "No active session — routing from repo level. Run `/session:start` first for proper attribution."

Also determine the **source session type** (`story` / `cab` / `plugin` / `personal` / `general`) for provenance — read the active session file's `type:` frontmatter (or the `- **Type:**` body bullet); fall back to the current repo's type from Path Resolution. This is the SOURCE type — recorded on the item so the receiving inbox shows where it came from. If no session is active, omit the `(<type>)` segment.

### 1. Determine Content

If item content is already clear from context (e.g., the scope guard just detected a specific file or described a task), use it directly — do not ask.

Otherwise:
```
What's the item to route? (one-line description)
```

Compose a self-contained body block — enough context that the receiving session can act on it weeks later with no memory of this conversation.

### 2. Determine Target

If an argument was passed (e.g., `/session:inbox release`), use it as the target session name and skip the prompt.

If the target is clear from context (scope guard already identified the file path and owning plugin/session), use it and confirm with a plain routing line:

```
Route to <target-name> inbox?
  yes  ·  pick different
```

Otherwise, list sessions and ask:
```
Where should this go?
  [1] <session-name> — <type> · inbox N · last <date>
  [2] <session-name> — <type> · inbox N · last <date>
  ...
  [G] Global inbox — no named target yet (surfaces at next session:start)
  [X] Cross-repo — different project
```

- **Target type decides the file:**
  - **plugin / personal target** → the slug's consolidated inbox `<target_session_root>/_inbox.md`. These types are item-driven: there is ONE inbox per slug, and `/session:start` `pick`s from it. Do NOT write a per-session `_inbox_<name>.md` for these — the new flow never reads it.
  - **story / cab / general target** → per-session `<target_session_root>/_inbox_<target-name>.md` (route a handoff to a specific story/CAB, as today).
- **Global** → `<target_session_root>/_inbox.md` (cross-cutting items with no specific target; for plugin/personal slugs this is the same file as a named target).
- **Cross-repo** → ask for the target repo slug, then show that repo's sessions using the same prompt

### 3. Write Inbox Entry

Determine target file:
- plugin / personal target, or Global → `<target_session_root>/_inbox.md` (create with header `# Inbox — <slug>` if needed)
- story / cab / general named session → `<target_session_root>/_inbox_<target-name>.md` (create with header `# Inbox — <target-name>` if needed)

Append (record the **source** slug/session/type — not the target):
```markdown
## [YYYY-MM-DD @<handle>] from <source-slug> / <source-session> (<source-type>) — <description>
<body>
```
Omit the `(<source-type>)` segment only when no source session is active (repo-level routing). See Provenance Rendering in `references/inbox-convention.md` for how this header is later displayed.

### 4. Write Outbox Entry

If a source session is active, append to `<session_root>/_outbox_<source-name>.md` (create with header `# Outbox — <source-name>` if needed):

```markdown
## [YYYY-MM-DD @<handle>] → <target-slug> / <target-session> — <description>
<body>
```

Outbox is append-only — never modified or archived.

### 5. Confirm

```
Routed to <target-name> inbox. Will surface when that session starts.
```
