---
name: mapping
description: Background skill — do not run directly. Use /mapping:add, /mapping:list, /mapping:remove for manual phrase management. Loaded automatically to resolve ambiguous user input to the correct command.
---

# Mapping Skill

Background skill — do not run directly.

## Purpose

When the user's message is not a slash command and the intended command is unclear, consult the phrase registry before asking for clarification or guessing. The registry maps natural-language phrases to specific plugin commands.

## When to trigger this lookup

Trigger condition: user sends a message that looks like an intent to run a command, but does not use `/plugin:command` syntax, and you are not already confident about what they want.

Examples that should trigger a lookup:
- "show me what's going on with my tickets"
- "kick off a release"
- "start my day"
- "what did I work on yesterday"

Do NOT trigger when:
- The user typed a slash command explicitly
- The request is clearly a question, coding task, or explanation — not a command intent
- The intent is already obvious from context

## Registry files

Two files, read in order (user file takes precedence on conflict):

1. **Shipped defaults** (empty for new installs, may be populated in future plugin updates):
   `~/.claude/plugins/marketplaces/<pluginMarketplaceName>/mapping/.claude-plugin/phrases.json`

2. **User registry** (all real data lives here — fills in through use):
   `~/.claude/plugins/phrases.json`

Read `pluginMarketplaceName` from `~/.claude/plugins/user-config.json` → `paths.pluginMarketplaceName`. Default: `ajudd-claude-plugins`.

## Lookup procedure

1. Read both files (skip if not found)
2. Merge into one map: phrase → command (user file wins on conflict)
3. Match the user's input semantically against all phrases — use LLM judgment, not exact string match
4. Act on the result:

| Result | Action |
|--------|--------|
| One clear match | Run the command. Say: "Running /x:y — let me know if that's wrong." |
| Multiple plausible matches | Ask: "Did you mean /x:y or /a:b?" |
| No match found | Ask what they wanted, then offer to add the phrase |

## Auto-add flow (no match found)

1. Ask: "I don't have a mapping for that. Which command did you want?"
2. Once confirmed: append the phrase to `~/.claude/plugins/phrases.json` under the correct command key
3. Confirm: "Added — I'll recognize that next time."

## Inline shortcut

When the user says:
- "that should have been /story:dashboard"
- "add that phrase to dashboard"
- "remember that for /release:create"

...immediately add using the most recent ambiguous phrase as the phrase and the named command as the target. No confirmation prompt — just add and confirm.
