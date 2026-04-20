---
name: calendar
description: Today's calendar — meetings and events via Microsoft 365.
---

# Setup: Calendar

Show today's calendar events from Microsoft 365.

## Instructions

<!-- SYNC NOTE: These calendar instructions are duplicated in setup/commands/local.md (section 5). If you change them here, update there too. -->

1. Compute today's date range in UTC. The user is in Mountain Time (MDT = UTC-6 from mid-March through early November; MST = UTC-7 otherwise). April–October → MDT.
   - Start: today at 00:00 local → UTC (e.g. 2026-04-20T06:00:00Z for MDT)
   - End:   today at 23:59 local → UTC (e.g. 2026-04-21T05:59:00Z for MDT)

2. Call `mcp__claude_ai_yl-msoffice__list_events` with:
   - `startDateTime`: computed start in ISO 8601 UTC
   - `endDateTime`: computed end in ISO 8601 UTC
   - `top`: 20

3. Filter out events where the user's response status is `declined`.

4. Sort remaining events by start time ascending.

5. For each event compute:
   - **Time:** start time in 12-hour format, no seconds (e.g. `9:00 AM`)
   - **Duration:** end − start. Show as `(30 min)`, `(1h)`, `(1h 30m)`, etc.
   - **Location hint:** if the event has a Teams join URL or `isOnlineMeeting` is true → `— Teams`. Otherwise show the location name if non-empty. Omit if neither.

6. Output:

```
CALENDAR (N events)

  9:00 AM   Daily Standup                 (30 min)  — Teams
  10:30 AM  Sprint Planning               (1h)
  2:00 PM   1:1 with Heber               (1h)  — Teams
```

Format rules:
- Align times with consistent padding so event names start at the same column
- If no events: `CALENDAR — No events today`
- If call fails: `CALENDAR — Unavailable`
