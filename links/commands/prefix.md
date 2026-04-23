---
name: prefix
description: Add or edit a prefix-to-window mapping in prefixDefaults. Controls which Edge window a link opens in based on its key prefix.
argument-hint: "<prefix> [window-name]"
---

# /links:prefix <prefix> [window-name]

Add or update a prefix → window mapping in `browser-links.json`.

Prefix defaults determine which Edge window a link opens in when no explicit `window` field is set on the link. For example, prefix `jira` → window `Jira` means all `jira:*` links open in the Jira window by default.

## Steps

1. Read `~/.claude/browser-links.json`

2. **If no arguments provided:**
   - Ask: "What would you like to do? add / edit / view all"
   - **view all** — print the full `prefixDefaults` map as a table:
     ```
     Prefix     Window
     --------   --------
     jira       Jira
     git        Github
     ...
     ```
   - **add / edit** — ask for prefix, then proceed to step 3

3. Parse `prefix` and optional `window-name` from arguments.

4. **If prefix does not exist → Create mode:**
   - If `window-name` not provided, ask for it
   - Add to `prefixDefaults`:
     ```json
     "prefix": "WindowName"
     ```
   - Write back to `browser-links.json`
   - Print: `Added prefix [prefix] → [window-name]`

5. **If prefix exists and `window-name` provided → Update:**
   - Overwrite the existing mapping
   - Write back to `browser-links.json`
   - Print: `Updated prefix [prefix]: [old-window] → [new-window]`

6. **If prefix exists and no `window-name` provided → Offer to edit:**
   - Show: `[prefix] → [current window-name]`
   - Ask: "Update window name? (enter new name or press enter to cancel)"
   - If new name provided: update, write back, print: `Updated prefix [prefix]: [old] → [new]`
   - If cancelled: do nothing
