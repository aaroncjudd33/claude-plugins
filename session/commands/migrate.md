---
name: migrate
description: One-time migration — move session files AND project memories from local ~/.claude into the repo under .claude/ so they are git-tracked and shared across developers.
argument-hint: "[--force] [--vetted]"
---

# Session Migrate

Move **the current repo's** session files from local memory into the git repo under `.claude/sessions/`. Run this from within any session on any repo — it uses `pwd` to determine which repo to migrate. After migration all session reads and writes use the repo path. Local files are preserved as a backup but no longer updated.

Run once per project. Use `--force` to re-sync local → repo if repo sessions get corrupted. Use `--vetted` to skip the two reasoning-heavy steps (secrets/PII scan in Step 5a, feature-label walkthrough in Step 11b's 2a) when the content has already been reviewed — the flag is the confirmation, no extra prompt, same precedent as `--force`.

**`--vetted` scope — say what it does and doesn't cover (acp-ajudd#146 follow-up).** `--vetted` means "I am personally certifying every file in this migration set is already clean — skip re-checking it." It does **not** mean the content has been scanned and found clean by this tool; it means the scan is being skipped on your word. Two things this does not cover, so print them once, right where the skip is reported, not buried in docs:
1. **It doesn't override the harness's own independent safety classifier.** Claude Code can still flag/block on content it judges sensitive regardless of `--vetted` — that's a separate layer this flag has no authority over.
2. **It never retroactively cleans anything, in either direction.** If content turns out not to be clean, `--vetted` didn't create the problem and re-running without it doesn't erase history already written — it only controls whether *this run's* scan happens.
When printing the skip line in the progress checklist, use: `✨ Secrets/PII scan skipped (--vetted — asserted clean, not verified clean)` instead of the bare "skipped (--vetted)" — the parenthetical is the point.

**Print progress as you go — one line per major step, not silence until the end (acp-ajudd#145).** This command has enough sequential steps (secrets scan, session copy, history copy, inbox copy, memory copy, labeling, `MEMORY.md` regen, commit) that a user watching it run has no way to tell "still working" from "stuck" without per-step feedback. After each major step below completes, print one line before moving to the next:
```
✨ Secrets/PII scan complete — N file(s) flagged  ← or "skipped (--vetted — asserted clean, not verified clean)"
✨ Session files copied — N file(s)
✨ History + inbox/backlog copied
✨ Project memory copied — N file(s) added, K skipped
✨ Feature labels applied  ← or "skipped (--vetted)"
✨ MEMORY.md regenerated
✨ Committed and pushed
```
This is in addition to, not instead of, each step's own existing output (the batch confirmations, the final summary) — it's a lightweight running progress marker so silence never gets mistaken for a hang. **This is a hard turn boundary per line** (acp-ajudd#146 follow-up) — print the line for a completed step before starting the next tool call, do not batch multiple steps silently into one turn.

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
- **`--vetted` flag present:** note it for Steps 5a and 11b's label walkthrough (both skip below) — the flag itself is the user's explicit assertion that this content was already reviewed; no separate confirmation prompt (same precedent as `--force`).

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

Check `~/.claude/memory/sessions/<slug>/`. List all `.md` files not starting with `_`. **Exclude `refinement-*.md`** — refine no longer creates session files (the record it produces is the WIP store), but any leftover legacy `refinement-*.md` from the old model must still never be migrated into the repo.

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

Write `<repo_root>/.claude/sessions/.gitignore` **exactly as below** — each pattern on its own line with **no inline `#` comment** (a `#` only starts a comment at the start of a line; a trailing `_context_*  # note` is parsed as a literal pattern and silently ignores nothing):
```gitignore
# Per-user state — never commit
_active
# _context_*: per-user pre-clear / planning-resume stash (store + handoff) — always local
_context_*
*.approved-hash

# Derived caches — rebuilt locally, never committed
# _history.md: local worklog glimpse; duplicates the global worklog at ~/.claude/memory/worklog/
_history.md
# _index.md: listing render cache — session-list.py rebuilds it from the committed <name>.md files
_index.md
```

**Only per-ticket `<name>.md` state files, the inbox/backlog records, and `.gitignore` are committed** — the derived caches (`_history.md`, `_index.md`) and the local stashes (`_active`, `_context_*`, `*.approved-hash`) are all gitignored (acp-ajudd#48/#49). The committed session set stays source-of-truth only; everything derivable regenerates locally.

Add to repo root `.gitignore` if `.claude/config/` is not already excluded:
```gitignore
.claude/config/
```

### 5. Read Handle

Read `handle` from `~/.claude/plugins/user-config.json` (`user.handle`). If absent, derive from `user.email` prefix.

### 5a. Pre-Migration Secrets & PII Scan (BLOCKING)

**Skip this entire step if `--vetted` was passed.** Print `✓ Secrets/PII scan complete — skipped (--vetted)` and proceed directly to Step 6. `--vetted` asserts the user has already reviewed this content (e.g. re-migrating the same local files after a stranded-branch situation where they were scanned once already) — the flag itself is the confirmation, same as `--force` needs no separate prompt. This is a real trade: the PII/secrets safety net is off for this run, which is why it requires the explicit flag rather than being a default.

**Otherwise, before copying anything into the repo, scan every candidate file for secrets and PII.** Migration git-tracks these files permanently — a credential committed here lives in the git history forever, even if removed later. The pre-commit guard (`session-commit-guard.py`) is the backstop, but catch it here first, where files can be excluded or scrubbed cleanly before they ever enter the tree.

**Scan the full content of every file about to be migrated** — session `.md` files, `_history.md`, all top-level `_inbox*.md`, every per-item `_inbox/*.md` (acp-ajudd#102), and the project memory files from Step 11b. (`_context_*.md` pre-clear dumps are **never migrated** — they are always-local personal stashes, out of migrate scope entirely — so they never need scanning here.)

Flag:
- **Secrets / credentials** — DB connection strings with passwords (e.g. `user/PASS@host:port`), `password=`/`pwd:` assignments, API keys, `AKIA…` AWS keys, JWTs, `-----BEGIN … PRIVATE KEY-----`. (Same patterns as `SECRET_PATTERNS` in the commit guard.)
- **PII** — real person name ↔ member/custid pairings, `fedTaxNum`/`ssn`/`taxId` fields, addresses tied to a named individual. PII detection is fuzzy — surface anything plausible for the user to judge.

For each flagged file, present a per-file disposition (never silent, never auto-decide):
```
⚠️  Secrets / PII found in files staged for migration:

  _history.md
    [secret] db-connection-credentials — cmsuser/…@oracln.yleo.us:1521  (×2)
    [PII] name↔custid — "Edie Wadsworth / 1443424"
  BPT2-5558.md
    [PII] name↔custid — "Edie Wadsworth / 1443424"

Handle each before migrating:
  exclude <file>   — don't copy it into the repo at all (safest for pure-secret files)
  scrub <file>     — copy it but redact the flagged values (placeholders: <REDACTED>, <test-member>)
  keep <file>      — migrate as-is (NOT recommended — secrets/PII enter git history permanently)

Reply per file, e.g. "scrub _history.md BPT2-5558.md".
```

Apply before the copy steps:
- **exclude:** drop the file from the migration set entirely — skip it in Steps 6/8/9/11b. Note it in the final summary as "excluded (secrets/PII)". The local original is untouched — `exclude` means "stay local-only," not "also clean the local copy."
- **scrub:** copy it, but replace each flagged value with a placeholder (`<REDACTED>` for secrets, `<test-member>` / `<custid>` for PII) during the transform. Preserve surrounding context. **Also apply the same redaction to the local source file in place, in this step** (acp-ajudd#146 follow-up) — not just the repo-bound copy. Without this, the unredacted value keeps living in `~/.claude/memory/sessions/<slug>/<name>.md` forever and re-surfaces on every future `--force`/re-migrate of this slug, which is exactly the confusing "I thought we already vetted this" loop this note exists to close. Report both writes: `scrubbed <name>.md (repo copy + local original)`.
- **keep:** migrate unchanged — only on explicit per-file confirmation; warn once more that it lands in git history. Local original untouched (nothing to clean — user explicitly chose to keep the value).

**Default bias:** recommend `exclude` for any file whose value is purely a secret (e.g. a credentials dump); recommend `scrub` for session/history files that carry real record but happen to name a person. Do not proceed to Step 6 until every flagged file has a disposition.

**Why "vetted" alone can't guarantee a clean local tree:** this step is the *only* layer that ever inspects the content of a regular session `.md` file for PII (`/session:store`'s scan only covers `_context_*.md` pre-clear stashes — see the Secrets/PII Defense design). A file that was never scrubbed here — because an earlier migrate run used `--vetted`, or because it was written/edited after the last scan — carries no record of having been checked. "We went through it before" is only true for files that were actually scrubbed *here*, not for the local tree as a whole. If PII turns up on a `--vetted` run, that's this step being skipped as instructed, not a bug — the fix is to re-run without `--vetted` at least once per file that's never been through this scan.

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

**This copy seeds the LOCAL working-tree `_history.md` — it is gitignored (Step 4) and never committed (acp-ajudd#49).** `_history.md` is a per-user worklog glimpse (it duplicates the global worklog at `~/.claude/memory/worklog/`); copying it here just carries the pre-migration glimpse forward on this machine. It stays local — the commit in Step 12 does not include it.

### 8. Copy and Tag Inbox / Backlog Files

**The consolidated inbox is a per-item dir (acp-ajudd#102).** Copy the whole `_inbox/` directory — every `_inbox/*.md` item file — to `<repo_root>/.claude/sessions/_inbox/`. These per-item files are shared work records and commit like the old `_inbox.md` did. (A legacy single `_inbox.md`, if one is still present pre-migration, is copied too; the lazy auto-migration in `inbox-render.py` will split it into the dir on first access in the new location.)

For each file matching `_inbox*.md`, `_backlog*.md` at the top level of `~/.claude/memory/sessions/<slug>/`, AND each `_inbox/*.md` item file:

1. Copy to `<repo_root>/.claude/sessions/` (item files → `<repo_root>/.claude/sessions/_inbox/`).
2. For each entry header line matching `## [YYYY-MM-DD] from` (no handle present):
   - Rewrite as `## [YYYY-MM-DD @<handle>] from`

### 9. Copy Archive and Work Files

Copy as-is (no handle tagging needed):
- `_inbox_*_archive.md`
- `_backlog_*_archive.md` (if any)
- `_work_*.md` (work notes created during inbox processing — carry the decisions forward)

Do **not** copy:
- `_active` — per-user hint, excluded by `.gitignore`
- `_context_*.md` — pre-clear restore stashes are **always local, ephemeral, personal** (treated like `_active`): never migrated, never committed. Any present are left behind, excluded by `.gitignore`.

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

**`_index.md` is a LOCAL render cache — gitignored (Step 4), never committed (acp-ajudd#49).** Building it here just warms the cache so the first post-migrate `/session:start` is fast; it is fully derivable from the committed `<name>.md` files and `session-list.py` rebuilds it on any machine when absent. The commit in Step 12 does not include it.

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

**User-specific memory scan (informational — all files migrate):**

After migrate commits, the local memory directory is tombstoned (see Step 12a). Files left behind there will not be auto-loaded again — they become inaccessible. For this reason, **everything migrates**. There is no EXCLUDE option.

Before the PII scan, identify files that look personal so the user knows what is going in:

Auto-flag as user-specific:
- Any file matching `user_*.md` (e.g. `user_timezone.md`, `user_team_heber.md`)
- Any file whose `description:` frontmatter contains first-person language ("my", "I") or personal identifiers

If any are found, surface as an informational note only — they still proceed to the PII scan and are migrated like every other file:
```
ℹ️  These files look personal to this developer — they will be migrated and PII-scrubbed:

  user_team_heber.md   — "Heber Iraheta — manager/lead, default approver"
  user_timezone.md     — "User's timezone — Eastern time, convert for Jira/CAB"

(They go in like everything else — the local copy is wiped after commit.)
```

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
   **Apply the Step 5a secrets/PII scan to these files too** (if 11b runs standalone via the guard path and 5a did not execute, run the scan here against the memory files before copying). Honor exclude/scrub/keep dispositions. **Skip this scan if `--vetted` was passed** — same as Step 5a, the flag already covers these files.
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

2a. **Label walk-through** — apply the memory plugin's feature-label convention to every file being added. **Skip this entire sub-step if `--vetted` was passed** — print `✓ Feature labels applied — skipped (--vetted)` and leave all files unlabeled; they remain findable by description and can be labeled later via `/memory:groom` or a manual relabel pass. Otherwise: read `~/.claude/plugins/marketplaces/<pluginMarketplaceName>/memory/skills/memory/references/label-convention.md` first (derive `pluginMarketplaceName` from `~/.claude/plugins/user-config.json`). If the memory plugin is not installed, skip this sub-step silently and leave files unlabeled.

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

1. Create `<repo_root>/.claude/playwright/` if it does not exist.

2. For each `*.ts` file in `<e2eTestsDir>/tasks/`, apply the PII scan before copying:
   - Task files often contain member IDs and spoofed identity comments (e.g. `TH_MEMBER = '4169062'`). Flag name↔memberId pairings as PII.
   - Recommend `scrub` (replace with `<test-member-id>` placeholder) unless the user explicitly keeps them.
   - Apply exclude/scrub/keep dispositions, then copy to `<repo_root>/.claude/playwright/<name>.ts`.

**Update the runner:**

Rewrite `<e2eTestsDir>/scripts/run-checks.ts` — replace the block of `import '../tasks/<name>'` lines with imports pointing to the repo path. Use `git rev-parse --show-toplevel` (run from `<e2eTestsDir>`) to resolve `<repoRoot>`.

Replace each `import '../tasks/<name>'` with `import '<repoRoot>/.claude/playwright/<name>'`.

If the runner uses a dynamic glob import over `tasks/*.ts`, update the glob path to `<repoRoot>/.claude/playwright/*.ts` instead.

**Write `.e2e.json`:**

Read `<e2eTestsDir>/.e2e.json` if it exists, otherwise start with `{}`. Merge in the `tasksDir` key and write back:
```json
{ "tabs": [...existing tabs if any...], "tasksDir": "<repoRoot>/.claude/playwright" }
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
  .claude/sessions/_inbox/ — per-item inbox files (shared work records — acp-ajudd#102)
  .claude/sessions/_inbox*.md / _backlog*.md — archive + backlog records (shared work records)
  .claude/sessions/.gitignore  — excludes _active, _context_*, *.approved-hash, _history.md, _index.md
  .gitignore                 — added .claude/config/ exclusion
  .claude/memory/            — J memory file(s) added (K skipped — already present), feature labels applied
  .claude/memory/MEMORY.md   — index regenerated (N entries)
  .claude/playwright/        — N task file(s) copied from <e2eTestsDir>/tasks/   ← omit if Step 11c skipped
  (no .claude/CLAUDE.md — project memory loads on demand via the memory plugin, never auto-loaded)

Local only (not committed):
  .claude/sessions/_history.md — seeded in working tree, gitignored (derived cache — acp-ajudd#49)
  .claude/sessions/_index.md   — render cache warmed, gitignored (rebuilds from session files — acp-ajudd#49)
  ~/.claude/memory/sessions/<slug>/<name>.approved-hash — N files seeded
  ~/.claude/projects/<encoded>/memory/.migrated-to-repo — sentinel written
  .git/hooks/pre-commit — session-commit-guard shim installed (delegates to live plugin; auto-updates)
  <e2eTestsDir>/scripts/run-checks.ts — imports updated to repo path   ← omit if Step 11c skipped
  <e2eTestsDir>/.e2e.json — tasksDir written   ← omit if Step 11c skipped
  ~/.claude/plugins/user-config.json — paths.e2eTestsDir set   ← omit if already present

Commit and push? (Yes / Edit message / Cancel)
```

**Staging note (acp-ajudd#49):** stage `.claude/sessions/` as a directory — the `.gitignore` written in Step 4 keeps `_history.md`, `_index.md`, `_active`, `_context_*`, and `*.approved-hash` out of the commit automatically, so only the `<name>.md` state files, `_inbox*`/`_backlog*` records, and `.gitignore` land. Do not hand-stage the derived caches.

Omit the `.claude/memory/` lines if Step 11b was skipped.

Default commit message: `chore: add Claude Code session files and project memory (.claude/)`

- **Yes:** stage `.claude/sessions/`, `.claude/memory/`, and `.gitignore` changes, commit, push. → proceed to Step 12a.
- **Edit message:** ask for preferred message, then commit and push. → proceed to Step 12a.
- **Cancel:** leave files in place but do not commit. User can commit manually. **Do not run Step 12a** — do not tombstone until the commit has actually happened.

### 12a. Tombstone Local Memory (runs only after successful commit)

The local project memory at `~/.claude/projects/<encoded>/memory/` is auto-loaded by Claude Code in every conversation. After migrate, that context should come from the repo only — on demand, not automatically. Tombstone the local directory so the auto-loader gets nothing.

**Verify first:** confirm `<repo_root>/.claude/memory/MEMORY.md` exists and has at least one `- [` entry. If the repo copy looks empty or missing, stop — do not touch local. Report: "Repo memory looks empty — skipping tombstone. Check .claude/memory/ before manually running cleanup."

**On success — one operation only:**

Overwrite `~/.claude/projects/<encoded>/memory/MEMORY.md` with a tombstone:
```
# Migrated — do not use
Project memories for this repo have been migrated to the git repository.
Repo path: <repo_root>/.claude/memory/
Migrated: <today>
All reads and writes now go to the repo path. This index is intentionally empty.
```

Claude Code's auto-loader reads this index and finds no `- [name](file.md)` entries — nothing auto-loads. The individual `.md` files **stay in place** so the directory remains a valid source for a future re-run or `--force` sync.

**Do NOT delete the individual `.md` files.** Keeping them enables:
- Re-running migrate on a second branch (migrate scans the directory, not MEMORY.md, so it finds the files)
- Two branches migrating in parallel — each picks up from local, commits to their branch's `.claude/memory/`, and the two branches merge additively to master

**Going forward:**
- Reads: memory plugin resolves `.claude/memory/` in the repo — on demand only, never automatic
- Writes: memory plugin writes to `.claude/memory/` — local MEMORY.md index is inert
- Fresh clone (no local config yet): developer runs `/session:migrate` once to seed their `~/.claude/config/<slug>.json`; memories load on demand from that point

### 13. Confirm Completion

```
Migrated — session files and project memory are now repo-based.

  Repo sessions: <repo_root>/.claude/sessions/  (N files)
  Repo memory:   <repo_root>/.claude/memory/  (N files)   ← omit if Step 11b skipped
  Repo tasks:    <repo_root>/.claude/playwright/  (N files)   ← omit if Step 11c skipped
  Local memory:  ~/.claude/projects/<encoded>/memory/  — TOMBSTONED (auto-load disabled)
  Local config:  ~/.claude/config/<slug>.json

Going forward:
  Sessions — all reads and writes use .claude/sessions/ exclusively.
  Memory — loads ONLY on demand via the memory plugin (/memory:load, :scan, :review).
    Nothing auto-loads. No .claude/CLAUDE.md import. Zero context overhead on repo open.
    Local project memory directory has been tombstoned — it will not be read or written.
  Playwright tasks — new tasks written to .claude/playwright/tasks/ (e2e skill auto-detects).

New developers who pull this repo run /session:migrate once to seed their local config.
To revert: delete .claude/ from the repo. Claude falls back to a fresh local state.
```

Omit the Repo memory / Local memory lines if Step 11b was skipped.

---

## --force Re-sync

Same steps 5–11, but:
- `.claude/sessions/` already exists — **overwrite** all files.
- Skip the confirm in step 3 (no "Already migrated" guard).
- Commit message: `chore: re-sync Claude Code session files from local`
