---
name: edit-workspace
description: Modify a workspace — add or remove links, update description, or delete it
argument-hint: "[name]"
---

# /links:edit-workspace [name]

Edit an existing workspace interactively.

## Steps

1. Read `C:\Users\ajudd\.claude\browser-links.json`

2. Find workspace by name (case-insensitive). If not found → "No workspace named '[name]'. Run `/links:add-workspace [name]` to create it." Stop.

3. Show current state:
   ```
   Workspace: BPT2-6258  (story)
   Description: GLB Shopify
   Links (3):
     story:BPT2-6258        GLB Shopify
     pr:virtual-office#789  GLB Shopify PR
     actions:virtual-office#run-456  Actions run
   ```

4. Accept edit commands (one at a time or multiple):
   ```
   add [key]           add an existing link key to this workspace
   remove [key]        remove a link key from this workspace (does not delete the link itself)
   description [text]  update the workspace description
   delete              delete this workspace entirely (does not delete its links)
   done                save and exit
   ```

   **Known limitation:** workspace `type` cannot be changed via edit. To change the type, delete the workspace and recreate it with `/links:add-workspace`.

5. For `add [key]`:
   - Verify the key exists in `links` section. If not → "Link '[key]' not found. Add it first with `/links:add-link`."
   - Append to workspace's `links` array

6. For `delete`:
   - Confirm: "Delete workspace '[name]'? Its [N] links will remain in the registry. (y/n)"
   - On yes: remove from `workspaces` section

7. After each command, show updated state and re-prompt until user says `done`

8. Write back to `browser-links.json` on `done`

9. Print: `Saved workspace '[name]'`
