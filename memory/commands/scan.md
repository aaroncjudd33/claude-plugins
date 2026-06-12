---
name: scan
description: Detect the current feature area from context and surface matching project memories to load. Never auto-loads — you pick.
argument-hint: "[feature area or topic]"
---

# Memory Scan

Infer what you're working on and surface project memories that look relevant. You choose which to load. Use this when starting work in an area, or when you want to know what the project already knows about the feature you're touching.

## Instructions

### 1. Resolve Memory Root

Resolve `memory_root` using Project Memory Path Resolution (see Memory Skill). If `MEMORY.md` does not exist there, report "No project memory for this repo yet — use `/memory:save` to create the first entry." and stop.

### 2. Determine Feature Area

If an argument was passed, use it as the feature area / topic directly.

Otherwise infer from context using Feature-Area Detection (see Memory Skill), in priority order: current conversation → branch name → active session `Title:` → recently touched files (`git diff --name-only` + `--staged`). Derive 1–4 candidate terms (e.g. `checkout`, `payment`, `validation`).

Show what was inferred:
```
Scanning for: checkout, payment, validation
  (from branch feature/BPT2-6155-checkout-validation + 3 changed files)
```

### 3. Match

Run two passes against `memory_root`:

1. **Label match (precise):** grep memory files for `label:.*feature:<term>` for each term.
   ```bash
   grep -rl "label:.*feature:checkout" <memory_root>
   ```
2. **Description match (fuzzy):** scan `MEMORY.md` description lines for the terms.

Merge results, dedupe, rank label matches above description-only matches.

### 4. Present Candidates

```
Found N relevant memories:

  1  checkout-payment-validation   [feature:checkout/payment-validation]
     Payment validation rules and edge cases at checkout
  2  cart-totals                   [feature:cart/totals]
     How line-item totals and tax are computed

Load which? (numbers / all / none)
```

If none matched: "No memories matched <terms>. Try `/memory:load <topic>` with a different term, or `/memory:save` to record what you learn." and stop.

### 5. Load and Record

For each picked memory: read the file into context and report `Loaded: <name>`.

**Record to session** (if a session is active — find it via the session plugin's Path Resolution `_active` marker → session file):
- Add each loaded memory to the session file's `- **Loaded memories:**` list as `  - <name>  [<label>]` if not already present.
- If the field does not exist yet, add it after `Open items:`.
- Recompute the approved-hash for repo sessions after writing (see session Skill).

If no session is active, skip recording silently — the memories are still loaded for this conversation.
