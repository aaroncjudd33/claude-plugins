---
name: delete
description: Delete a link, workspace, or prefix mapping from the registry.
argument-hint: "<key | workspace-name | prefix>"
---

# /links:delete <key | workspace-name | prefix>

Delete a link, workspace, or prefix from `browser-links.json`.

## Steps

1. Read `~/.claude/browser-links.json`

2. If no argument provided, ask: "What would you like to delete? (link key, workspace name, or prefix)"

3. Match the argument against all three sections:
   - `links` — exact key match (e.g. `jira:board`)
   - `workspaces` — case-insensitive name match (e.g. `Jira`)
   - `prefixDefaults` — exact prefix match (e.g. `jira`)

4. **If matched in multiple sections:**
   - List all matches:
     ```
     '[arg]' found in:
       link       jira:board → https://...
       workspace  Jira (2 links)
       prefix     jira → Jira
     ```
   - Ask: "Which would you like to delete?"

5. **Deleting a link:**
   - Check all workspaces for references to this key
   - If referenced:
     - Show: `'[key]' is referenced in [N] workspace(s): [workspace names]`
     - Ask: "Remove from all workspaces and delete, or cancel? (remove / cancel)"
     - On cancel: stop, do nothing
     - On remove: delete key from all workspace `links` arrays, then remove from `links` section
   - If not referenced:
     - Confirm: "Delete link '[key]'? (y/n)"
     - On yes: remove from `links` section
   - Print: `Deleted link [key]` and `Removed from [N] workspace(s)` if applicable

6. **Deleting a workspace:**
   - Confirm: "Delete workspace '[name]'? Its [N] links will remain in the registry. (y/n)"
   - On yes: remove from `workspaces` section
   - Print: `Deleted workspace [name]`

7. **Deleting a prefix:**
   - Confirm: "Delete prefix '[prefix]' → '[window]'? Links with this prefix will fall back to no default window. (y/n)"
   - On yes: remove from `prefixDefaults`
   - Print: `Deleted prefix [prefix]`

8. Write back to `browser-links.json`
