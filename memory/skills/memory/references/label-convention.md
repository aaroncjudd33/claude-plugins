# Memory Label Convention

The canonical format for project/feature memory labels. Every memory file the memory plugin writes carries a `label:` field in its frontmatter. This is the foundation the `scan`, `load`, `save`, and `review` commands all build on.

---

## The label format

```
feature:<area>/<subcategory>
```

- **`feature:`** — fixed prefix. Marks this as a feature/location memory (as opposed to global behavioral feedback).
- **`<area>`** — the top-level feature or location in the app. Lowercase, kebab-case. Examples: `checkout`, `auth`, `session-plugin`, `downline-reports`.
- **`<subcategory>`** — the specific aspect within that area. Lowercase, kebab-case. Examples: `payment-validation`, `sso-flow`, `resume-path`.

**Examples:**
```
feature:checkout/payment-validation
feature:auth/sso-flow
feature:session-plugin/resume-path
feature:downline-reports/tree-traversal
```

**Stop at subcategory.** Do not encode file names or function names in the label. Files get renamed and functions get refactored — a label tied to `validatePayment()` becomes wrong the moment someone renames it. Features are intentional design units that rename rarely. If a memory is so specific it needs a file or function reference, that detail belongs in the body, not the label — and may be a sign it should be a code comment instead.

---

## Multiple labels

A memory that genuinely spans two feature areas carries a comma-separated list:

```
label: feature:checkout/payment-validation, feature:cart/totals
```

Use sparingly — most memories belong to exactly one area. Multiple labels are for true cross-cutting facts (a shared contract, a data format both areas depend on). If you find yourself adding three or more, the memory is probably too broad and should be split.

---

## Frontmatter shape

```
---
name: checkout-payment-validation
label: feature:checkout/payment-validation
description: Payment validation rules and edge cases at checkout
written: 2026-06-12
---

Body content — the actual fact, in prose. Link related memories with [[other-name]].
```

- **`name`** — short kebab-case slug, matches the filename without `.md`. Used by `[[name]]` cross-links.
- **`label`** — one or more `feature:area/subcategory` values (see above).
- **`description`** — one line. This is what `scan`/`load` match against when no label hits, and what renders in `MEMORY.md`.
- **`written`** — ISO date the fact was first recorded. Drives the staleness signal in `review` (see below). Preserve on update; do not overwrite — instead the body records what changed and when.

---

## Filename

The filename is a short human-readable slug — typically the same as `name`. It is NOT the label and does NOT encode the feature path. All memory files live flat in one directory:

```
.claude/memory/
  checkout-payment-validation.md
  auth-sso-flow.md
  session-plugin-resume-path.md
  MEMORY.md
```

Flat + label-in-frontmatter (rather than nested folders) keeps search to a single grep and lets a label change without moving the file.

---

## Searching by label

```bash
# Everything in the checkout area
grep -rl "label:.*feature:checkout" .claude/memory/

# A specific subcategory
grep -rl "label:.*feature:checkout/payment" .claude/memory/

# All feature memories (regardless of area)
grep -rl "label:.*feature:" .claude/memory/
```

`.*` after `label:` tolerates comma-separated multi-label lines.

---

## Where memory lives — repo vs. local vs. global

| Tier | Path | Holds | Labeled? |
|------|------|-------|----------|
| **Repo** | `<repo>/.claude/memory/` | Project/feature facts, git-tracked, shared | Yes — `feature:X/Y` |
| **Local project** | `~/.claude/projects/<encoded>/memory/` | Project facts before migration | Yes — `feature:X/Y` |
| **Global** | `~/.claude/memory/` | Behavioral feedback, preferences, cross-project rules | No — global memory is not feature-scoped |

The memory plugin manages the **repo** and **local project** tiers (feature memory). Global behavioral memory stays as-is — it is not feature-scoped and loads freely as needed.

**Active project memory path resolution:**
```
if <repo_root>/.claude/memory/ exists  →  use it (repo tier, migrated)
else                                    →  use ~/.claude/projects/<encoded>/memory/ (local tier)
```
`<encoded>` is the projectRoot path with separators replaced by `-` (the Claude Code local memory convention). `<repo_root>` from `git rev-parse --show-toplevel`.

---

## Staleness signal

The `written:` date is the only staleness mechanism — no auto-expiry, no background pruning. `/memory:groom` surfaces memories by age:

- A memory whose `written:` date is more than ~6 months old is flagged for review on the next `review` run.
- Review asks: still accurate? → confirm (no change), update (revise body, note the change + date in-line), or delete (no longer true).
- Confirming an old memory does NOT reset `written:` — instead append a `confirmed: <date>` note so the original age is preserved but the review is recorded.

This is the human-in-the-loop alternative to autonomous memory consolidation: a memory is reviewed when it is loaded into relevant work (at finish) or when its age trips the review threshold. Memories never loaded stay inert and cannot mislead.
