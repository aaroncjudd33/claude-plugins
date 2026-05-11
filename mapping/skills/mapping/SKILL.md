---
name: mapping
description: Background skill — do not run directly. Use /mapping:add, /mapping:list, /mapping:remove for manual phrase management. Loaded automatically to resolve ambiguous user input to the correct command.
---

# Mapping Skill

Background skill — do not run directly.

## Purpose

When the user's message is not a slash command and the intended command is unclear, consult the phrase registry before asking for clarification or guessing. This registry maps natural-language phrases to specific plugin commands.

## When to trigger this lookup

Trigger condition: user sends a message that looks like an intent to run a command, but does not use `/plugin:command` syntax, and you are not already confident about what they want.

Examples that should trigger a lookup:
- "show me what's going on with my tickets"
- "kick off a release"
- "check my jira"

Do NOT trigger when:
- The user typed a slash command explicitly
- The request is clearly a question, coding task, or explanation — not a command intent
- The intent is already obvious from context

## Registry file locations

Plugin-shipped defaults (versioned with each plugin):
```
~/.claude/plugins/marketplaces/<pluginMarketplaceName>/<plugin>/.claude-plugin/phrases.json
```

User-local additions (personal, not in the repo):
```
~/.claude/plugins/phrases/<plugin>.json
```

Read `pluginMarketplaceName` from `~/.claude/plugins/user-config.json` → `paths.pluginMarketplaceName`. Default: `ajudd-claude-plugins`.

## Lookup procedure

1. Read `~/.claude/plugins/user-config.json` → get `paths.pluginMarketplaceName`
2. Read `~/.claude/plugins/marketplaces/<name>/.claude-plugin/marketplace.json` → list all plugin names
3. For each plugin, read (if the file exists):
   - `~/.claude/plugins/marketplaces/<name>/<plugin>/.claude-plugin/phrases.json` — shipped defaults
   - `~/.claude/plugins/phrases/<plugin>.json` — user additions (take precedence on conflict)
4. Flatten into a single map: phrase → command
5. Match the user's input (semantic/fuzzy — use LLM judgment, not exact string match)
6. Act on the result:

| Result | Action |
|--------|--------|
| One clear match | Run the command. Brief note: "Running /x:y — say something if that's wrong." |
| Multiple plausible matches | Ask: "Did you mean /x:y or /a:b?" |
| No match found | Ask what command they wanted, then offer to add the phrase (see below) |

## Auto-add flow (no match found)

When no match is found:
1. Ask: "I don't have a mapping for that. Which command did you want? (e.g., /story:dashboard)"
2. Once the user confirms: call `/mapping:add` with the phrase and command
3. Confirm: "Added — I'll recognize that next time."

## Inline shortcut

When the user says something like:
- "that should have been /story:dashboard"
- "add that phrase to dashboard"
- "remember that for /release:create"
- "that phrase should trigger X"

...treat it as an immediate add: use the most recent ambiguous phrase as the phrase to register, the named command as the target. No confirmation needed — just add and confirm.
