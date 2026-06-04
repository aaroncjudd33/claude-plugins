---
name: pto
description: Send an all-day OOF calendar invite to the pto-invite team for specified dates
argument-hint: "<date-range> [, <date-range>]"
---

# /comms:pto <date-range>

Send an all-day OOF calendar invite to the `pto-invite` team for the given dates.

## Arguments

One or more date ranges in natural language:
- Single day: `June 5`
- Range, same month: `May 22-23`
- Range, cross-month: `May 29 - June 2`
- Multiple ranges: `May 22-23, June 5`

## Steps

### 1. Parse dates

Using today's date for context, convert the argument to:
- **Start date** — first PTO day in ISO 8601 format (`2026-05-22`)
- **End date** — day after the last PTO day, ISO 8601 (`2026-05-24` for May 22–23). Graph API uses exclusive end dates for all-day events.
- **Human-readable range** — e.g. "Thursday May 22 and Friday May 23"
- **Back in office** — next weekday after the last PTO day (e.g. "Monday May 26" if last day is Friday)

### 2. Load attendees

Read `~/.claude/plugins/team.json`. Filter to members whose `roles` array includes `"pto-invite"`. Collect their `name` and `email` fields.

### 3. Ask for personal note

Ask the user: "Any personal note to include? (e.g. 'Celebrating my wife's birthday') — or press enter to skip."

Compose the body:
- **With note:** `<note>. I'll be out of office <human-readable range>. Back in the office <back-in-office date>.`
- **Without note:** `I'll be out of office <human-readable range>. Back in the office <back-in-office date>.`

### 4. Preview

Show the full event details before creating:
```
Title:      Aaron on PTO
Dates:      <human-readable range>
Start:      <start-date>
End:        <end-date> (exclusive — Graph API convention)
Show as:    Out of Office
All day:    Yes
Body:       <composed body text>
Attendees:  <name>, <name>, ... (N people)
```

Ask: "Send invite? (yes / cancel)"

### 5. Create event

On approval, call `create_event` with:
- `subject`: `Aaron on PTO`
- `body`: the composed body text
- `start`: `<start-date>T00:00:00.000Z`
- `end`: `<end-date>T00:00:00.000Z`
- `isAllDay`: `true`
- `showAs`: `"oof"`
- `attendees`: array of email addresses from Step 2

### 6. Confirm action

Call `confirm_action` with the returned `actionId` to execute the invite.

Report: `PTO invite sent — <human-readable range>. <N> attendees notified.`
