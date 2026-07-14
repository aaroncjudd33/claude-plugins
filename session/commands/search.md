---
name: search
description: Search session files and worklogs by story key or keywords. Find past context without knowing which session it's in.
argument-hint: "[BPT2-XXXX | keyword | \"multi word phrase\"]"
---

# Session: Search

Find past session context by story key, keyword, or phrase. Searches all session files and worklog entries for the current repo — plus the global worklog.

## Instructions

### 1. Parse Arguments

Read the argument string passed to the command.

- **No argument** — discovery mode: list all sessions with metadata (see Step 4).
- **Jira key pattern** (`BPT2-\d+`, `CAB-\d+`) — story key mode: search for that exact key.
- **Anything else** — keyword mode: treat the argument as a search phrase (strip surrounding quotes if present).

Derive the repo slug from `pwd` (last path component). Resolve `session_root` and `handle` using Path Resolution (`references/path-resolution.md`). Worklog always stays local at `~/.claude/memory/worklog/`.

---

### 2. Build the File List

Collect files to search across:

**Session files:** all `*.md` files in `session_root` that do NOT start with `_`.

**Worklog files:** all `*.md` files in `~/.claude/memory/worklog/`.

**Global inbox:** the consolidated per-item dir `<session_root>/_inbox/*.md` — search each item file (acp-ajudd#102); also include a legacy `<session_root>/_inbox.md` if one is still present (pre-migration). Include only in keyword/story mode, not discovery mode.

---

### 3. Search (story key mode or keyword mode)

For each file in the list:

1. Read the file.
2. Check whether the search term appears in the content (case-insensitive for keywords; exact match for Jira keys).
3. If matched:
   - **Session file:** extract `Name`, `Branch`, `Last worked on`, `Open items`, `Next step`, and `Status` from frontmatter/body. Record the matched lines or sections for context snippets (up to 3 relevant lines per file).
   - **Worklog file:** extract the date from the filename (`YYYY-MM-DD`). Record which `## HH:MM` entry/entries contain the match, plus the `Accomplished:` line for each matched entry.

Collect all matches. If nothing found: print `No sessions or worklog entries found for "<query>".` and stop.

---

### 4. Discovery Mode (no argument)

List all session files from `session_root` (no searching). For each:
- Read `Name`, `Branch`, `Last worked on`, `Status`, `updated-by` (from session file fields).
- Count logical inbox items: **plugin / personal (item-driven) use the consolidated `<session_root>/_inbox/`** — the item count is the number of `_inbox/*.md` files (each file is one item; there is no per-session `_inbox_<name>.md`); **story / cab / general use `<session_root>/_inbox_<name>.md`** — count lines beginning with `[20` or `## ` (the `> [type: … · status: …]` metadata line starts with `> ` and is naturally excluded — never count it as an item).

Print:

```
All sessions — <slug>
================================================================
  session        master   completed    inbox 0   May 7
  release        master   completed    inbox 1   May 3
  story          master   paused       inbox 3   Apr 28
  ...
```

Sort by `updated:` date descending (most recent first). Stop here — no switch offer in discovery mode.

---

### 5. Format Results

Print a header:

```
Search results — "<query>"
================================================================
```

Group results into two sections if both types matched: **Sessions** then **Worklogs**. Omit a section header if that type had no matches.

**Session matches:**

```
session  (master · completed · last worked May 7)
  Last work:  <Last worked on value>
  Open items: <Open items value or "none">
  Context:
    • <matched line or relevant excerpt 1>
    • <matched line or relevant excerpt 2>
```

Show up to 3 context bullets per matched session file. Keep excerpts to one line each — truncate at 120 chars.

**Worklog matches:**

```
2026-04-15  (Tuesday)
  • 14:32 — session (plugin)  →  <Accomplished line>
  • 09:10 — story (story)     →  <Accomplished line>
```

Show each matched `HH:MM` entry on its own line. Most recent date first.

Separate each result block with a blank line.

---

### 6. Switch Offer (session matches only)

If one or more **session files** matched, output a plain routing line after the results:

- **One match:**
  ```
  Switch to '<name>'?  yes / n
  ```
  If `yes`: run `/session:switch <name>`.

- **2+ matches:** list them numbered and ask:
  ```
  Switch to one?
    1  <name-1>
    2  <name-2>
    ...
  (number or 'n')
  ```
  If a number: run `/session:switch <name>`.

If only worklog entries matched (no session files): no switch offer — just show results.

---

### 7. Auto-surface in session:start (passive integration)

This step is invoked automatically by `session:start` when starting a **story or CAB session** — not by the user directly.

When `session:start` resolves a story key (e.g. `BPT2-6258`) for a new session, before writing the session file it should call the equivalent of `/session:search <story-key>` and check for prior session file matches.

If prior sessions are found, surface them as context before the session file is written:

```
Found prior sessions mentioning BPT2-6258:
  • story (last worked Apr 15) — "implemented DLE orchestrator, blocked on IAM circular dep"
  • release (last worked Apr 20) — "CAB-1234 deployed to prod, closed"

Picking up from prior work.
```

Then continue with normal session:start flow.

If no prior sessions found: proceed silently.
