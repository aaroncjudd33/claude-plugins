---
name: workspace
description: Create a new workspace or edit an existing one. Detects whether the name exists and acts accordingly.
argument-hint: "<name>"
---

# /links:workspace <name>

Create a new workspace or edit an existing one in `browser-links.json`.

## Steps

1. Read `~/.claude/browser-links.json`

2. Parse `name` from argument. If missing, ask for it.

3. **If workspace does not exist → Create mode:**
   - Ask for:
     - **Description** — what this workspace is for
     - **Initial links** — comma-separated existing link keys to add, or "none"
   - Validate any provided link keys exist in the `links` section. Warn about any that don't.
   - Add to `workspaces` section:
     ```json
     "workspace-name": {
       "description": "...",
       "links": []
     }
     ```
     Add any validated initial links to the array.
   - Write back to `browser-links.json`
   - Print: `Created workspace '[name]'` with member count if links were added

4. **If workspace exists → Edit mode:**
   - Show current state:
     ```
     [name]
       description: [current description]
       links ([N]):
         [key]  [description]
         ...
     ```
   - Ask: "What would you like to change?"
   - Apply requested changes:
     - **Add link** — verify key exists in `links` section; if not, suggest `/links:link [key]` first. Append to workspace's `links` array.
     - **Remove link** — remove key from workspace's `links` array only. The link itself stays in the registry.
     - **Description** — update workspace description
   - Write back to `browser-links.json`
   - Print: `Updated workspace '[name]'` with a summary of what changed
