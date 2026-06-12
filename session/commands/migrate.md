---
name: migrate
description: One-time migration — move session files AND project memories from local ~/.claude into the repo under .claude/ so they are git-tracked and shared across developers.
argument-hint: "[--force]"
---

# Session Migrate

Move **the current repo's** session files from local memory into the git repo under `.claude/sessions/`. Run this from within any session on any repo — it uses `pwd` to determine which repo to migrate. After migration all session reads and writes use the repo path. Local files are preserved as a backup but no longer updated.

Run once per project. Use `--force` to re-sync local → repo if repo sessions get corrupted.

**Example:** Working in a VO story session and want to migrate that repo's sessions? Just run `/session:migrate` — it picks up `pwd` and migrates the VO repo's local session files into `<vo-repo>/.claude/sessions/`. You don't need to leave your current session or context.

---

## Instructions

### 1. Verify Conditions

Run `pwd` and extract the repo slug (last path component).

```bash
git rev-parse --show-toplevel
```

- **Not a git repo:** stop — "Session migrate requires a git repository."
- **`--force` flag present:** skip the "already migrated" guard in step 2 and proceed.

### 2. Guard Against Re-Run

Check whether `<repo_root>/.claude/sessions/` and `<repo_root>/.claude/memory/` already exist.

- **Both exist (no `--force`):** stop —
  ```
  Already fully migrated — .claude/sessions/ and .claude/memory/ both exist.
  Use --force to re-sync local → repo (overwrites repo copies with local files).
  ```
- **`.claude/sessions/` exists, `.claude/memory/` does not (no `--force`):** skip Phase A (session files, Steps 3–11a), run Phase B (memory migration, Step 11b) only. Show: "Sessions already migrated — running memory migration only."
- **Neither exists:** run Phase A (Steps 3–11a) then Phase B (Step 11b) as normal.
- **`--force` flag present:** skip this guard entirely — redo everything.

### 3. Confirm Local Sessions Exist

Check `~/.claude/memory/sessions/<slug>/`. List all `.md` files not starting with `_`.

- **None found:** stop — "No local sessions found for `<slug>`. Nothing to migrate."
- **Found:** show the list and confirm:
  ```
  Found N session file(s) for <slug>:
    session.md
    release.md
    ...

  Migrate these to .claude/sessions/? (Yes / Cancel)
  ```

### 4. Create Repo Structure

```bash
mkdir -p <repo_root>/.claude/sessions
```

Write `<repo_root>/.claude/sessions/.gitignore`:
```gitignore
# Per-user state — never commit
_active
_resume_*
*.approved-hash
```

Add to repo root `.gitignore` if `.claude/config/` is not already excluded:
```gitignore
.claude/config/
```

### 5. Read Handle

Read `handle` from `~/.claude/plugins/user-config.json` (`user.handle`). If absent, derive from `user.email` prefix.

### 6. Copy and Transform Session State Files

For each `<name>.md` not starting with `_` in `~/.claude/memory/sessions/<slug>/`:

1. Read the file.
2. Remove the `- **Project:** ...` line entirely.
3. Convert `Scope:` from absolute path to relative:
   - Strip the absolute project root prefix and any leading separator.
   - For plugin sessions the absolute scope was `<marketplace-root>/<plugin-name>` → relative scope = `<plugin-name>/`
   - For story/personal the scope was the repo root (i.e., `./`)
   - If scope is already relative or empty, leave as-is.
4. Add `- **updated-by:** @<handle>` after the `- **Name:** ...` line if not already present.
4a. Add `- **created-by:** @<handle>` immediately after the `- **updated-by:** ...` line if not already present. Seeded from the migrating user's handle as the best available approximation — original authorship cannot be determined from local session files.
5. Convert `- **Next step:** <text>` (scalar) to array format: `- **Next steps:**\n  - [today @<handle>] <text>`. If value is "none" or empty, write `- **Next steps:** none`.
6. Tag any untagged Open items: for each item under `- **Open items:**` that does not start with `[YYYY-MM-DD @`, prepend `[today @<handle>] `.
7. Scan body text for absolute local paths and report them:
   ```bash
   grep -n "C:\\dev\|C:\\temp\|C:\\Users\|/c/dev\|~/.claude/memory\|~/.claude/projects" "<name>.md"
   ```
   If any found, show them and note: "These paths may need manual cleanup — they reference local machine paths that won't resolve for other developers." Do not block the migration; report after all files are processed.
8. Write to `<repo_root>/.claude/sessions/<name>.md`.

### 7. Retroactively Tag History

Copy `~/.claude/memory/sessions/<slug>/_history.md` to `<repo_root>/.claude/sessions/_history.md`.

For each line matching the pattern `[YYYY-MM-DD] <name> —` (no handle already present):
- Rewrite as `[YYYY-MM-DD @<handle>] <name> —`

Lines already containing `@` are left unchanged.

### 8. Copy and Tag Inbox / Backlog Files

For each file matching `_inbox*.md`, `_backlog*.md` in `~/.claude/memory/sessions/<slug>/`:

1. Copy to `<repo_root>/.claude/sessions/`.
2. For each entry header line matching `## [YYYY-MM-DD] from` (no handle present):
   - Rewrite as `## [YYYY-MM-DD @<handle>] from`

### 9. Copy Context, Archive, and Work Files

Copy as-is (no handle tagging needed):
- `_inbox_*_archive.md`
- `_backlog_*_archive.md` (if any)
- `_context_*.md` (pre-clear dumps — useful for teammates)
- `_work_*.md` (work notes created during inbox processing — carry the decisions forward)

Do **not** copy:
- `_active` — per-user hint, excluded by `.gitignore`
- `_resume_*` — transient per-user signal, excluded by `.gitignore`

### 10. Create Local Config

Write `~/.claude/config/<slug>.json`:
```json
{
  "projectRoot": "<absolute path from git rev-parse --show-toplevel>",
  "handle": "<handle>"
}
```

Create `~/.claude/config/` directory if it does not exist.

### 11. Write Approved-Hashes and Install Pre-Commit Hook

**Approved-hashes:** For each session file written to `<repo_root>/.claude/sessions/<name>.md`, compute its SHA-256 hash and write to the local approved-hash file:
```bash
python3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "<repo_root>/.claude/sessions/<name>.md" > ~/.claude/memory/sessions/<slug>/<name>.approved-hash
```
This seeds the approval baseline so the first `session:start` after migration loads cleanly without triggering a first-time review prompt.

**Pre-commit hook:** Write the session content guard directly into `.git/hooks/pre-commit` (create or append). Read the script content from `${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session-commit-guard.py` and embed it:

```bash
# Check if pre-commit hook already exists
if [ -f "<repo_root>/.git/hooks/pre-commit" ]; then
  # Append a call to session-commit-guard.py if not already present
  grep -q "session-commit-guard" "<repo_root>/.git/hooks/pre-commit" || \
    echo 'python3 ~/.claude/plugins/cache/ajudd-claude-plugins/session/*/hooks/scripts/session-commit-guard.py || exit 1' >> "<repo_root>/.git/hooks/pre-commit"
else
  # Write full script content directly — no path dependency on plugin cache
  cp "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session-commit-guard.py" "<repo_root>/.git/hooks/pre-commit"
  chmod +x "<repo_root>/.git/hooks/pre-commit"
fi
```

**Preferred approach:** Write the full script content directly into `.git/hooks/pre-commit` rather than calling the plugin cache path. This avoids breakage if the plugin is updated or the cache is cleared. Read `${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session-commit-guard.py` and write its content to `.git/hooks/pre-commit`, prepending `#!/usr/bin/env python3` if not already present.

Note: `.git/hooks/` is local only — not committed. Each developer installs by running `session:migrate` once.

### 11a. Build `_index.md`

Construct the session index from all written session files. Enables fast, handle-attributed listings without reading individual session files at listing time.

Write `<repo_root>/.claude/sessions/_index.md`:
```
# Session Index — <slug>
# name | created-by | created-date | updated-by | updated-date | status | title
```

For each `<name>.md` written in Step 6, append one line (7 columns):
- `name` = filename without `.md`
- `@created-by` = `created-by:` field from the written file (or `@<handle>` if absent)
- `created-date` = from git: `git log --diff-filter=A --follow --format=%as -- "<session_root>/<name>.md" | tail -1`; fall back to `updated:` frontmatter date if git returns nothing
- `@updated-by` = `updated-by:` field from the written file (or `@<handle>` if absent)
- `updated-date` = `updated:` frontmatter value
- `status` = `Status:` field value (e.g. `in-progress`, `completed`, `paused`)
- `title` = `Title:` field for story/cab types; `—` for plugin, personal, and general

Example:
```
BPT2-6377 | @ajudd | 2026-06-01 | @ajudd | 2026-06-09 | in-progress | Shopify Member Agreement Prompt
session   | @ajudd | 2026-06-01 | @nivi  | 2026-06-11 | in-progress | —
```

### 11b. Migrate Local Project Memories

Find the local project memory path. The encoded path format is the full `projectRoot` path with path separators and special characters replaced by `-`. Search for it:

```bash
ls ~/.claude/projects/*/memory/MEMORY.md 2>/dev/null
```

If multiple matches, prefer the one whose directory name most closely corresponds to `projectRoot` (from `~/.claude/config/<slug>.json`).

**If no local memory directory found:** skip silently — show "No local project memory found — skipping memory migration."

**If found:** read the directory. Count `.md` files (excluding `MEMORY.md` and `.migrated-to-repo`).

Show:
```
Local project memory: N files at ~/.claude/projects/<encoded>/memory/
Repo memory:          .claude/memory/ [exists with M files / does not exist]
```

Determine what to do:
- Files with same name already in `.claude/memory/`: K files → skip
- Files not yet in `.claude/memory/`: J files → add

Show plan:
```
Will add:  J file(s)
Will skip: K file(s) — already present in repo
```

Confirm: "Proceed? (Yes / Skip)"

**On confirm — execute:**

1. Create `<repo_root>/.claude/memory/` if it does not exist.

2. For each `*.md` file in local memory (not `MEMORY.md`, not `.migrated-to-repo`):
   a. If `<repo_root>/.claude/memory/<filename>` already exists → skip.
   b. If not present:
      - Read local file.
      - Add attribution to frontmatter (after the closing `---` of the existing metadata block, before the body). Insert these fields inside the frontmatter block (before its closing `---`):
        ```
        created-by: "@<handle>"
        created-date: "<file mtime — YYYY-MM-DD format>"
        updated-by: "@<handle>"
        updated-date: "<file mtime — YYYY-MM-DD format>"
        ```
        Get mtime via: `python3 -c "import os,datetime; t=os.path.getmtime('<path>'); print(datetime.date.fromtimestamp(t))"`
      - Write to `<repo_root>/.claude/memory/<filename>`.

2a. **Label walk-through** — apply the memory plugin's feature-label convention to every file being added. Read `~/.claude/plugins/marketplaces/<pluginMarketplaceName>/memory/skills/memory/references/label-convention.md` first (derive `pluginMarketplaceName` from `~/.claude/plugins/user-config.json`). If the memory plugin is not installed, skip this sub-step silently and leave files unlabeled.

   For each file being added that does not already have a `label:` field, read its content and propose a `feature:<area>/<subcategory>` label inferred from its `name`, `description`, and body. Present all proposals as one batch (do not prompt one file at a time):
   ```
   Suggested labels (edit any, then 'go'):
     1  project-checkout-flow          → feature:checkout/order-flow
     2  feedback-teams-html            → (behavioral — global, no feature label)
     3  reference-oracle-environments  → feature:oracle-legacy/connections
     ...
   Reply: 'go' to accept all · '1 feature:cart/totals' to override · '2 skip' to leave unlabeled
   ```
   - Files that are clearly behavioral/global feedback (preferences, cross-project rules) should be proposed as `(behavioral — global, no feature label)` and left unlabeled — they are not feature-scoped.
   - On `go` (with any overrides applied): add the chosen `label:` line and a `written: <created-date>` line to each file's frontmatter (use the mtime-derived created-date as `written`).
   - This is the one-time relabel pass the memory plugin's `scan`/`load` depend on. Files left unlabeled remain findable by description but won't match label-based searches.

3. Regenerate `<repo_root>/.claude/memory/MEMORY.md` fresh from all files now present:
   - Read all `*.md` files in `.claude/memory/` (not `MEMORY.md` itself, not `.migrated-to-repo`)
   - For each, extract `name:` and `description:` from frontmatter
   - Write `MEMORY.md`:
     ```
     # Memory Index

     - [<name>](<filename>) — <description>
     ```
   - One line per file, sorted alphabetically by filename.

4. Write local sentinel file:
   ```
   ~/.claude/projects/<encoded-path>/memory/.migrated-to-repo
   ```
   Content: `"Migrated to repo: <repo_root>/.claude/memory/ on <today>"`

5. Create or update `<repo_root>/.claude/CLAUDE.md`:
   - If file does not exist: create it with both entries below.
   - If exists and `@.claude/memory/MEMORY.md` import is already present: skip the import line, but still add the Project Memory section if absent.
   - If exists and import not present: append both entries.

   Content to add:
   ```
   @.claude/memory/MEMORY.md

   ## Project Memory
   This repo uses `.claude/memory/` for shared project memory. When saving
   project-level memories (feedback, project context, references), write to
   `.claude/memory/<filename>.md` and update `.claude/memory/MEMORY.md` —
   not the local `~/.claude/projects/` path.
   ```

### 12. Confirm and Commit

Show a summary:
```
Ready to commit:
  .claude/sessions/          — N session file(s), transformed (Next steps array, created-by/updated-by, @handle tags, path cleanup)
  .claude/sessions/_index.md — N sessions indexed (name | @created-by | @updated-by | date | status | title)
  .claude/sessions/_history.md — N entries tagged @<handle>
  .claude/sessions/.gitignore  — includes *.approved-hash exclusion
  .gitignore                 — added .claude/config/ exclusion
  .claude/memory/            — J memory file(s) added (K skipped — already present)
  .claude/memory/MEMORY.md   — index regenerated (N entries)
  .claude/CLAUDE.md          — @import and write redirect added/updated

Local only (not committed):
  ~/.claude/memory/sessions/<slug>/<name>.approved-hash — N files seeded
  ~/.claude/projects/<encoded>/memory/.migrated-to-repo — sentinel written
  .git/hooks/pre-commit — session-commit-guard installed

Commit and push? (Yes / Edit message / Cancel)
```

Omit the `.claude/memory/` and `.claude/CLAUDE.md` lines if Step 11b was skipped.

Default commit message: `chore: add Claude Code session files and project memory (.claude/)`

- **Yes:** stage `.claude/sessions/`, `.claude/memory/`, `.claude/CLAUDE.md`, and `.gitignore` changes, commit, push.
- **Edit message:** ask for preferred message, then commit and push.
- **Cancel:** leave files in place but do not commit. User can commit manually.

### 13. Confirm Completion

```
Migrated — session files and project memory are now repo-based.

  Local backup:  ~/.claude/memory/sessions/<slug>/  (preserved, no longer updated)
  Repo sessions: <repo_root>/.claude/sessions/
  Repo memory:   <repo_root>/.claude/memory/  (N files)
  Local memory:  ~/.claude/projects/<encoded>/memory/  (preserved as fallback — sentinel written)
  Local config:  ~/.claude/config/<slug>.json

Going forward all session reads and writes use .claude/sessions/.
Going forward project memory writes go to .claude/memory/ (enforced by .claude/CLAUDE.md).
To revert memory: delete .claude/ folder — Claude falls back to local memory automatically.
New developers who pull this repo will be prompted for their local path on first session start.
```

Omit the Repo memory / Local memory lines if Step 11b was skipped.

---

## --force Re-sync

Same steps 5–11, but:
- `.claude/sessions/` already exists — **overwrite** all files.
- Skip the confirm in step 3 (no "Already migrated" guard).
- Commit message: `chore: re-sync Claude Code session files from local`
