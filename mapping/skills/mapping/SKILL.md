---
name: mapping
description: Central routing and recording layer — maps natural language input to plugin commands. Fires whenever Claude routes a user message to a command without an explicit slash command being typed.
---

# Mapping Skill

## Purpose

Central routing and recording layer for plugin commands. Fires whenever Claude determines a user's natural language message maps to a plugin command — not just for ambiguous input, but for any NL → command routing. Records every successful mapping so the registry grows automatically through use.

## When to fire

**Fire when:** the user's message expresses intent to run a command and they did NOT type a slash command explicitly.

**Do NOT fire when:**
- User typed a slash command explicitly (`/story:dashboard`)
- Request is clearly a question, coding task, explanation, or normal conversation — not command intent
- Claude is already mid-execution of a command

## Registry files

Two files, read in order:

1. **Shipped defaults** (read-only — starter phrases, no timestamps):
   `~/.claude/plugins/marketplaces/<pluginMarketplaceName>/mapping/.claude-plugin/phrases.json`

2. **User registry** (all tracked data lives here — grows through use):
   `~/.claude/plugins/phrases.json`

Read `pluginMarketplaceName` from `~/.claude/plugins/user-config.json` → `paths.pluginMarketplaceName`. Default: `ajudd-claude-plugins`.

Read both files (skip if missing). Use merged phrase pool for routing. Record only to user registry.

## Step 1 — Determine command and confidence

From the user's message, determine the best target command and your confidence:

| Level | Meaning |
|-------|---------|
| **High** | One clear match — no reasonable alternative |
| **Plausible** | Best guess, but another command could fit |
| **Ambiguous** | Two or more commands are equally plausible |

## Step 2 — Act on confidence

| Confidence | Action |
|-----------|--------|
| High | Run command silently → record (Step 3) |
| Plausible | Run command, append "— let me know if that's wrong" → record (Step 3) |
| Ambiguous | Ask: "Did you mean /x:y or /a:b?" → record only after user confirms |

## Step 3 — Record the mapping

After routing is decided, record to `~/.claude/plugins/phrases.json`:

**3a. Extract the phrase** — normalize the user's input:
- Short input (≤8 words): use verbatim
- Long input: extract the intent-bearing core (e.g. "show me what's going on with my stories and flag overdue ones" → "show me what's going on with my stories")

**3b. Check user registry for this command's phrases:**

- **Semantic match found** — the normalized phrase is similar to an existing phrase for this command → update that phrase object's `last_used` to today. Done.
- **No semantic match** — add a new phrase object (no `last_used` yet — set on next match):
  ```json
  { "text": "normalized phrase", "added_date": "YYYY-MM-DD" }
  ```
- **Phrase matches a DIFFERENT command** — surface conflict before proceeding:
  `"[phrase]" is mapped to /other:command. Route to /intended:command instead?`
  - Yes: remove from old command, add to new command, run intended command
  - No: run intended command this time, leave registry unchanged

**3c. Write** the updated user registry. Skip silently if write fails.

## Correction flow

When the user signals the wrong command fired ("no", "stop", "that should have been /x:y", "wrong command", "halt"):

1. Stop current action if still in progress
2. Identify the intended command (ask if not stated)
3. Find the phrase just recorded under the wrong command in `~/.claude/plugins/phrases.json`
4. Remove it from the wrong command's `phrases` array
5. Add it to the correct command's `phrases` array with `added_date: today`
6. Run the correct command
7. Confirm: `Moved "[phrase]" → /correct:command`

## Inline shortcut

When the user explicitly names the right command ("that should have been /story:dashboard", "add that to release", "remember that for /setup:local"):

- Use the most recently routed phrase as the phrase text
- Execute correction flow steps 3–7 above
- No confirmation prompt needed
