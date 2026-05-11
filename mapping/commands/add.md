---
allowed-tools: Read, Write
description: Register a natural-language phrase to a command in the mapping registry
---

Register a phrase so Claude recognizes it as a specific command next time.

## Steps

1. **Get the phrase** — parse from args if provided (e.g., `/mapping:add "show my stories" → /story:dashboard`). Otherwise ask: "What phrase do you want to register?"

2. **Get the command** — parse from args if provided. Otherwise ask: "Which command should it trigger? (e.g., /story:dashboard)"

3. **Load the registry** — read `~/.claude/plugins/phrases.json`. If it doesn't exist, start with `{}`.

4. **Add the phrase:**
   - If the command key already exists, append to its `phrases` array (skip if already present)
   - If the command key doesn't exist, create it:
     ```json
     {
       "/story:dashboard": {
         "description": "Show open Jira stories with current status",
         "phrases": ["new phrase here"]
       }
     }
     ```
   - If creating a new command key, derive a short description from the command name

5. **Write** the updated JSON to `~/.claude/plugins/phrases.json`

6. **Confirm:** `Added "[phrase]" → [command]`
