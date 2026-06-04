---
name: worklog
description: Show work log entries. Accepts a date, rolling window (3d, 5d, last week), or story key (BPT2-XXXX) to filter across all dates.
---

# Session: Work Log

Show what was accomplished during sessions. Supports single dates, rolling windows, and cross-date story filtering.

## Instructions

### 1. Parse Arguments and Mode

Extract `--brief` if present → `brief_mode = true`. Remove it from the remaining args.

Detect mode from the remaining argument:

**Story filter mode** — arg matches a session/story key pattern (e.g. `BPT2-6258`, `session`, `release`, any known session name):
- Set `mode = story_filter`, `filter_key = <arg>`

**Rolling window mode** — arg matches a duration pattern:
- `3d`, `5d`, `7d`, `Nd` → last N calendar days (including today)
- `1w`, `2w` → last 7 or 14 days
- `last N days` / `last N weeks` / `last week` → same
- Set `mode = window`, compute `start_date` and `end_date` (today)
- Cap at 14 days — if the user requests more, show the last 14 and note the cap

**Single date mode** (default):
- `today` / `(no argument)` → today
- `yesterday` → yesterday
- `last Tuesday` etc. → most recent occurrence of that weekday
- `April 15`, `Apr 15`, `4/15`, `2026-04-10` → that date
- Set `mode = single`, `target_date = <YYYY-MM-DD>`

If the argument is ambiguous or unparseable, ask the user to clarify.

### 2. Collect Entries

**Single date:** Read `~/.claude/memory/worklog/<target_date>.md`. If missing or empty: `No worklog entries for <friendly date>.` and stop.

**Rolling window:** Enumerate all `YYYY-MM-DD.md` files in `~/.claude/memory/worklog/` whose date falls within `[start_date, end_date]`. Read each. Skip missing dates silently. If no files found: `No worklog entries for the last N days.` and stop.

**Story filter:** Enumerate all `YYYY-MM-DD.md` files in `~/.claude/memory/worklog/` within the last 30 days. Read each. Extract only `## HH:MM` entries whose session name contains `filter_key` (case-insensitive). Collect matching entries tagged with their source date. If no matches: `No worklog entries found for "<filter_key>" in the last 30 days.` and stop.

### 3. Output

#### Single date

```
Work Log — <DayOfWeek>, <Month> <Day>, <Year>
================================================================

Summary
  - <theme 1>
  - <theme 2>
  - <theme 3 if warranted>
```

2–3 bullets. Synthesize themes from entries — do not copy text verbatim. Each bullet names a domain or initiative (e.g. "Session plugin inbox redesign — in-progress state model shipped", "GLB sandbox verified against env6").

If `brief_mode`, stop after summary.

Otherwise print each entry:
```
HH:MM — session-name (type)

  Accomplished: <value>
  Open items:   <value or "none">
```

Chronological order, blank line between entries.

#### Rolling window

```
Work Log — Last N days  (<start friendly> – <end friendly>)
================================================================

Summary
  - <theme 1>
  - <theme 2>
  - <theme 3>
  - <theme 4 if warranted>
```

3–4 bullets max synthesized across all entries in the window. Name themes broadly enough to span multiple days (e.g. "Release plugin comms gap work across 3 sessions", "Story dashboard deploy-date visibility").

If `brief_mode`, stop after summary.

Otherwise print entries day-by-day, oldest first:
```
<DayOfWeek>, <Month> <Day>
---
HH:MM — session-name (type)

  Accomplished: <value>
  Open items:   <value or "none">
```

Separate days with a blank line. Within each day, entries are chronological.

#### Story filter

```
Work Log — <filter_key>  (last 30 days)
================================================================
```

No theme synthesis — entries are already scoped to one story/session. Group by date, newest first:

```
<DayOfWeek>, <Month> <Day>
  HH:MM — <session-name> (<type>)
    Accomplished: <value>
    Open items:   <value or "none">
```

`--brief` has no effect in story filter mode — entries are already compact.

### 4. Cleanup (silent)

After displaying results, silently delete any files in `~/.claude/memory/worklog/` older than 30 days. No output for this step.
