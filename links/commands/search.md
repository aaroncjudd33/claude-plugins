---
name: search
description: Search across link keys, descriptions, URLs, and workspace names
argument-hint: "<query> [-w | -l | -a]"
---

# /links:search <query> [-w | -l | -a]

Search links and workspaces. Case-insensitive partial match across keys, descriptions, URLs, and workspace names.

## Flags

- `-w` — search workspaces only
- `-l` — search link keys, descriptions, and URLs only
- `-a` — search all (default)

## Steps

1. Read `~/.claude/browser-links.json`

2. Parse any flag from the argument (`-w`, `-l`, `-a`). Default scope is all.

3. If no query provided, ask: "What are you looking for?"

4. Search (case-insensitive) across scoped data:
   - **Links** (`-l` or `-a`): key, description, URL
   - **Workspaces** (`-w` or `-a`): name, description

5. For matching links, also determine which workspaces contain them (scan `workspaces[*].links` arrays).

6. Display results grouped:

```
Workspaces (2)
  BPT2-6258       GLB Shopify
  Jira            Core Jira navigation

Links (3)
  story:BPT2-6258   GLB Shopify               https://younglivingeo.atlassian.net/browse/BPT2-6258   [BPT2-6258]
  jira:board        BPT2 board filtered to me  https://younglivingeo.atlassian.net/...                [Jira]
  jira:calendar     Jira/CAB calendar view     https://younglivingeo.atlassian.net/...                [Jira]
```

   The bracketed value at the end of each link row lists its workspaces (or blank if none).
   Workspaces with empty `links` arrays still appear in results — show them with "(no links)" in place of the member count.

7. If no results → "No matches for '[query]'"

8. After displaying results, ask: "Open any of these? Enter a key or workspace name, or press enter to skip."
   - If a valid key or workspace name is entered → run `/links:open <value>`
   - If blank or unrecognized → do nothing
