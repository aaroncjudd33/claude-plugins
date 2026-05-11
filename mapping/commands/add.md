---
allowed-tools: Read, Write
description: Register a natural-language phrase to a command in the mapping registry
---

Register a phrase so Claude recognizes it next time as a specific command.

## Steps

1. **Get the phrase** — if provided as an argument (e.g., `/mapping:add "show my stories" → /story:dashboard`), parse it. Otherwise ask: "What phrase do you want to register?"

2. **Get the command** — if provided as an argument, use it. Otherwise ask: "Which command should it trigger? (e.g., /story:dashboard)"

3. **Derive the plugin** — extract from the command prefix. `/story:dashboard` → plugin `story`. `/release:create` → plugin `release`.

4. **Load the user phrases file** — read `~/.claude/plugins/phrases/<plugin>.json` if it exists. If not, start with `{}`.

5. **Add the phrase:**
   - If the command key already exists, append to its `phrases` array (avoid duplicates)
   - If the command key does not exist, create it:
     ```json
     {
       "/story:dashboard": {
         "description": "<brief description of what the command does>",
         "phrases": ["the new phrase here"]
       }
     }
     ```
   - Derive a short description from the command name if creating a new key

6. **Write** the updated JSON to `~/.claude/plugins/phrases/<plugin>.json`

7. **Confirm:** `Added "[phrase]" → [command]`
