---
allowed-tools: Read, Write
description: Remove a phrase from your personal mapping registry
---

Remove a phrase from `~/.claude/plugins/phrases.json`. Shipped defaults cannot be removed — only phrases that live in your personal registry.

## Steps

1. **Get the phrase** — from args or prompt: "Which phrase do you want to remove?"

2. **Search** `~/.claude/plugins/phrases.json` for a matching phrase across all command entries.

3. **If not found** — "That phrase isn't in your registry. Shipped defaults (the empty set that ships with the plugin) can't be removed anyway. Use `/mapping:list` to see what you have."

4. **If found** — confirm: `Remove "[phrase]" → [command]? (yes/no)`

5. **On yes:**
   - Remove the phrase from the array
   - If the `phrases` array is now empty, remove that command key
   - If the whole file is now `{}`, delete it
   - Otherwise write the updated file

6. **Confirm:** `Removed "[phrase]"`
