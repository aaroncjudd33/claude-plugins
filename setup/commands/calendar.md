---
name: calendar
description: Today's calendar — meetings and events via Microsoft 365.
---

# Setup: Calendar

Show today's calendar events from Microsoft 365.

## Instructions

<!-- SYNC NOTE: These calendar instructions are duplicated in setup/commands/local.md (section 5). If you change them here, update there too. -->

1. Detect the user's local timezone and compute today's date range in UTC.

   **a. Run via Bash:**
   ```powershell
   $tz = [System.TimeZoneInfo]::Local; $now = [datetime]::Now; "$([int]$tz.GetUtcOffset($now).TotalHours)|$($tz.Id)|$($tz.IsDaylightSavingTime($now))"
   ```
   Parse output as `offset|tzId|isDst` (e.g. `-4|Eastern Standard Time|True`).

   **b. Map timezone ID to abbreviation** (isDst selects which label):
   - "Eastern Standard Time" → EST (false) / EDT (true)
   - "Central Standard Time"  → CST / CDT
   - "Mountain Standard Time" → MST / MDT
   - "Pacific Standard Time"  → PST / PDT
   - Anything else → `UTC-N` / `UTC+N` using the offset value

   **c. Compute date range** (UTC = local − offset):
   - Start: today 00:00 local → subtract offset hours → ISO 8601 UTC
   - End:   today 23:59 local → subtract offset hours → ISO 8601 UTC

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
CALENDAR (N events — EDT)

  9:00 AM   Daily Standup                 (30 min)  — Teams
  10:30 AM  Sprint Planning               (1h)
  2:00 PM   1:1 with Heber               (1h)  — Teams
```

Format rules:
- Header shows detected timezone abbreviation (e.g. `— EDT`, `— MST`)
- Align times with consistent padding so event names start at the same column
- If no events: `CALENDAR — No events today`
- If call fails: `CALENDAR — Unavailable`
