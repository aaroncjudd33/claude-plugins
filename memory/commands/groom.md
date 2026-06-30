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

### 2. Staleness Check + Review

**First — run the automated staleness check.** Read `references/staleness-check.md` and apply the algorithm against the target set (full mode — all files). This produces two buckets: `flagged` (unresolved code references found) and `clean`.

**Flagged files lead the review.** Present them first with their specific findings:

```
[1/3]  checkout-payment-validation   [feature:checkout/payment-validation]
       written 2026-06-12 · ⚠ stale reference detected
  ⚠  `src/checkout/PaymentForm.cs` — not found in repo
  ⚠  `CheckoutApiController.cs` — not found (searched by name)
  ---
  <body>
  ---
  Still accurate?  keep / update / delete
```

**Clean files follow** with a lighter prompt — no body shown unless the memory is older than 6 months (by `written:` date):

```
[2/3]  cart-totals  [feature:cart/totals]
       written 2026-05-01 · all references resolved
  Confirm still accurate?  keep / delete  (default: keep)
```

If a clean file is older than 6 months (stale by age regardless of reference check): show the full body and use the same `keep / update / delete` prompt as flagged files.

**If no flagged files and no aged files:** report "Memory: all N files pass staleness check — no review needed." and skip to Step 4.

Batch all prompts — present all, accept combined replies (`1 keep 2 update 3 delete`). Handle `update`/`delete` follow-ups after the batch.

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
