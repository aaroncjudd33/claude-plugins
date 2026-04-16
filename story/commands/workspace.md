---
name: workspace
description: Open the Jira workspace — close, reopen, load board, calendar, and in-progress stories
---

# /story:workspace

Open the Jira workspace with the board, calendar, and any in-progress stories assigned to me.

## Steps

### 1. Close existing Jira window

```bash
powershell -ExecutionPolicy Bypass -File "C:\Users\ajudd\.claude\scripts\Close-EdgeWindow.ps1" -WindowName "Jira"
```

Wait 2 seconds for it to fully close.

### 2. Open the Jira workspace

Read `C:\Users\ajudd\.claude\browser-links.json`. Get the `links` array from `workspaces["Jira"]`. Look up each key in the `links` section to get its URL.

Open each in the Jira window using the Open-EdgeUrl script. Open `jira:calendar` first, then `jira:board`, then any others.

```bash
powershell -ExecutionPolicy Bypass -File "C:\Users\ajudd\.claude\scripts\Open-EdgeUrl.ps1" -Url "<url>" -WindowName "Jira"
```

Wait 2 seconds after the first URL (window creation), 1 second between subsequent ones.

### 3. Query in-progress stories

Use `searchJiraIssuesUsingJql` on cloud ID `9de6eb2b-2683-44e6-89ff-c622027e09b4`:

```jql
assignee = "620147d91fec260068c1097d" AND status = "In Progress" ORDER BY duedate ASC
```

Fields: `summary, status, assignee, duedate, priority`

### 4. Register and open in-progress stories

For each story returned:

1. Register the link if not already in `browser-links.json`:
   - Add `story:BPT2-XXXX` to `links` section: `{ "url": "https://younglivingeo.atlassian.net/browse/BPT2-XXXX", "description": "<story summary>" }`
   - Create workspace `BPT2-XXXX` (type: story) if it doesn't exist
   - Add `story:BPT2-XXXX` to the workspace's `links` array
   - Write back to `browser-links.json`

2. Open the story URL in the Jira window:
   ```bash
   powershell -ExecutionPolicy Bypass -File "C:\Users\ajudd\.claude\scripts\Open-EdgeUrl.ps1" -Url "https://younglivingeo.atlassian.net/browse/<KEY>" -WindowName "Jira"
   ```

### 5. Report

```
Jira workspace initialized
  Tabs: jira:calendar, jira:board
  Stories (In Progress): BPT2-XXXX — Summary, BPT2-YYYY — Summary
```

If no in-progress stories: `Stories: none in progress`
