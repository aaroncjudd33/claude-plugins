---
name: add-workspace
description: Create a new named workspace — the workspace name becomes the Edge window title
argument-hint: "[name]"
---

# /links:add-workspace [name]

Create a new workspace. The workspace name becomes the Edge window title used when opening it.

## Steps

1. Read `C:\Users\ajudd\.claude\browser-links.json`

2. Parse `name` from argument. If missing, ask for it.

3. If workspace already exists → "Workspace '[name]' already exists. Use `/links:edit-workspace [name]` to modify it." Stop.

4. Ask for optional fields:
   - **Description** — what this workspace is for
   - **Type** — `story`, `cab`, or `custom` (default: `custom`)
   - **Initial links** — comma-separated existing link keys to add, or "none"

5. Validate any provided link keys exist in the `links` section. Warn about any that don't.

6. Add to `workspaces` section:
   ```json
   "WorkspaceName": {
     "description": "...",
     "links": []
   }
   ```
   Include `"type": "story"` or `"type": "cab"` only for story/CAB workspaces. Omit `type` entirely for custom workspaces. Add any validated initial links to the array.

7. Write back to `browser-links.json`

8. Print: `Created workspace '[name]'` with member count if links were added
