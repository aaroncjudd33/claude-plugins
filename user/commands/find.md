---
name: find
description: Search known customers by country, name, nickname, or notes.
argument-hint: "<query>"
---

# User Find

Search `~/.claude/memory/known-users.json` for member accounts matching a query.

## Instructions

### 1. Read Store

```bash
cat ~/.claude/memory/known-users.json 2>/dev/null || echo "{}"
```

If the file is empty or missing: "No known users yet. Use `/user:add` to add the first one."

### 2. Parse Query

Accept free text. Parse special filters first, then apply text search to remaining terms:

| Pattern | Filter |
|---------|--------|
| `country:XX` | Match `country` field (case-insensitive, e.g. `country:us`, `country:AU`) |
| `id:NNNN` | Match exact custId |
| Anything else | Case-insensitive substring match against `name`, `nickname`, and `notes` |

Multiple terms are ANDed: `country:AU downline` → Australian members whose notes contain "downline".

**No argument:** list all records.

### 3. Display Results

Present as a compact list, one record per line:

```
custId      Name                  Country  Nickname   Notes
──────────────────────────────────────────────────────────────────
1443424     Edie Wadsworth        US       edie       Sponsor with downline, used for VO rank tests
7890123     Jane Smith            AU       aussie     Australian member, tests international shipping flow

2 results
```

If no matches: "No known users match '<query>'."

If exactly one match: also offer a follow-up action line:
```
Use custId 1443424 in this session? (yes / copy / skip)
```
- **yes:** confirm "Using Edie Wadsworth (1443424)" — the custId is now in context for the current task
- **copy:** output the custId on its own line for easy copying
- **skip:** no action
