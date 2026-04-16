---
name: open
description: Open a named link by key or a workspace by name in Edge
argument-hint: "[key | workspace-name]"
---

# /links:open [key | workspace-name]

Open a named link or all links in a workspace.

## Steps

1. Read `C:\Users\ajudd\.claude\browser-links.json`

2. Match the argument against the data:
   - Workspace match: argument equals a key in `workspaces` (case-insensitive)
   - Link match: argument equals a key in `links`
   - **Both match** → ask: "Found both a workspace and a link named '[arg]'. Open workspace (all links) or just the link?"
   - **No match** → run search: "No exact match for '[arg]'. Searching..." and show results from `/links:search [arg]`

3. **Opening a link:**
   - Resolve window (priority order):
     1. Link has `window` field → use that
     2. Called from workspace context (step 4) → use workspace name
     3. Look up key prefix in `prefixDefaults`
     4. No match → open without named window
   - Run:
     ```bash
     powershell -ExecutionPolicy Bypass -File "C:\Users\ajudd\.claude\scripts\Open-EdgeUrl.ps1" -Url "<url>" -WindowName "<window>"
     ```
   - Print: `Opened [key] → [window] window`

4. **Opening a workspace:**
   - Window = workspace name
   - For each key in workspace's `links` array:
     - Look up link in `links` section
     - If link has `window` field → use that window (link wins)
     - Else → use workspace name as window
     - Run `Open-EdgeUrl.ps1`
     - Wait 2 seconds after the first URL, 1 second between subsequent ones
   - Print: `Opened [N] links in [workspace] workspace`
