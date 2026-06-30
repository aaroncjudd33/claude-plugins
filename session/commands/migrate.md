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

Check `~/.claude/memory/sessions/<slug>/`. List all `.md` files not starting with `_`. **Exclude `refinement-*.md`** — refinement sessions are ephemeral and must never be migrated into the repo.

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
_restore_*
_resume_*  # legacy marker name (pre-rename) — keep ignored during transition
*.approved-hash
```

Add to repo root `.gitignore` if `.claude/config/` is not already excluded:
```gitignore
.claude/config/
```

### 5. Read Handle

Read `handle` from `~/.claude/plugins/user-config.json` (`user.handle`). If absent, derive from `user.email` prefix.

### 5a. Pre-Migration Secrets & PII Scan (BLOCKING)

**Before copying anything into the repo, scan every candidate file for secrets and PII.** Migration git-tracks these files permanently — a credential committed here lives in the git history forever, even if removed later. The pre-commit guard (`session-commit-guard.py`) is the backstop, but catch it here first, where files can be excluded or scrubbed cleanly before they ever enter the tree.

**Scan the full content of every file about to be migrated** — session `.md` files, `_history.md`, all `_inbox*.md`, **and especially `_context_*.md`** (pre-clear dumps capture raw working state — connection strings, query output, spoofed identities — and are the highest-risk). Also the project memory files from Step 11b.

Flag:
- **Secrets / credentials** — DB connection strings with passwords (e.g. `user/PASS@host:port`), `password=`/`pwd:` assignments, API keys, `AKIA…` AWS keys, JWTs, `-----BEGIN … PRIVATE KEY-----`. (Same patterns as `SECRET_PATTERNS` in the commit guard.)
- **PII** — real person name ↔ member/custid pairings, `fedTaxNum`/`ssn`/`taxId` fields, addresses tied to a named individual. PII detection is fuzzy — surface anything plausible for the user to judge.

For each flagged file, present a per-file disposition (never silent, never auto-decide):
```
⚠️  Secrets / PII found in files staged for migration:

  _context_strongdm-oracle-setup.md
    [secret] db-connection-credentials — cmsuser/…@oracln.yleo.us:1521  (×2)
  _history.md
    [PII] name↔custid — "Edie Wadsworth / 1443424"
  BPT2-5558.md
    [PII] name↔custid — "Edie Wadsworth / 1443424"

Handle each before migrating:
  exclude <file>   — don't copy it into the repo at all (safest for context dumps / pure-secret files)
  scrub <file>     — copy it but redact the flagged values (placeholders: <REDACTED>, <test-member>)
  keep <file>      — migrate as-is (NOT recommended — secrets/PII enter git history permanently)

Reply per file, e.g. "exclude _context_*, scrub _history.md BPT2-5558.md".
```

Apply before the copy steps:
- **exclude:** drop the file from the migration set entirely — skip it in Steps 6/8/9/11b. Note it in the final summary as "excluded (secrets/PII)".
- **scrub:** copy it, but replace each flagged value with a placeholder (`<REDACTED>` for secrets, `<test-member>` / `<custid>` for PII) during the transform. Preserve surrounding context.
- **keep:** migrate unchanged — only on explicit per-file confirmation; warn once more that it lands in git history.

**Default bias:** recommend `exclude` for `_context_*.md` and any file whose value is purely a secret (e.g. a credentials dump); recommend `scrub` for session/history files that carry real record but happen to name a person. Do not proceed to Step 6 until every flagged file has a disposition.

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
- `_restore_*` — transient per-user signal, excluded by `.gitignore`

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

**Pre-commit hook (shim, not a copy):** Install a thin shim into `.git/hooks/pre-commit` that **delegates** to the live plugin script. Do **not** copy the full script in — a frozen copy goes stale the moment the plugin is fixed, and there is no link back to propagate the update. The shim points at the **marketplace clone** (non-versioned path), so `claude plugin marketplace update` refreshes every migrated repo's guard automatically.

Resolve `<marketplace>` from `~/.claude/plugins/user-config.json` → `pluginMarketplaceName`. The shim references the clone via `$HOME` (portable across machines/users), **not** `${CLAUDE_PLUGIN_ROOT}` (that resolves to the version-pinned cache dir, which is exactly what goes stale).

The shim body to write:

```bash
#!/usr/bin/env bash
# session-commit-guard shim — installed by session:migrate.
# Delegates to the live plugin script so plugin updates propagate automatically.
# Regenerate via session:migrate if the marketplace path changes.
GUARD="$HOME/.claude/plugins/marketplaces/<marketplace>/session/hooks/scripts/session-commit-guard.py"
if [ -f "$GUARD" ]; then
  exec python3 "$GUARD" "$@"
fi
echo "session-commit-guard: plugin script not found at $GUARD — skipping (commit allowed)." >&2
exit 0  # fail open: a missing guard must never block commits
```

Install logic:

```bash
HOOK="<repo_root>/.git/hooks/pre-commit"
if [ -f "$HOOK" ] && ! grep -q "session-commit-guard" "$HOOK"; then
  # Foreign pre-commit hook already present (husky, etc.) — append a guard call,
  # do not clobber it.
  printf '\npython3 "$HOME/.claude/plugins/marketplaces/<marketplace>/session/hooks/scripts/session-commit-guard.py" || exit 1\n' >> "$HOOK"
else
  # No hook, or a prior session shim — (re)write the shim fresh.
  cat > "$HOOK" <<'SHIM'
<shim body from above, with <marketplace> substituted>
SHIM
  chmod +x "$HOOK"
fi
```

Note: `.git/hooks/` is local only — not committed. Each developer installs by running `session:migrate` once. Because the shim delegates to the marketplace clone, a later plugin fix needs no re-migration and no per-repo copy — just `claude plugin marketplace update`.

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

**Migrate reads the local project tier ONLY — by design.** It does not scan the global tier (`~/.claude/memory/`). If project memories are stranded in global (legacy data from before the tier split, or a mis-resolved save), migrate cannot see them and they will be silently left behind. This is intentional: teaching migrate to reach into global would force it to guess which global files are project-scoped vs. genuine behavioral rules — a judgment that must have a human in the loop. That reconciliation lives in `/memory:localize` instead.

**If no local memory directory found:** skip — show "No local project memory found in the project tier — skipping memory migration. If you expected memories here, some may be stranded in the global tier; run `/memory:localize` to find and relocate them, then re-run migrate."

**If found:** read the directory. Count `.md` files (excluding `MEMORY.md` and `.migrated-to-repo`).

**User-specific memory filter (runs before PII scan):**

Scan the candidate list for files that are personal to the developer rather than project context. These should not be committed to a shared repo.

Auto-flag as user-specific:
- Any file matching `user_*.md` (e.g. `user_timezone.md`, `user_team_heber.md`)
- Any file whose `description:` frontmatter contains first-person language ("my", "I") or personal identifiers

If any are found, present as a batch — EXCLUDE is the default:
```
⚠️  User-specific memories (personal to this developer — not project context):

  user_team_heber.md   — "Heber Iraheta — manager/lead, default approver"
  user_timezone.md     — "User's timezone — Eastern time, convert for Jira/CAB"

These will be EXCLUDED from the repo by default.
Reply: 'go' to accept · 'keep user_timezone.md' to override individual files
```

Excluded files stay in local memory and keep working — they are not copied into the repo. This filter runs **before** the PII scan so excluded files are never scanned.

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
   **Apply the Step 5a secrets/PII scan to these files too** (if 11b runs standalone via the guard path and 5a did not execute, run the scan here against the memory files before copying). Honor exclude/scrub/keep dispositions.
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

5. **Do NOT create or modify `<repo_root>/.claude/CLAUDE.md`.** Project memory is loaded **on demand only** by the memory plugin — never auto-loaded. Adding an `@.claude/memory/MEMORY.md` import to `CLAUDE.md` would force the index into every developer's context the moment they open the repo, without invoking any command, with real token cost — the exact overhead this design rejects.

   Instead: the memory plugin resolves `.claude/memory/` via its own Path Resolution. It reads `MEMORY.md` and individual files only when the user runs `/memory:load`, `/memory:scan`, `/memory:groom`, or a session command that surfaces them. It writes new memories to `.claude/memory/` via `/memory:save`. No `CLAUDE.md` redirect is needed — the plugin already knows the path.

   If a `<repo_root>/.claude/CLAUDE.md` already exists for other reasons, leave it untouched. If it contains a stale `@.claude/memory/MEMORY.md` import from a previous version of this command, remove only that import line and report it: "Removed auto-load import from .claude/CLAUDE.md — project memory now loads on demand via the memory plugin."

### 11c. Migrate Playwright Tasks (Phase C)

Detect the E2E tests directory. Check in order — stop at the first hit:
1. `e2eTestsDir` field in the session file being migrated (e.g. `- **E2E tests dir:** /c/dev/vo-playwright-tests`)
2. `paths.e2eTestsDir` in `~/.claude/plugins/user-config.json`
3. `paths.voPlaywrightTestsDir` in `~/.claude/plugins/user-config.json` (VO legacy key)

If no E2E tests dir found, skip this step silently.

If found, check `<e2eTestsDir>/tasks/`. If absent or empty, skip with note: "No task files found in `<e2eTestsDir>/tasks/` — skipping Playwright migration."

**Copy task files:**

1. Create `<repo_root>/.claude/playwright/tasks/`.

2. For each `*.ts` file in `<e2eTestsDir>/tasks/`, apply the PII scan before copying:
   - Task files often contain member IDs and spoofed identity comments (e.g. `TH_MEMBER = '4169062'`). Flag name↔memberId pairings as PII.
   - Recommend `scrub` (replace with `<test-member-id>` placeholder) unless the user explicitly keeps them.
   - Apply exclude/scrub/keep dispositions, then copy to `<repo_root>/.claude/playwright/tasks/<name>.ts`.

**Update the runner:**

Rewrite `<e2eTestsDir>/scripts/run-checks.ts` — replace the block of `import '../tasks/<name>'` lines with imports pointing to the repo path. Use `git rev-parse --show-toplevel` (run from `<e2eTestsDir>`) to resolve `<repoRoot>`.

Replace each `import '../tasks/<name>'` with `import '<repoRoot>/.claude/playwright/tasks/<name>'`.

If the runner uses a dynamic glob import over `tasks/*.ts`, update the glob path to `<repoRoot>/.claude/playwright/tasks/*.ts` instead.

**Write `.e2e.json`:**

Read `<e2eTestsDir>/.e2e.json` if it exists, otherwise start with `{}`. Merge in the `tasksDir` key and write back:
```json
{ "tabs": [...existing tabs if any...], "tasksDir": "<repoRoot>/.claude/playwright/tasks" }
```

**Update user-config.json:**

If `paths.e2eTestsDir` is not already set in `~/.claude/plugins/user-config.json`, write it:
```json
"paths": {
  "e2eTestsDir": "<e2eTestsDir absolute path>"
}
```
This makes the path available for future migrates on other repos without re-prompting.

### 12. Confirm and Commit

Show a summary:
```
Ready to commit:
  .claude/sessions/          — N session file(s), transformed (Next steps array, created-by/updated-by, @handle tags, path cleanup)
  .claude/sessions/_index.md — N sessions indexed (name | @created-by | @updated-by | date | status | title)
  .claude/sessions/_history.md — N entries tagged @<handle>
  .claude/sessions/.gitignore  — includes *.approved-hash exclusion
  .gitignore                 — added .claude/config/ exclusion
  .claude/memory/            — J memory file(s) added (K skipped — already present), feature labels applied
  .claude/memory/MEMORY.md   — index regenerated (N entries)
  .claude/playwright/tasks/  — N task file(s) copied from <e2eTestsDir>/tasks/   ← omit if Step 11c skipped
  (no .claude/CLAUDE.md — project memory loads on demand via the memory plugin, never auto-loaded)

Local only (not committed):
  ~/.claude/memory/sessions/<slug>/<name>.approved-hash — N files seeded
  ~/.claude/projects/<encoded>/memory/.migrated-to-repo — sentinel written
  .git/hooks/pre-commit — session-commit-guard shim installed (delegates to live plugin; auto-updates)
  <e2eTestsDir>/scripts/run-checks.ts — imports updated to repo path   ← omit if Step 11c skipped
  <e2eTestsDir>/.e2e.json — tasksDir written   ← omit if Step 11c skipped
  ~/.claude/plugins/user-config.json — paths.e2eTestsDir set   ← omit if already present

Commit and push? (Yes / Edit message / Cancel)
```

Omit the `.claude/memory/` lines if Step 11b was skipped.

Default commit message: `chore: add Claude Code session files and project memory (.claude/)`

- **Yes:** stage `.claude/sessions/`, `.claude/memory/`, and `.gitignore` changes, commit, push.
- **Edit message:** ask for preferred message, then commit and push.
- **Cancel:** leave files in place but do not commit. User can commit manually.

### 13. Confirm Completion

```
Migrated — session files and project memory are now repo-based.

  Local backup:  ~/.claude/memory/sessions/<slug>/  (preserved, no longer updated)
  Repo sessions:    <repo_root>/.claude/sessions/
  Repo memory:      <repo_root>/.claude/memory/  (N files)
  Repo tasks:       <repo_root>/.claude/playwright/tasks/  (N files)   ← omit if Step 11c skipped
  Local memory:     ~/.claude/projects/<encoded>/memory/  (preserved as fallback — sentinel written)
  Local config:  ~/.claude/config/<slug>.json

Going forward all session reads and writes use .claude/sessions/.
Project memory lives in .claude/memory/ and loads ONLY on demand via the memory plugin
(/memory:load, :scan, :review) — nothing auto-loads, no .claude/CLAUDE.md import.
A developer who opens this repo without invoking a plugin command inherits zero context
overhead — the files are inert until a command reads them.
To revert memory: delete .claude/memory/ — the memory plugin falls back to local memory automatically.
New developers who pull this repo will be prompted for their local path on first session start.
```

Omit the Repo memory / Local memory lines if Step 11b was skipped.

---

## --force Re-sync

Same steps 5–11, but:
- `.claude/sessions/` already exists — **overwrite** all files.
- Skip the confirm in step 3 (no "Already migrated" guard).
- Commit message: `chore: re-sync Claude Code session files from local`
