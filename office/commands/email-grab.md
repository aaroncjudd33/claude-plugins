---
name: email-grab
description: Fetch email headers from a folder and cache to C:\temp\email-cache.json. Reusable by email-sweep and email-process.
argument-hint: "[folder] [limit]"
---

# /office:email-grab [folder] [limit]

Fetch email headers and write to cache. No bodies fetched.

## Arguments
- `folder` — folder name (default: `action`). Supported: `inbox`, `action`, `archive`, `github`, `braze`, `bamboo`, `training`, `docs`, `amplitude`, `aws`, `jira`, `teams`
- `limit` — max emails to fetch (default: 50, use 3-5 for testing)

## Folder IDs (from project_inbox_triage.md)
Look up the folder name in the Folder IDs table in `project_inbox_triage.md`.

> **Note:** `project_inbox_triage.md` is a project-level memory file, not part of this plugin. It lives in the active project's memory folder and is loaded automatically as project context. It is not bundled with the office plugin.

## Steps

1. Launch a **Haiku sub-agent** with this minimal prompt:

> Call `mcp__claude_ai_yl-msoffice__list_emails` with folderId `[resolved-id]`, limit `[limit]`, and orderBy `receivedDateTime desc`.
> Return JSON array with only: id, subject, from.displayName, from.address, receivedDateTime, isRead.

2. Parse the result. Write to `C:\temp\email-cache.json`:

```json
{
  "folder": "inbox",
  "fetchedAt": "2026-04-14T13:00:00Z",
  "count": 3,
  "emails": [
    { "id": "...", "subject": "...", "fromName": "...", "fromAddress": "...", "receivedAt": "...", "isRead": false }
  ]
}
```

3. Print: `Grabbed N emails from [folder].`
