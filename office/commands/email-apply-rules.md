---
name: email-apply-rules
description: Classify emails in C:\temp\email-cache.json against inbox rules, then spawn a Haiku sub-agent to execute mark_read + move (keeps MCP responses out of main context).
---

# /office:email-apply-rules

Two phases — classify (no API calls), then execute via Haiku sub-agent.

**Why sub-agent:** `mail.move` and `mail.mark_read` responses return full message objects with HTML bodies (5K–15K tokens each). Running them in the main session causes context compaction. Delegating to a sub-agent keeps those responses out of main context entirely.

## Phase 1 — Classify (no API calls)

Read `C:\temp\email-cache.json` and `project_inbox_triage.md` (sender rules + folder IDs).

For each email, match `fromAddress` against sender rules:
- Exact match → target folder
- Pattern match (e.g. `v-*@youngliving.com`) → mapped folder
- No match → Action folder

Build two arrays:
- `to_mark_read` — list of email IDs for non-Action emails where `isRead` is `false`
- `to_move` — list of `{ id, folderId, folderName }` for all emails

Rules:
- Non-Action: mark read (skip if already `isRead: true`), move to target folder
- Action: move to Action folder, omit from `to_mark_read` (leave unread)

Print the plan:
```
Plan: 34 → Archive, 7 → GitHub, 2 → Braze, 3 → Action (unread)
Spawning Haiku sub-agent to execute...
```

## Phase 2 — Execute via Haiku Sub-Agent

Spawn a **Haiku sub-agent** using the Agent tool with the following prompt. Substitute the actual arrays built in Phase 1 for the placeholders.

---
You are executing email triage for Microsoft 365. Do not read any files or fetch anything.

First, call ToolSearch with query `select:mcp__claude_ai_yl-msoffice__execute_action` to load the execute_action tool.

**Step 1 — Mark as read** (skip entirely if list is empty):
For each ID in the list below, call execute_action with:
`{ "action": "mail.mark_read", "parameters": { "id": "<id>", "isRead": true } }`
Run up to 15 calls in parallel per batch. Wait for all results before starting the next batch.

Mark-read list (email IDs):
[PASTE to_mark_read array here]

**Step 2 — Move**:
For each item in the list below, call execute_action with:
`{ "action": "mail.move", "parameters": { "id": "<id>", "folder": "<folderId>" } }`
Run up to 15 calls in parallel per batch. Wait for all results before starting the next batch.

Move list (id + folderId + folderName for reference):
[PASTE to_move array here]

When all steps are done, respond with exactly one line:
`Done: X mark_read, Y moved (Archive: N, GitHub: N, ...). Errors: Z`
---

Wait for the sub-agent to complete before proceeding.

## Phase 3 — Cleanup

Delete `C:\temp\email-cache.json`. Print the sub-agent's summary line as the final output.
