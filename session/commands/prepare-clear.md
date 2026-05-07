---
name: prepare-clear
description: Dump volatile in-session reasoning to a context file before running /clear, so /session:resume can fully restore working context without re-explanation.
---

# Session Prepare-Clear

Captures everything held in conversation that isn't in persistent files — reasoning chains, confirmed facts, decisions and why, rejected options, open questions, key code/values — into `_context_<session-name>.md`. Then writes a `_resume_<session-name>` marker so `/session:resume` can find this session immediately after `/clear`.

Run this **before** `/clear`. After `/clear`, run `/session:resume` to restore.

## Instructions

### 1. Identify Current Session

Read current session from conversation context (most recent `session:start` output — "Resuming `<name>`"). If not found in context, read `~/.claude/memory/sessions/<slug>/_active` as a fallback.

Run `pwd` and extract the repo slug (last path component).

### 2. Dump Context File

Write `~/.claude/memory/sessions/<slug>/_context_<session-name>.md`:

```markdown
# Pre-Clear Context — <session-name>
Generated: <YYYY-MM-DD HH:MM>

## Problem Being Solved Now
<One paragraph — what are we trying to accomplish in this exact moment>

## Confirmed Facts
- <fact confirmed this session — source or evidence>
- ...

## Decisions Made This Session
- <decision> — **Why:** <reasoning>
- ...

## Rejected Options
- <option> — **Why rejected:** <reason>
- ...

## Open Questions
- <question not yet resolved>
- ...

## Key Code / Values / Names
- <file path, function name, value, or identifier that matters>
- ...

## Exact Next Action
<The most granular possible next step — more specific than the session file's Next step field>
```

Focus on the volatile reasoning layer — things that are true NOW in this conversation that aren't captured in the session file, inbox, or memory. Do not repeat information already in those files.

### 3. Write Resume Marker

Write `~/.claude/memory/sessions/<slug>/_resume_<session-name>` (plain text — just the session name, no extension):

```
<session-name>
```

This is the durable signal that survives `/clear`. `/session:resume` scans for `_resume_*` files rather than relying on `_active`.

### 4. Update Session Status

In `~/.claude/memory/sessions/<slug>/<session-name>.md`, update the `Status` field to `prepare-clear`. If the field does not exist, add it after the `Branch` line.

### 5. Confirm to User

Print:

```
Ready to /clear

  Session:    <name>
  Context:    _context_<name>.md — <N> sections captured
  Marker:     _resume_<name> written

Run /clear now. When you're back, run /session:resume to restore full context.
```
