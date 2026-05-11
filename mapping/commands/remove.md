---
allowed-tools: Read, Write
description: Remove a user-local phrase from the mapping registry
---

Remove a phrase from your personal registry. Only user-local phrases can be removed — shipped defaults (built into each plugin) are read-only.

## Steps

1. **Get the phrase** — from args or prompt: "Which phrase do you want to remove?"

2. **Search user phrase files** — check all `~/.claude/plugins/phrases/*.json` for a matching phrase. Do NOT search plugin-shipped defaults (`phrases.json` files in the marketplace) — those are read-only.

3. **If not found** — "That phrase isn't in your user registry. Shipped defaults can't be removed — only phrases you added via `/mapping:add`. Use `/mapping:list` to see what you have."

4. **If found** — show what it maps to and confirm: `Remove "[phrase]" → [command]? (yes/no)`

5. **On yes:**
   - Remove the phrase from the array
   - If the command's `phrases` array is now empty, remove that command key
   - If the JSON object is now empty (`{}`), delete the file
   - Write the updated file

6. **Confirm:** `Removed "[phrase]"`
