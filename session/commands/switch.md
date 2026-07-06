---
name: switch
description: Switch to a different session without the full session:start overhead. Use mid-day to pivot between sessions.
---

# Session Switch

Lightweight context swap for mid-day pivots between sessions. Skips permission mode, teams chat setup, and routing branches — just loads the target session and goes.

## Instructions

### 1. Derive Repo Slug

Run `pwd` and extract the last path component as the repo slug. Resolve `session_root` and `handle` using Path Resolution (see Session Skill).

**Session guard (command-level enforcement — acp-ajudd#1).** `switch` moves focus between existing sessions, so at least one session must exist for the slug. If `session_root` holds no session `.md` files (only `_`-prefixed infra files, or the directory is absent), **stop cleanly** — there is nothing to switch to:

```
No session established for <slug>. Run /session:start first.
```

Editing files is never blocked; the session commands are what require a session. (`start` / `refine` and read-only views are exempt.)

### 2. Load Session List

**Argument handling first:**
- arg `mine` → render the filtered list (pass `--mine` below).
- any other arg (e.g. `/session:switch release`) → skip the list, jump directly to Step 3 with that name.

**Render the listing — run the helper script and display its stdout verbatim** (same renderer as session:start):
```bash
SL="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}/scripts/session-list.py"
if command -v python3 >/dev/null 2>&1 && [ -f "$SL" ]; then
  python3 "$SL" --session-root "<session_root>" --slug "<slug>" --handle "<handle>"   # add --mine when arg is mine
fi
```
The script reads `_index.md` (7-col current / 6-col legacy), the per-session inbox files (`_inbox_<name>.md`, archives excluded), the `_active` marker, and the session `.md` filenames, and prints the finished, aligned, grouped table (default columns; completed + `refinement-*` hidden, active marked `←`). **Echo its stdout exactly — do not re-align or restate.** Then append the routing block:

```
  Start / Resume:
    <n>              — switch to session by number

  Search by:
    mine             — show only your sessions
    all              — include completed sessions
    full             — show all columns (adds out count + created date)
    status <value>   — filter by in-progress / paused / completed
    <text>           — search name or title, or describe a filter (e.g. "has inbox", "updated by nivi")
```

**Filter flags** — re-run the script with the matching flag, re-display, and re-append the routing block: `full`→`--full` · `all`→`--show all` · `status <value>`→`--status <value>` · `mine`→`--mine`. **Free-text** natural-language filters: read `_index.md` yourself and render the subset inline.

**Index rebuild (switch builds eagerly):** if the script output ends with `(index missing or incomplete …)`, read the affected session `.md` files in parallel, extract `updated-by:`/`created-by:`/`updated:`/`Status:`/`Title:`, write `_index.md` in 7-column format, then re-run the script — do not present a degraded table.

**Fallback (script unavailable):** if `python3` is absent, the script exits non-zero, or stdout is empty, render the list yourself — group by status, one row per session `# · name · title (≤32, "..." if longer) · status · in · @updater date` (add `out` + `@creator created-date` only on `full`), mark `_active` with `←`, end with `N in-progress · N paused · N completed`.

Then wait for selection.

### 3. Display Resume Block

**Run these three reads in parallel:**

Read `<session_root>/<name>.md`.
Read `<session_root>/_history.md` — count total entries and extract the most recent one.
Read the inbox file **fresh (acp-ajudd#6)** — **plugin / personal → the canonical `<session_root>/_inbox.md`** (item-driven; there is no per-session `_inbox_<name>.md`); **story / cab / general → `<session_root>/_inbox_<name>.md`** — and collect all items (in-progress and pending). Count **by `## <id>` header lines** and **skip the `> [type: … · status: …]` metadata line** under each (v1.57.0 item metadata — never miscount it). **Split by `type`:** only `type: story` items are inbox work (listed + swept in Step 4); `type: note` / `type: data` items with `status: new` are **mailbox** items (acp-ajudd#10) — count them for the Messages line, never list or sweep them as pickable.

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
  Inbox (N):          ← layout B; provenance dim below each item (see inbox-convention.md); type: story only
    [1] <description> — in-progress / pending
        ↳ <slug> / <session> (<type>) · MM-DD
  Messages: N waiting (note/data) — say "check messages" to read them   ← omit line if none; mailbox glance (acp-ajudd#10)
  Next steps (mine, N):
    - [date @handle] next step
  History:     N entries — last: [condensed one-liner of most recent entry]
```

If inbox is empty: `Inbox: none`. If no history: `History: none`. Omit Teammate sections if no teammate items exist. Old scalar `Next step: <text>` treated as mine.

### 4. Check Inbox

Check the same fresh inbox read from Step 3 — **plugin / personal → the canonical `<session_root>/_inbox.md`**; **story / cab / general → `<session_root>/_inbox_<name>.md`**. (Do not fall back to a per-session file for item-driven types — it does not exist for them.) **This batch handles `type: story` items only** — `type: note` / `type: data` mailbox items are excluded (they surfaced as the Messages line in Step 3 and are read/archived only on request, per `references/inbox-convention.md` § Mailbox).

If the inbox file has content beyond the header, first scan for in-progress items, then handle pending items.

If the inbox file has content beyond the header, gather all items and present as a batched block. **Do not use AskUserQuestion.** Output and wait for one reply (Pattern 2):

```
  (1) [<id>] Inbox [in-progress]: "<description>"    keep / done
  (2) [<id>] Inbox: "<description>"    work / done / backlog / keep

Reply with overrides or "go".
```
(Lead with the item's stable `[<id>]`; omit for legacy items that have none.)

"go" accepts all defaults. Parse freely: `1 done`, `2 work`, `1 done 2 work`, etc.

- **done** (in-progress): strip `[in-progress — ...]`, archive with `[DONE YYYY-MM-DD]` (archive file is type-aware: `_inbox_archive.md` for plugin / personal, `_inbox_<name>_archive.md` for story / cab / general), remove from inbox, remove `[inbox] <item>` from Open items.
- **keep** (in-progress): no change.
- **work** (pending): insert `[in-progress — <session-name>, YYYY-MM-DD]` after `## [date]...` header. Do NOT archive. Add `[inbox] <item>` to Open items.
- **done** (pending): archive with `[DONE YYYY-MM-DD]`, remove from inbox.
- **backlog**: move to `_backlog_<name>.md` (plugin) or `_backlog.md` (others), remove from inbox.
- **keep** (pending): leave as-is. Do not add to Open items.

Auto-purge archive entries with `[DONE]` dates older than 30 days after handling.

For **story / cab / general** sessions, also check `~/.claude/memory/sessions/<slug>/_inbox.md` for global (undirected) items. Display only — never auto-cleared. (Plugin / personal already read `_inbox.md` as their primary inbox above — there is no separate global file for them.)

### 5. Write _active and Update Session File

Write `~/.claude/memory/sessions/<slug>/_active` with the new session name (always local — plain text, no `.md`).

Update `<session_root>/<name>.md`: set `updated` to today, set `updated-by: @<handle>`, and preserve `created-by:` as-is (never overwrite). Tag any untagged Open items or Next steps items with `[today @<handle>]`.

**Preserve frontmatter keys.** For `plugin` / `personal` sessions, the frontmatter carries `type:`, `mode:`, and `status:` — these gate the scope guard. When updating `updated:`, leave `type:`/`mode:`/`status:` intact (do not strip them). If the session file has no frontmatter `mode:` yet (older file), add `type:`/`mode:`/`status:` to match the body bullets while you're writing.

**Mode modifier (optional).** If the switch argument included a mode (`planning` / `coding` / `both` — e.g. `/session:switch release planning`), apply it now: update both the frontmatter `mode:` key and the `- **Mode:**` body bullet, and note `Mode changed to <new>`. Mode is a soft convention (acp-ajudd#1 removed edit-blocking — no hook reads it): switching into a `planning` session signals "scope, don't build," while `coding` signals normal build work. Nothing hard-blocks edits either way.

**After writing — update approved-hash (repo sessions only):** Recompute and overwrite `~/.claude/memory/sessions/<slug>/<name>.approved-hash`:
```bash
python3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "<session_root>/<name>.md" > ~/.claude/memory/sessions/<slug>/<name>.approved-hash
```

**Update `_index.md`:** Read `<session_root>/_index.md` — create with header if not exists. Find the line for `<name>`: extract `@created-by` (col 2) and `created-date` (col 3) to preserve; if no existing line, use `@<handle>` and `<today>`. Replace or append: `<name> | @<created-by> | <created-date> | @<handle> | <today> | <status> | <title-or-dash>`. Where `<status>` = the session's current `Status:` field.

**Note:** `switch` is not a save point — it does not write a `_history.md` entry or create a checkpoint. If you worked on the previous session before switching, run `/session:checkpoint` or `/session:commit` first so that work is captured.

Done — proceed with the work.
