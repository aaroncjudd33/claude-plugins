---
name: switch
description: Switch to a different session without the full session:start overhead. Use mid-day to pivot between sessions.
---

# Session Switch

Lightweight context swap for mid-day pivots between sessions. Skips permission mode, teams chat setup, and routing branches — just loads the target session and goes.

## Instructions

### 1. Derive Repo Slug

Run `pwd` and extract the last path component as the repo slug. Resolve `session_root` and `handle` using Path Resolution (see Session Skill).

### 2. Load Session List

Run **three calls in parallel:**
1. `ls -lt <session_root>/` — extract session names from `.md` filenames, skipping `_*` files. Use file modification date as sort key and display date.
2. Inbox/outbox counts (batch shell loop):
   ```bash
   find "<session_root>" -maxdepth 1 -name '_inbox*.md' 2>/dev/null | while read -r f; do echo "=== FILE: $f ==="; cat "$f"; done
   ```
   Count logical items per named inbox file (lines beginning with `[20` or `## `). Also check `_outbox_<name>.md` files for outbox counts.
3. **Read `<session_root>/_index.md`** — handle, status, and title data for all sessions.

**If `_index.md` is absent or missing entries:** read the affected session `.md` files in parallel to extract `updated-by:`, `created-by:`, `updated:` date, `Status:`, `Title:`. Write `_index.md` now. Show: "`_index.md` built from N session files." Do NOT degrade to `@—` — always build before displaying.

If an argument was passed to the command:
- Argument is `mine`: set `filter_mine = true`, show filtered list — do not skip to step 3.
- Any other argument (e.g. `/session:switch release`): skip the list and jump directly to step 3 with that name.

If `filter_mine`, filter the session list to those where `@created-by` or `@updated-by` from `_index.md` matches `@<handle>`.

Otherwise, print the numbered list and wait for selection. Use the same grouped format as session:start (section headers per status group, column header once at top, fixed column widths, up to 10 total with active sessions prioritized):

```
Sessions in <slug>

  #    name          title                             status         in    last edit

  In Progress
  [1]  BPT2-6377     Shopify Member Agreement Pro...   in-progress     1     @ajudd Jun 09
  [2]  session       —                                 in-progress     0     @nivi  Jun 11

  2 in-progress · 0 paused · 8 completed

  Start / Resume:
    <n>              — switch to session by number

  Search by:
    mine             — show only your sessions
    all              — include completed sessions
    full             — show all columns (adds out count + created date)
    status <value>   — filter by in-progress / paused / completed
    <text>           — search name or title, or describe a filter (e.g. "has inbox", "updated by nivi")
```

**Title truncation:** cap title at 32 characters. If longer, truncate and append `...`. If title is `—` (absent), show `—` with no padding.

**Default columns:** `# · name · title · status · in · last edit`. The `out` count and `created` date are hidden by default — on `full`, add `@creator created-date` in a "created" column and the `out` count. Always show the `in` count (`0` — never omit). `@updater updated-date` is the "last edit" column. Omit a status group entirely if it has no sessions. Mark active session with `←` at end of row.

### 3. Display Resume Block

**Run these three reads in parallel:**

Read `<session_root>/<name>.md`.
Read `<session_root>/_history.md` — count total entries and extract the most recent one.
Read the inbox file (`_inbox_<name>.md` for plugins, `_inbox.md` otherwise — from `session_root`) and collect all items (in-progress and pending).

**Security check (repo sessions only):** If `session_root` is inside a repo, run the approval-hash check using the same flow as `session:start` Step 4 — compute SHA-256, compare to `~/.claude/memory/sessions/<slug>/<name>.approved-hash`, handle missing/matching/differing cases with first-time review, normal load, or diff-review flow. See `references/skill-repo-security.md` for the full procedure.

Display:

```
Switching to <name>
  Branch:      [branch]
  Mode:        planning          ← show ONLY when Mode is planning; omit for coding/both/absent
  Open items (mine, N):
    - [date @handle] item
  Teammate notes (N — read-only):
    - [date @other] item
  Inbox (N):
    [1] [date] <description> — in-progress / pending
  Next steps (mine, N):
    - [date @handle] next step
  History:     N entries — last: [condensed one-liner of most recent entry]
```

If inbox is empty: `Inbox: none`. If no history: `History: none`. Omit Teammate sections if no teammate items exist. Old scalar `Next step: <text>` treated as mine.

### 4. Check Inbox

For all sessions: check `<session_root>/_inbox_<name>.md`.

If the inbox file has content beyond the header, first scan for in-progress items, then handle pending items.

If the inbox file has content beyond the header, gather all items and present as a batched block. **Do not use AskUserQuestion.** Output and wait for one reply (Pattern 2):

```
  (1) Inbox [in-progress]: "<description>"    keep / done
  (2) Inbox: "<description>"    work / done / backlog / keep

Reply with overrides or "go".
```

"go" accepts all defaults. Parse freely: `1 done`, `2 work`, `1 done 2 work`, etc.

- **done** (in-progress): strip `[in-progress — ...]`, archive with `[DONE YYYY-MM-DD]` to `_inbox_<name>_archive.md`, remove from inbox, remove `[inbox] <item>` from Open items.
- **keep** (in-progress): no change.
- **work** (pending): insert `[in-progress — <session-name>, YYYY-MM-DD]` after `## [date]...` header. Do NOT archive. Add `[inbox] <item>` to Open items.
- **done** (pending): archive with `[DONE YYYY-MM-DD]`, remove from inbox.
- **backlog**: move to `_backlog_<name>.md` (plugin) or `_backlog.md` (others), remove from inbox.
- **keep** (pending): leave as-is. Do not add to Open items.

Auto-purge archive entries with `[DONE]` dates older than 30 days after handling.

For plugin sessions, also check `~/.claude/memory/sessions/<slug>/_inbox.md` for global items. Display only — never auto-cleared.

### 5. Write _active and Update Session File

Write `~/.claude/memory/sessions/<slug>/_active` with the new session name (always local — plain text, no `.md`).

Update `<session_root>/<name>.md`: set `updated` to today, set `updated-by: @<handle>`, and preserve `created-by:` as-is (never overwrite). Tag any untagged Open items or Next steps items with `[today @<handle>]`.

**After writing — update approved-hash (repo sessions only):** Recompute and overwrite `~/.claude/memory/sessions/<slug>/<name>.approved-hash`:
```bash
python3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "<session_root>/<name>.md" > ~/.claude/memory/sessions/<slug>/<name>.approved-hash
```

**Update `_index.md`:** Read `<session_root>/_index.md` — create with header if not exists. Find the line for `<name>`: extract `@created-by` (col 2) and `created-date` (col 3) to preserve; if no existing line, use `@<handle>` and `<today>`. Replace or append: `<name> | @<created-by> | <created-date> | @<handle> | <today> | <status> | <title-or-dash>`. Where `<status>` = the session's current `Status:` field.

**Note:** `switch` is not a save point — it does not write a `_history.md` entry or create a checkpoint. If you worked on the previous session before switching, run `/session:checkpoint` or `/session:commit` first so that work is captured.

Done — proceed with the work.
