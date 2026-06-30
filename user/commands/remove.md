---
name: remove
description: Remove a known customer record from the local user store.
argument-hint: "<custId or nickname>"
---

# User Remove

Remove a record from `~/.claude/memory/known-users.json`.

## Instructions

### 1. Resolve Target

Read the store:
```bash
cat ~/.claude/memory/known-users.json 2>/dev/null || echo "{}"
```

If an argument was passed:
- Try as custId (exact key match)
- Try as nickname (scan `nickname` fields)

If no match: "No known user found for '<arg>'."
If no argument: show the full list and ask "Which custId or nickname to remove?"

### 2. Confirm

Show the record and require confirmation:
```
Remove Edie Wadsworth (custId: 1443424, US)?   yes / cancel
```

### 3. Write

Remove the entry from the JSON object and write back the updated file.

### 4. Confirm

```
Removed: Edie Wadsworth (custId: 1443424)
Known users: N remaining
```
