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

- **Named session** → `<target_session_root>/_inbox_<target-name>.md`
- **Global** → `<target_session_root>/_inbox.md` (for items with no known target session or truly cross-cutting items)
- **Cross-repo** → ask for the target repo slug, then show that repo's sessions using the same prompt

### 3. Write Inbox Entry

Determine target file:
- Named session → `<target_session_root>/_inbox_<target-name>.md` (create with header `# Inbox — <target-name>` if needed)
- Global → `<target_session_root>/_inbox.md` (create with header `# Inbox — <slug>` if needed)

Append:
```markdown
## [YYYY-MM-DD @<handle>] from <source-slug> / <source-session> — <description>
<body>
```

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
