---
name: search
description: Search across link keys, descriptions, URLs, and workspace names
argument-hint: "[query]"
---

# /links:search [query]

Search all links and workspaces. Case-insensitive partial match across keys, descriptions, URLs, and workspace names.

## Steps

1. Read `C:\Users\ajudd\.claude\browser-links.json`

2. Search (case-insensitive) across:
   - Link keys
   - Link descriptions
   - Link URLs
   - Workspace names
   - Workspace descriptions

3. For matching links, also determine which workspaces contain them (scan `workspaces[*].links` arrays).

4. Display results grouped:

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

5. Workspaces with empty `links` arrays still appear in results — show them with "(no links)" in place of the member count.

6. If no results → "No links or workspaces matched '[query]'"
