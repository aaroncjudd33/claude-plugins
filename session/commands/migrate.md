---
name: migrate
description: One-time migration — move session files from ~/.claude/memory/ into the project repo under .claude/sessions/ so they are git-tracked and shared across developers.
argument-hint: "[--force]"
---

# Session Migrate

Move this project's session files from local memory into the git repo under `.claude/sessions/`. After migration all session reads and writes use the repo path. Local files are preserved as a backup but no longer updated.

Run once per project. Use `--force` to re-sync local → repo if repo sessions get corrupted.

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

Check whether `<repo_root>/.claude/sessions/` already exists.

- **Exists (no `--force`):** stop —
  ```
  Already migrated — .claude/sessions/ exists.
  Use --force to re-sync local → repo (overwrites repo copies with local files).
  ```
- **Does not exist:** continue.

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
5. Write to `<repo_root>/.claude/sessions/<name>.md`.

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

### 9. Copy Context and Archive Files

Copy as-is (no handle tagging needed):
- `_inbox_*_archive.md`
- `_backlog_*_archive.md` (if any)
- `_context_*.md` (pre-clear dumps — useful for teammates)

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

### 11. Confirm and Commit

Show a summary:
```
Ready to commit:
  .claude/sessions/     — N session file(s)
  .claude/sessions/_history.md — N entries tagged @<handle>
  .claude/sessions/.gitignore
  .gitignore            — added .claude/config/ exclusion

Commit and push? (Yes / Edit message / Cancel)
```

Default commit message: `chore: add Claude Code session files (.claude/sessions/)`

- **Yes:** stage only `.claude/sessions/` and the `.gitignore` changes, commit, push.
- **Edit message:** ask for preferred message, then commit and push.
- **Cancel:** leave files in place but do not commit. User can commit manually.

### 12. Confirm Completion

```
Migrated — session files are now repo-based.

  Local backup:  ~/.claude/memory/sessions/<slug>/  (preserved, no longer updated)
  Repo sessions: <repo_root>/.claude/sessions/
  Local config:  ~/.claude/config/<slug>.json

Going forward all session reads and writes use .claude/sessions/.
New developers who pull this repo will be prompted for their local path on first session start.
```

---

## --force Re-sync

Same steps 5–11, but:
- `.claude/sessions/` already exists — **overwrite** all files.
- Skip the confirm in step 3 (no "Already migrated" guard).
- Commit message: `chore: re-sync Claude Code session files from local`
