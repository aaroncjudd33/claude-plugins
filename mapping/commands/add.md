---
allowed-tools: Read, Write
description: Register a natural-language phrase to a command in the mapping registry
---

Register a phrase so Claude recognizes it as a specific command next time.

## Steps

1. **Get the phrase** — parse from args if provided (e.g., `/mapping:add "show my stories" → /story:dashboard`). Otherwise ask: "What phrase do you want to register?"

2. **Get the command** — parse from args if provided. Otherwise ask: "Which command should it trigger? (e.g., /story:dashboard)"

3. **Load the registry** — read `~/.claude/plugins/phrases.json`. If it doesn't exist, start with `{}`.

4. **Duplicate / conflict check** — before writing, scan all phrases across all commands (skip the `_config` key):

   - **Exact match, same command:** phrase already registered here — skip silently, confirm `"[phrase]" is already mapped to [command]`.
   - **Exact match, different command:** block. Say: `"[phrase]" is already mapped to [other-command]. Remove it there first with /mapping:remove, or pick a different phrase.`
   - **Semantic near-match, different command:** warn and ask. Say: `"[phrase]" is similar to "[existing phrase]" which maps to [other-command]. Add anyway?` Proceed on yes, abort on no.
   - **Semantic near-match, same command:** no warning needed — close variants on the same command are fine.

   Semantic similarity judgment: use LLM judgment — phrases are "near-matches" if a user saying one could reasonably mean the other (e.g. "log me in" vs "login to aws"). Err toward warning rather than silently adding.

5. **Add the phrase:**
   - If the command key already exists, append to its `phrases` array
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

6. **Write** the updated JSON to `~/.claude/plugins/phrases.json`

7. **Confirm:** `Added "[phrase]" → [command]`
