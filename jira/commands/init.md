---
name: init
description: Initialize the Jira browser window — close, reopen, load board, calendar, and in-progress stories
user_invocable: true
---

# Jira: Init

Set up the Jira browser window with the board, calendar, and any in-progress stories assigned to me.

## Instructions

### 1. Close existing Jira window

```bash
powershell -ExecutionPolicy Bypass -File "C:\Users\ajudd\.claude\scripts\Close-EdgeWindow.ps1" -WindowName "Jira"
```

Wait 2 seconds for it to fully close.

### 2. Load named links

Read `C:\Users\ajudd\.claude\browser-links.json`. Collect all entries where `window` is `"Jira"`.

### 3. Query assigned in-progress stories

Use `searchJiraIssuesUsingJql` on cloud ID `9de6eb2b-2683-44e6-89ff-c622027e09b4`:

```jql
assignee = "620147d91fec260068c1097d" AND status = "In Progress" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY duedate ASC
```

Request fields: `summary, status, assignee, duedate, priority`

### 4. Open everything in the Jira window

Use the Open-EdgeUrl script for all URLs. The **first** URL creates the window; subsequent ones add tabs.

```bash
powershell -ExecutionPolicy Bypass -File "C:\Users\ajudd\.claude\scripts\Open-EdgeUrl.ps1" -Url "<URL>" -WindowName "Jira"
```

**Order:**
1. Named links from browser-links.json (jira:calendar first, then jira:board, then any others)
2. Each in-progress story: `https://younglivingeo.atlassian.net/browse/<KEY>`

Wait 2 seconds after the first URL (window creation), then 1 second between subsequent URLs.

### 5. Report

Print a short summary:

```
Jira window initialized
  Tabs: jira:board, jira:calendar
  Stories (In Progress): BPT2-XXXX, BPT2-YYYY
```

If no in-progress stories, say `Stories: none in progress`
