---
name: default
description: View, set, or clear default known-user assignments — a global fallback and optional per-system overrides (e.g. vo) used when no specific user is requested.
argument-hint: "[custId-or-nickname] [system:<name>] | clear [system:<name>]"
---

# User Default

Manage default entries in `~/.claude/memory/known-users.json` — a global fallback used whenever no specific person is requested, with optional per-system overrides (e.g. `vo`).

## Instructions

### 1. Read Store

```bash
cat ~/.claude/memory/known-users.json 2>/dev/null || echo "{}"
```

Defaults live under the `_defaults` key — an array of `{ "system": null | "<name>", "custId": "<id>" }`. `system: null` is the global fallback; any other value is a per-system override that takes precedence over global when that system is in play.

### 2. No Arguments — Show Current Defaults

Resolve each entry's `custId` to a name and list:

```
Global default:  Edie Wadsworth (1443424)
vo:              Edie Wadsworth (1443424)
```

If `_defaults` is empty or missing: "No defaults set. Use `/user:default <custId-or-nickname>` to set the global default."

### 3. `clear` — Remove a Default

- `clear` alone → remove the global (`system: null`) entry, after confirming: "Clear global default (currently Edie Wadsworth)? yes / cancel"
- `clear system:<name>` → remove that system's override only, same confirmation pattern.

### 4. Set a Default

Resolve the (non-`clear`) argument to a custId using the same order as the Lookup Pattern in the `user` skill: exact custId match, then nickname, then case-insensitive name. If no match: "No known user found for '<arg>'. Use `/user:add` first."

Parse an optional `system:<name>` token from the remaining arguments (lowercase it). No `system:` token → this sets the **global** default (`system: null`).

**Validation — at most one entry per system, including global:**

- If an entry for that system already exists, show it and confirm replacement: "Global default is currently Jane Smith (7890123). Replace with Edie Wadsworth (1443424)? yes / cancel"
- A replacement means removing the existing entry for that `system` value before appending the new one — never leave two entries with the same `system`.

### 5. Write

Write the updated `_defaults` array back, leaving every customer record untouched. Format with 2-space indentation.

### 6. Confirm

```
Global default set: Edie Wadsworth (custId: 1443424)
```

or, for a system override:

```
Default for 'vo' set: Edie Wadsworth (custId: 1443424)
```
