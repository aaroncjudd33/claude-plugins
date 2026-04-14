---
name: email-apply-rules
description: Classify emails in C:\temp\email-cache.json, silently process matched senders via Haiku sub-agent, then run interactive triage for unmatched emails.
---

# /office:email-apply-rules

Three phases: classify (no API calls), silent execute via Haiku, then interactive triage for unmatched emails.

**Why sub-agent for silent phase:** `mail.move` and `mail.mark_read` responses return full message objects with HTML bodies (5K–15K tokens each). Running them in the main session causes context bloat. Delegating to Haiku keeps those responses out of main context.

## Phase 1 — Classify (no API calls)

Read `C:\temp\email-cache.json` and `project_inbox_triage.md` (sender rules + folder IDs).

Classify each email into one of four buckets:

0. **`to_accept`** — matches a row in `## Meeting Accept Rules` (from + subject contains) → accept calendar event silently, mark read, leave in inbox
1. **`to_move`** — rule matches a non-Archive folder → mark read + move silently
2. **`to_mark_read_only`** — rule matches Archive → mark read only, leave in inbox (user archives manually — no move cost)
3. **`unmatched`** — no rule match → interactive triage

Check `to_accept` first (before sender-only rules). For each match, find the calendar event using `list_events` filtered by subject, call `calendar.respond_to_event` with `response=accept, sendResponse=false` (or `calendar.delete_event` for remove), then delete the email via `mail.move` with `folder=deleteditems`. Note: there is no `mail.delete` action.

Build the arrays:
- `to_move`: `[{ id, folderId, folderName, isRead }]`
- `to_mark_read_only`: `[{ id, isRead }]`
- `unmatched`: `[{ id, subject, fromName, fromAddress, receivedAt, isRead }]`

Print the plan:
```
Plan:   2 → accept (BPT2 Daily Standup, BPT2 Refinement)
       12 → silent moves (GitHub: 7, Bamboo: 3, Braze: 2)
        8 → mark-read only (Archive senders, stay in inbox)
       14 → interactive triage
Executing silent phase...
```

## Phase 2 — Silent Execute via Haiku Sub-Agent

Spawn a **Haiku sub-agent** with the prompt below. Substitute the actual arrays built in Phase 1.

---
You are executing email triage for Microsoft 365. Do not read any files or fetch anything.

First, call ToolSearch with query `select:mcp__claude_ai_yl-msoffice__execute_action` to load the execute_action tool.

**Step 1 — Mark as read** (skip entirely if list is empty):
Collect all IDs where `isRead` is false from BOTH `to_move` and `to_mark_read_only`. Call execute_action with actionId="mail.mark_read" and params={"id": "<id>", "isRead": true} for each.
Run up to 15 calls in parallel per batch. Wait for all results before starting next batch.

Mark-read IDs (combined from to_move and to_mark_read_only where isRead=false):
[PASTE combined mark-read ID list here]

**Step 2 — Move** (skip entirely if list is empty):
For each item in to_move, call execute_action with actionId="mail.move" and params={"id": "<id>", "folder": "<folderId>"}.
Run up to 15 calls in parallel per batch. Wait for all results before starting next batch.

Move list (id + folderId + folderName for reference):
[PASTE to_move array here]

When all steps are done, respond with exactly one line:
`Done: X mark_read, Y moved (FolderName: N, ...). Errors: Z`
---

Wait for sub-agent. Print its summary line.

## Phase 3 — Interactive Triage

If `unmatched` is empty → delete `C:\temp\email-cache.json` and stop.

Otherwise print:
```
[N] unmatched emails. How do you want to review?
  1  All at once — see the full list, annotate by number
  2  One at a time — step through one by one
```

Wait for the user to choose 1 or 2, then follow the section below.

---

### Mode 1 — All at Once

Display the numbered list, columns aligned:
```
  #   From                                           Subject                          Date
  1   GitHub <notifications@github.com>              PR #123 merged                   Apr 14
  2   Workday <wd@myworkday.com>                     Action Required: Time Sheet       Apr 13
  ...
```

Then show action codes:
```
skip      leave in inbox (archive manually later)
archive   mark read, leave in inbox (same as skip but explicit)
action    move to Action folder
move/X    move to folder X (e.g. move/github, move/braze)
rule/X    add sender rule → folder X, then move
read      fetch and summarize body first, then decide
accept    accept meeting invite, delete email
remove    remove event from calendar, delete email
delete    delete the email (mail.move to deleteditems — no mail.delete action exists)
```

Wait for user annotations. Accept any reasonable format:
- `1=skip, 2=action, 3=move/github, 4=rule/braze, 5=read`
- Line per item: `1: skip`
- Partial list is fine — any unspecified items default to `skip`

**Handle "read" items first:**
For each `read` item, call `mcp__claude_ai_yl-msoffice__get_email` directly in the main session (user-initiated, value-bearing). Show a 2–3 sentence summary of the email. Ask the user for the final action on that item before proceeding.

**After all annotations are resolved:**
1. For any `rule/X` items: add the sender to the `## Sender Rules (auto-move)` table in `project_inbox_triage.md` using the Edit tool. Then scan the remaining `unmatched` list — any other emails from that sender are now resolved with the same action.
2. Show a final decision summary: `8 skip, 3 action, 2 rule/braze, 1 delete — executing...`
3. Batch execute all moves and deletes via Haiku sub-agent (same pattern as Phase 2, but include delete actions as `mail.delete`).
4. Delete `C:\temp\email-cache.json`.

---

### Mode 2 — One at a Time

For each email in sequence, show:
```
[2/14]  GitHub  <notifications@github.com>  —  PR #123 merged  —  Apr 14
Action?  skip / action / move/<folder> / rule/<folder> / read / delete
```

Process the user's response:
- `read` → call `mcp__claude_ai_yl-msoffice__get_email` in main session, show 2–3 sentence summary, re-prompt for final action
- `rule/<folder>` → record decision, then immediately: update `project_inbox_triage.md` with the new sender rule (Edit tool), scan remaining unmatched for same sender and resolve those automatically (print how many were auto-resolved)
- All other actions → record decision and move to next email

After the last email, show a decision summary and confirm before executing:
```
Summary: 8 skip, 3 action, 2 rule/braze, 1 delete
Execute? (y/n)
```

On confirmation:
1. Batch execute all moves and deletes via Haiku sub-agent (same pattern as Phase 2).
2. Delete `C:\temp\email-cache.json`.

---

## Saving New Rules

Any time the user creates a rule during triage (either mode):
- Add a row to the `## Sender Rules (auto-move)` table in `project_inbox_triage.md`
- Use the Edit tool (never manual — keep it reliable)
- Immediately apply the rule to any remaining unmatched emails in the current loop so the user doesn't see the same sender twice
