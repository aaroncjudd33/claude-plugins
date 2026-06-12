---
name: save
description: Create a project memory with a proper feature label. Guided — proposes label, filename, and frontmatter; you confirm.
argument-hint: "[what to remember]"
---

# Memory Save

Record a project/feature fact with a `feature:area/subcategory` label so it can be found later. Use when you learn something about how the codebase works that future sessions (or teammates) should know.

**Scope check first:** this is for *project/feature* facts — how a feature works, a non-obvious constraint, a data contract, a gotcha tied to an area of the app. It is NOT for behavioral preferences or cross-project rules — those are global memory (`~/.claude/memory/`), out of scope here. If the fact is behavioral ("always do X"), say so and point to the global auto-memory system instead.

## Instructions

### 1. Resolve Memory Root

Resolve `memory_root` using Project Memory Path Resolution (see Memory Skill). Create the directory and a `MEMORY.md` (with `# Memory Index` header) if they do not exist.

Read `references/label-convention.md` (see Memory Skill) before composing the label.

### 2. Gather the Fact

- **Argument given:** use it as the fact.
- **No argument:** ask "What should I record?" and wait.

If the fact is unclear or too broad to be one memory, ask one clarifying question — or note that it may need to be split into two memories.

### 3. Propose Label, Name, and Description

Infer the feature area from the fact and the current context (conversation, branch, touched files). Propose:

```
Proposed memory:
  label:       feature:checkout/payment-validation
  name:        checkout-payment-validation
  description: Payment validation rules and edge cases at checkout
  written:     <today>

Body:
  <the fact, in prose — 1–4 sentences>

Confirm? (go / edit label: <x> / edit name: <x> / edit desc: <x> / edit body: <text> / cancel)
```

- Check for an existing memory with a matching label or near-identical name — if found, say so and offer to **update that one instead** (route to `/memory:review` on that file) rather than creating a duplicate.
- Keep the body tight. Link related memories with `[[other-name]]`.

### 4. Write

On `go` (applying any edits):

1. Write `<memory_root>/<name>.md`:
   ```
   ---
   name: <name>
   label: <label>
   description: <description>
   written: <today>
   ---

   <body>
   ```
2. Append to `MEMORY.md`: `- [<name>](<name>.md) — <description>` (keep alphabetical by filename).
3. **Record to session** (if active): add `  - <name>  [<label>]` to `- **Loaded memories:**` — a freshly saved memory counts as loaded. Recompute approved-hash for repo sessions.

Report: `Saved: <name> [<label>]`.
