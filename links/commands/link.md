---
name: link
description: Add or edit a named link in the registry. Detects whether the key exists and acts accordingly.
argument-hint: "<key> [url]"
---

# /links:link <key> [url]

Add a new link or edit an existing one in `browser-links.json`.

## Steps

1. Read `~/.claude/browser-links.json`

2. Parse `key` and optional `url` from arguments. If key is missing, ask for it.

3. Validate key format: must be `prefix:name` (e.g. `jira:sprint`, `pr:virtual-office#789`).
   If no colon, ask the user to confirm or suggest a prefix based on the URL or context.

4. **If key does not exist → Create mode:**
   - If `url` not provided, ask for it
   - Ask for:
     - **Description** — short phrase used in search results
     - **Workspace** — name of workspace to add this link to (or "none")
     - **Window override** — only if this link must always open in a window that differs from its prefix default (rare; skip if unsure)
   - If workspace specified, verify it exists; if not, ask to create it first via `/links:workspace`
   - Write to `links` section:
     ```json
     "key": { "url": "...", "description": "..." }
     ```
     Include `window` only if a window override was specified.
   - If workspace specified, add key to workspace's `links` array
   - Print: `Added [key] → [url]` and `Added to [workspace]` if applicable

5. **If key exists → Edit mode:**
   - Show current values:
     ```
     [key]
       url:         [current url]
       description: [current description]
       window:      [current window or "none"]
       workspaces:  [list of workspaces containing this key, or "none"]
     ```
   - Ask: "What would you like to change?"
   - Apply requested changes. For workspace: always additive — add to the specified workspace without removing existing ones.
   - Write back to `browser-links.json`
   - Print: `Updated [key]` with a summary of what changed

6. Write back to `browser-links.json`
