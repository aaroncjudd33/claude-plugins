# Staleness Check — Algorithm Reference

Used by `/memory:groom` (Step 2) and `session:finish` Slot A2 (review path). Runs the same algorithm in two modes:

- **Scoped** — a provided list of files (used by `session:finish` against `Loaded memories:`)
- **Full** — all `*.md` files in `memory_root` (used by `/memory:groom all` or `/memory:groom stale`)

---

## Algorithm

### Input
- `files`: list of memory file paths to check
- `repo_root`: from `git rev-parse --show-toplevel` (run once, reuse)

### Step 1 — Extract Code References

For each file, read the body and extract **backtick-wrapped** content only (single backticks `` `like this` ``). This scopes extraction to explicit code references, not prose descriptions.

Filter extracted strings to those that look like file paths:
- Contains a `/` (path separator), OR
- Has a recognizable code extension: `.ts`, `.tsx`, `.js`, `.cs`, `.py`, `.md`, `.json`, `.yaml`, `.yml`, `.tf`, `.sh`

Exclude false positives: strings shorter than 4 characters, purely generic terms (`null`, `true`, `any`, `void`, `this`, `key`, `id`), and strings that are clearly prose wrapped in backticks for emphasis (e.g., `` `go` ``, `` `yes` ``).

### Step 2 — Check Existence

For each extracted file-path reference:

```bash
# Try exact relative path from repo root
ls "<repo_root>/<ref>" 2>/dev/null

# If not found, try by basename
find "<repo_root>" -name "<basename(ref)>" -maxdepth 6 2>/dev/null | head -3
```

If neither resolves → **flag** the reference as not found.

Only flag when BOTH checks miss. A file that moved location (found by basename but not at the exact path) is not flagged — the memory's path reference is stale but the concept is still valid. Optionally note the new location as a suggestion.

### Step 3 — Produce Findings

Group files into two buckets:

**Flagged** — one or more references not found:
```
checkout-payment-validation  [feature:checkout/payment-validation]
  ⚠  `src/checkout/PaymentForm.cs` — not found in repo
  ⚠  `CheckoutApiController.cs` — not found (searched by name)
```

**Clean** — all references resolved (or no file-path references extracted):
- In **scoped mode** (session:finish): clean files are skipped — no review needed
- In **full mode** (groom all/stale): clean files still appear in the review but with a lighter prompt

### Step 4 — Return

Return two lists:
- `flagged[]`: files with unresolved references + the specific refs that failed
- `clean[]`: files that passed (or had no checkable references)

Callers (groom Step 2, finish A2) decide how to present and what dispositions to offer based on these lists.

---

## Performance Notes

- Run all `ls`/`find` checks in parallel across files where possible
- Skip the check entirely for memories whose body has no backtick spans at all (no file-path references to extract)
- `maxdepth 6` on `find` keeps it bounded for large repos
- The check is best-effort: a reference not found is a *signal*, not a verdict. The user confirms the final disposition.

---

## Integration Points

**`/memory:groom` Step 2:** runs this algorithm, leads the review with flagged files, presents clean files with a lighter "confirm" prompt.

**`session:finish` Slot A2 (review path):** runs this algorithm in scoped mode against `Loaded memories:`. Only flagged files appear in the batch — clean loaded memories are kept automatically. If all loaded memories are clean: skip straight to the capture offer.
