---
name: worklog
description: Show work log entries for a given day. Accepts natural language dates — today, yesterday, last Tuesday, April 15, a specific date, etc.
---

# Session: Work Log

Show what was accomplished during sessions on a given day.

## Instructions

### 1. Resolve the Date and Flags

Parse the arguments:
- Extract `--brief` if present and set `brief_mode = true`; remove it from the date portion
- Resolve the remaining date string in any natural language form:
  - `today` / `(no argument)` → today's date
  - `yesterday` → yesterday's date
  - `last Tuesday`, `last Monday`, etc. → the most recent occurrence of that weekday
  - `April 15`, `Apr 15`, `4/15` → that date in the current year (or prior year if it would be in the future)
  - `2026-04-10`, `April 10 2026`, etc. → that exact date

Resolve to a `YYYY-MM-DD` string. If the date is ambiguous or unparseable, ask the user to clarify.

### 2. Read the Worklog File

Read `~/.claude/memory/worklog/<YYYY-MM-DD>.md`.

- If the file does not exist: output `No worklog entries for <friendly date>.` and stop.
- If the file is empty or has no entries: same message.

### 3. Output

Print a header:
```
Work Log — <DayOfWeek>, <Month> <Day>, <Year>
================================================================
```

Then synthesize a **Day Summary** from all entries and print it immediately after the header:

```
Summary
  - <theme 1>
  - <theme 2>
  - <theme 3 if warranted>
```

2–3 bullets max. Synthesize themes from the entry content — do not copy accomplishment text verbatim. Each bullet names a domain or initiative (e.g. "Session plugin hardening — inbox count fix and worklog enhancements", "GLB E2E verified against sandbox, blocked on SSM params in prod"). Aim for a scan-friendly read of the day.

If `brief_mode = true`, stop here — do not print the per-entry detail.

Otherwise, print a blank line then each `## HH:MM — name (type)` entry:

```
HH:MM — session-name (type)

  Accomplished: <value>
  Open items:   <value, or "none">
```

Separate entries with a blank line. Preserve the order they appear in the file (chronological).

If only one entry exists, still use the same format — no special-casing.

### 4. Cleanup (silent)

After displaying results, silently delete any files in `~/.claude/memory/worklog/` that are older than 30 days. No output for this step.
