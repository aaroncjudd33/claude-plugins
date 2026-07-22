---
name: sync
description: Reconcile locally-tracked story/CAB sessions against live Jira status — surface any session that's stuck open locally but already terminal in Jira (deployed/closed outside the plugin flow), then close it locally on confirmation.
---

# Session Sync

Read-only by default, one confirmed write at the end. Answers "is any session I'm tracking
locally actually already done in Jira?" — the case a session was closed out-of-band (a
teammate finished the story, a CAB shipped without going through `/session:finish`) and sits
around forever showing only as "stale by age," never as "actually done."

**Work-repo (story/cab) scope only, v1 (acp-ajudd#163).** Plugin/personal reconciliation is a
different mechanism entirely (no Jira system of record to check against) and is explicitly
deferred, not folded in here.

**Never auto-closes.** A hit is a local/Jira mismatch worth a human's attention, not something
to silently paper over — always confirm before writing anything.

## Instructions

### 1. Resolve Location + Scope Gate

Run `pwd`, extract the repo slug (last path component). Resolve `session_root`, `handle`, and
`zone` using Path Resolution (`references/path-resolution.md` — core resolution + § Zone
Detection).

If `zone` is not `work` (story/cab repos), stop and print: `/session:sync is scoped to
work-repo (story/CAB) sessions only — nothing to reconcile here.`

### 2. Scan Locally-Tracked Sessions

List `<session_root>/*.md`, same discovery as `session-list.py` (skip `_`-prefixed files and
`*.approved-hash`). Keep only names matching `^(BPT2-\d+|CAB-\d+)$` (case-insensitive,
normalize to uppercase) — these are the story/CAB session files; anything else (a
`refinement-*` leftover, a stray general-type session name) is out of scope.

For each matching name, read its status the same way `session-list.py`'s
`read_session_meta` does (body `- **Status:**` line, defaulting to `in-progress` if absent).
**Keep only `in-progress` and `paused`** — a session already `completed` has nothing to
reconcile.

If nothing remains, print: `Nothing to sync — no in-progress or paused story/CAB sessions
tracked locally.` and stop.

### 3. One Batched JQL Query

Reuse the terminal-status set already canonical in this codebase (`story/skills/story/SKILL.md`
§ terminal statuses, same list `story:dashboard` and `story:ready` query against) — do not
invent a new taxonomy:

```jql
key in (KEY1,KEY2,...) AND status in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated, Implemented)
```

Substitute every key found in Step 2, comma-separated, no per-session loop — one call covers
the whole batch, mirroring `story:dashboard`'s own query pattern. Run via
`searchJiraIssuesUsingJql` on cloud ID `9de6eb2b-2683-44e6-89ff-c622027e09b4`. Request fields:
`summary, status`.

If the query returns zero results, print: `Checked N session(s) against Jira — all still
open. Nothing to reconcile.` (list the keys checked) and stop.

### 4. Present Hits — Plain Text, No Picker Widget

**Never use `AskUserQuestion` or any selectable/arrow-key widget here (Session Skill § Never a
selectable picker) — this is plain text the user replies to by typing, same as every other
session-flow decision point.**

For each key the query returned, show the mismatch:

```
Sync — <slug>

Found N session(s) already closed in Jira but still open locally:
  1  BPT2-6479 — Jira: Done       (local: in-progress, last updated Jun 10)
  2  CAB-9240  — Jira: Released   (local: paused, last updated Jul 02)

Close these locally to match Jira? (yes / no / pick numbers, e.g. "1")
```

`last updated` is the session's `updated_date` from its meta (`read_session_meta` / index row).
Wait for a typed reply. `no` stops here with nothing written. A bare `yes` (or "all") means
every row listed; numbers mean only those rows.

### 5. Close Confirmed Sessions — One `finish-close.py` Call Per Session

For each confirmed key, resolve its `type` from the key prefix (`BPT2-*` → `story`, `CAB-*` →
`cab`) and compose:

- `done_note`: `synced from Jira status <jira-status>`
- `history_line`: `[<today>] <name> — reconciled: Jira status <jira-status> (synced via
  /session:sync)`
- `worklog_entry`: `## <HH:MM> — <name> — <jira-summary> (<type>)\n\n**Accomplished:**
  Reconciled against Jira — status is <jira-status>, session closed to match.\n\n**Open
  items:** none`
- `--title`: the Jira `summary` from Step 3's result (keeps `_index.md`'s title current)
- `--item-id`: leave empty — story/cab sessions aren't picked up from the plugin/personal
  item-driven inbox, so there's no `[DONE]` archive stamp to write

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
PYBIN=python3; command -v python3 >/dev/null 2>&1 || PYBIN=python
"$PYBIN" "$ROOT/scripts/finish-close.py" \
  --session-root "<session_root>" --slug "<slug>" --name "<key>" \
  --type "<story-or-cab>" --date "<YYYY-MM-DD>" --handle "<handle>" \
  --title "<jira-summary>" << 'JSON'
{"history_line": "<the composed line>", "worklog_entry": "<the composed block, internal newlines escaped as \n>", "done_note": "<the composed note>"}
JSON
```

**This is safe to run even when the confirmed key is NOT the current terminal's active
session (acp-ajudd#163 hardened `finish-close.py` for exactly this case)** —
`finish-close.py` only clears `_active`/`_active.dirty` when they actually name the session
being closed; a different in-progress session's active pointer is left untouched. Run one call
per confirmed key, in any order — each is independent.

Same **fail-closed / self-verifying** contract as `/session:finish`'s own close: on any
non-zero exit, report the error for that key and move on to the rest — do NOT hand-edit the
surfaces, and do NOT treat that one key as reconciled. Re-running is idempotent (safe retry).

### 6. Report

```
Sync — <slug>

Reconciled:
  BPT2-6479 — Jira: Done       → local session closed
  CAB-9240  — Jira: Released   → local session closed

Skipped (declined): BPT2-XXXX   ← only if any hit was declined
Failed (see error above): CAB-YYYY   ← only if a finish-close.py call exited non-zero
```

Omit the `Skipped` / `Failed` lines if empty.
