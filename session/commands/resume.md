---
name: resume
description: Instantly restore session context after /clear — no navigation, no list if unambiguous. Reads _resume_* markers and the pre-clear context file.
---

# Session Resume

Fast context restoration after `/clear`. Reads `_resume_*` marker files to find which session(s) need restoring, loads the session file and pre-clear context dump, and drops you back in without navigation.

**This is not session:start.** No inbox processing, no Teams setup, no options list (unless multiple sessions are waiting). Pure context restoration.

## Instructions

### 1. Find Waiting Sessions

Run `pwd` and extract the repo slug. Resolve `session_root` using Path Resolution (see Session Skill). `_resume_*` markers are always local — scan `~/.claude/memory/sessions/<slug>/`, not `session_root`.

Scan `~/.claude/memory/sessions/<slug>/` for any files matching `_resume_*`. Each file represents a session waiting to be resumed after a `/clear`.

- **One found:** proceed automatically — no prompt needed.
- **Multiple found (≤ 4):** use **AskUserQuestion** (SessionPickerPrompt — see prompt-patterns.md):
  ```yaml
  question: "Multiple sessions waiting — which to resume?"
  header: "Session"
  options:
    - label: "<session-name-1>"
      description: "Last resume marker for this session"
    - label: "<session-name-2>"
      description: "..."
  ```
- **Multiple found (> 4):** show a numbered list and ask as plain text: "Which session? (number)"
- **None found:** fall back to `_active`. If `_active` exists, resume that session with a note: "No resume marker found — resuming last active session (`<name>`)." If neither exists, ask: "Which session to resume? (name or 'start' to run /session:start instead)"

### 2. Load Session File

Read `<session_root>/<session-name>.md` and extract all fields.

Read last 5 entries from `<session_root>/_history.md` (omit block if file doesn't exist).

### 3. Load Pre-Clear Context (if present)

Check for `<session_root>/_context_<session-name>.md`.

If found, read the full file. This is the volatile reasoning layer captured before `/clear`.

### 4. Display Resume Block

```
Resuming <name> (after /clear)
  Branch:      <branch>
  Open items:  <bullets or "none">
  Next step:   <next step>

Recent history:
  [YYYY-MM-DD] <entry>
  ...

Pre-clear context:
  Problem:     <problem being solved>
  Decisions:   <key decisions>
  Next action: <exact next action>
  [full context available — type 'context' to see all sections]
```

Show a compact summary by default. If the user types `context`, display the full `_context_<session-name>.md` contents.

### 5. Clean Up

Delete the `_resume_<session-name>` marker file — it has been consumed.

If `_context_<session-name>.md` was loaded, use **AskUserQuestion** (ConfirmPrompt — see prompt-patterns.md):

```yaml
question: "Archive the pre-clear context file?"
header: "Context file"
options:
  - label: "Yes, archive it"
    description: "Delete _context_<name>.md — it's loaded into context and no longer needed"
  - label: "Keep for reference"
    description: "Leave it in place for this session"
```

- **Yes, archive it:** delete the file — it's been loaded into context, no longer needed.
- **Keep for reference:** leave it in place for this session; it will not be shown again automatically.

Update `Status` field in `<session_root>/<session-name>.md` back to `in-progress`.

Write `~/.claude/memory/sessions/<slug>/_active` with the session name (always local — refreshes the hint for session:start).

### 6. Continue

No inbox processing. No Teams setup. Work resumes from where it left off.
