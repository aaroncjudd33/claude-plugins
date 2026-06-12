---
name: doctor
description: Find project memories stranded in the global tier and relocate them to the right project — explicit, confirmed per file. The only command that may read or move global memory.
argument-hint: "[repo slug or path]"
---

# Memory Doctor

Reconcile misplaced project memories. Legacy or mistaken saves can leave project-scoped facts sitting in the **global** behavioral tier (`~/.claude/memory/`), where `/session:migrate`, `/memory:load`, and `/memory:scan` will never find them — they resolve the project tier only. This command finds those stranded files and offers to move them home.

**This is the one and only command permitted to read and move global memory**, and it does so only on explicit invocation, only with per-file confirmation, never silently. Every other memory command treats global as off-limits (see Memory Skill: "Never touch global memory").

**Why this exists and not "make migrate scan global":** classification is genuinely ambiguous. A file tagged `type: feedback` may be a true behavioral preference (belongs in global) or project-specific design guidance mislabeled at save time (belongs in a project). A rule-based auto-mover would either drag personal feedback into a shared repo or strand real project memories — wrong either way, and silent. A human confirm resolves each case cleanly. Migrate stays narrow on purpose; this command carries the cross-tier judgment.

## Instructions

### 1. Resolve Target Project

Determine which project these stranded memories should move to:

- **Argument is a repo slug or path:** use it.
- **No argument:** use the current repo — `git rev-parse --show-toplevel` → slug = last path component. If not in a git repo, ask: "Which project should stranded memories move to? (repo slug or path)".

Resolve the destination project tier the same way the Memory Skill's Path Resolution does:
```
if <repo_root>/.claude/memory/ exists  →  dest = <repo_root>/.claude/memory/   (repo tier)
else                                    →  dest = ~/.claude/projects/<encoded>/memory/   (local tier)
```
Create `dest` and its `MEMORY.md` if needed only at write time (Step 4), not before.

### 2. Scan Global for Project-Looking Files

Read `~/.claude/memory/` (global tier). For each `*.md` file (skip `MEMORY.md`), score whether it looks project-scoped for the target project. Signals, strongest first:

- **Frontmatter `type: project`** — strong.
- **`name`, `label`, or body references the target repo slug** (or a recognizable variant — `commission-payments`, `commissionPayments`, `CommissionPayment`, etc.) — strong.
- **Body cites repo-specific artifacts** — file paths, service names, DynamoDB tables, stored procs tied to that project — medium.
- **`type: feedback` but the content is project-specific design guidance** (not a general "always do X" rule) — weak/ambiguous; surface it but never assume.

Do **not** move on score alone — scoring only decides what to *present*. Exclude anything that reads as a genuine cross-project behavioral rule or user preference.

### 3. Present Candidates — Confirm Per File

```
Stranded project memories for <target> (global tier):

  1  project_commission_payments_period_keys   type:project   → strong (references commission-payments)
       "How period+check composite keys map to annual summaries"
  2  feedback_commission_payments_speculative_fields   type:feedback   → ambiguous (project-specific guidance, but tagged feedback)
       "Don't add speculative fields to the payment projection"
  3  reference_oracle_environments   type:reference   → weak (mentions many projects)
       "Clone/env6 Oracle connection strings"

Relocate which to <dest>?  (numbers / all-strong / none)
Each pick is confirmed individually before moving — ambiguous ones get an extra prompt.
```

- `all-strong` selects only the strong-signal files.
- For each **ambiguous** pick, prompt once more before moving: `"<name>" is tagged <type> — is this project-specific (move) or a behavioral rule (leave in global)?  move / leave`.
- Leave anything the user doesn't pick exactly where it is. Never move a file that wasn't explicitly confirmed.

### 4. Relocate Confirmed Files

For each confirmed file:

1. Read it from global.
2. If it has no `label:` field, propose a `feature:<area>/<subcategory>` per `references/label-convention.md` (see Memory Skill) and confirm inline — these are becoming project memories, so they should carry a label. Add `written:` from the file mtime if absent.
3. Write it to `<dest>/<filename>`. If a file of that name already exists in `dest`, do not overwrite — report the collision and skip (the user can reconcile manually).
4. Remove the file from `~/.claude/memory/` (global) **only after** the destination write succeeds.
5. Update both indexes: append the entry to `<dest>/MEMORY.md`; remove its line from `~/.claude/memory/MEMORY.md`.

**Move, don't copy** — the whole point is to stop the file from living in global. A successful relocation leaves exactly one copy, in the project tier.

### 5. Report

```
Relocated K file(s) to <dest>:
  - <name>  [<label>]
Left in global (your choice / behavioral): J file(s)
Skipped (name collision in dest): M file(s)
```

If any were relocated to a repo tier and a session is active, note: "Run `/session:migrate` to commit these to the repo, or they'll travel on your next session sync." If files were relocated, suggest a quick `/memory:scan` to confirm they're now discoverable.
