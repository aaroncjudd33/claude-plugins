---
name: load
description: Load project memories by topic or feature label into context. Explicit, user-directed — the targeted counterpart to scan.
argument-hint: "<topic or feature:area/sub>"
---

# Memory Load

Load specific project memories into context by topic or label. Use when you know what you want — `/memory:scan` is for "what's relevant to where I am", `/memory:load` is for "give me the checkout payment stuff".

## Instructions

### 1. Resolve Memory Root

Resolve `memory_root` using Project Memory Path Resolution (see Memory Skill). If `MEMORY.md` does not exist, report "No project memory for this repo yet." and stop.

### 2. Interpret the Argument

- **No argument:** ask "What do you want to load? (a topic, or a `feature:area/sub` label)" and wait.
- **Looks like a label** (`feature:...`): treat as an exact-ish label match.
- **Free text:** treat as a topic — match against both labels and descriptions.

### 3. Match

```bash
# Label-shaped argument
grep -rl "label:.*feature:checkout/payment" <memory_root>

# Topic argument — labels first, then MEMORY.md descriptions
grep -rl "label:.*checkout" <memory_root>
```
Also scan `MEMORY.md` description lines for the topic terms. Merge and dedupe.

### 4. Load

- **Single clear match:** read it, report `Loaded: <name>`.
- **Multiple matches:** list them numbered (name + label + description) and ask `Load which? (numbers / all)`, then load the picks.
- **No match:** "Nothing matched '<arg>'. Closest by description: <1–3 nearest>. Load any? (numbers / no)" — offer the nearest description matches; stop if none.

### 5. Record to Session

Same as `/memory:scan` Step 5 — add each loaded memory to the active session's `- **Loaded memories:**` list (`  - <name>  [<label>]`), create the field if absent, recompute approved-hash for repo sessions. Skip silently if no session is active.
