---
name: add-link
description: Add a new named link to the registry, optionally associating it with a workspace
argument-hint: "[key] [url]"
---

# /links:add-link [key] [url]

Add or update a named link in `browser-links.json`.

## Steps

1. Read `C:\Users\ajudd\.claude\browser-links.json`

2. Parse `key` and `url` from arguments. If either is missing, ask for them.

3. Validate key format: must be `prefix:name` (e.g. `story:BPT2-6258`, `pr:virtual-office#789`). If no colon, ask the user to confirm or suggest a prefix based on the URL.

4. Ask for optional fields:
   - **Description** — short phrase used in search results
   - **Workspace** — name of workspace to add this link to (or "none")
   - **Window override** — only if this link must always open in a specific window that differs from its prefix default (rare)

5. If key already exists → confirm: "Key '[key]' already exists ([current url]). Overwrite?"

6. Write to `links` section:
   ```json
   "key": { "url": "...", "description": "..." }
   ```
   Include `window` only if a window override was specified.

7. If workspace specified:
   - Verify workspace exists; if not, ask to create it first via `/links:add-workspace`
   - Add key to workspace's `links` array

8. Write back to `browser-links.json`

9. Print: `Added [key] → [url]` and `Added to [workspace]` if applicable
