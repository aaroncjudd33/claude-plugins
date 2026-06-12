---
name: groom
description: Validate project memories for accuracy — confirm, update, or delete. Runs on loaded memories, a feature area, or aged entries.
argument-hint: "[loaded | feature:area | stale | all]"
---

# Memory Groom

Check whether memories still hold and act on the answer. This is the anti-rot mechanism: a memory that influenced work gets validated at the point of relevance (session finish runs `review loaded`), and old untouched memories surface by age.

## Instructions

### 1. Resolve Memory Root and Target Set

Resolve `memory_root` using Project Memory Path Resolution (see Memory Skill). Determine which memories to review from the argument:

- **`loaded`** (default when invoked by `session:finish`): the active session's `- **Loaded memories:**` list. If no session or none loaded, report "No loaded memories to review." and stop.
- **`feature:<area>`** or a topic: grep matching memories (same matching as `/memory:load`).
- **`stale`**: every memory whose `written:` date is more than 6 months before today (and not `confirmed:` within 6 months).
- **`all`**: every memory file in `memory_root`.
- **No argument, no session:** default to `stale`.

### 2. Review Each

For each target memory, read it and present:

```
[1/3]  checkout-payment-validation   [feature:checkout/payment-validation]
       written 2026-06-12 · loaded this session
  ---
  <body>
  ---
  Still accurate?  keep / update / delete
```

Batch the prompts when reviewing more than one — present all, accept combined replies (`1 keep 2 update 3 delete`), and handle `update`/`delete` follow-ups after the batch.

### 3. Apply

- **keep:** no change to the body. If the memory was flagged stale by age, append/update a `confirmed: <today>` line in frontmatter (preserves the original `written:` date while recording the review). Otherwise no write.
- **update:** ask "What changed?" (justified follow-up — content can't be known before). Revise the body, and add an in-line note `> Updated <today>: <what changed>` so history is visible. Do not overwrite `written:`. Refresh the `description:` and `MEMORY.md` line if the summary changed.
- **delete:** confirm once (`Delete <name>? this removes the file — yes / no`), then remove the file and its `MEMORY.md` line. Removing a no-longer-true memory is the point — don't leave rot in place.

### 4. Session Sync

If reviewing the session's loaded set and any memory was deleted, remove it from the session file's `- **Loaded memories:**` list too. Recompute the approved-hash for repo sessions after any session-file write.

### 5. Report

```
Reviewed N memories — K kept, J updated, M deleted.
```
