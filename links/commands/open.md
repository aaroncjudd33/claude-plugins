---
name: open
description: Open a named link or workspace in Edge. Supports partial matching and scope flags.
argument-hint: "<key | workspace> [-w | -l | -a]"
---

# /links:open <key | workspace> [-w | -l | -a]

Open a named link by key or all links in a workspace in Edge.

## Flags

- `-w` — search workspaces only
- `-l` — search link keys only
- `-a` — search all (default)

## Steps

1. Read `C:\Users\ajudd\.claude\browser-links.json`

2. Parse any flag from the argument (`-w`, `-l`, `-a`). Default scope is all.

3. Match the argument (case-insensitive) against the scoped data:

   **Exact matches first:**
   - Workspace key matches (e.g. `jira`, `forge-dev`) → workspace match
   - Link key matches (e.g. `jira:board`) → link match
   - Both match → ask: "Found both a workspace and a link named '[arg]'. Open workspace (all links) or just the link?"

   **Partial matches if no exact match:**
   - Filter workspaces and/or links where the key contains the argument
   - 1 result → open it
   - 2+ results → print the matched names and ask: "Which did you mean? [list]"

   **No match at all:**
   - Print: "No match for '[arg]'. Searching..." and show results from `/links:search [arg]`

4. **Opening a link:**
   - Resolve window (priority order):
     1. Link has `window` field → use that
     2. Called from workspace context (step 5) → use workspace name
     3. Look up key prefix in `prefixDefaults`
     4. No match → open without named window
   - Run:
     ```bash
     powershell -ExecutionPolicy Bypass -File "C:\Users\ajudd\.claude\scripts\Open-EdgeUrl.ps1" -Url "<url>" -WindowName "<window>"
     ```
   - Print: `Opened [key] → [window] window`

5. **Opening a workspace:**
   - Window = workspace name
   - For each key in workspace's `links` array:
     - Look up link in `links` section
     - If link has `window` field → use that window (link wins)
     - Else → use workspace name as window
     - Run `Open-EdgeUrl.ps1`
     - Wait 2 seconds after the first URL, 1 second between subsequent ones
   - Print: `Opened [N] links in [workspace] workspace`
