# Confluence Interaction Patterns

Use the `claude.ai` Atlassian MCP for all Confluence operations. The connection details are in the global `CLAUDE.md`.

---

## Finding an Existing Space or Parent Page

```
# Search for existing pages
searchConfluenceUsingCql: cql = "title = \"<Project Name>\" AND space = \"<SPACE_KEY>\""

# Get a page by ID
getConfluencePage: pageId = "<id>"

# List pages in a space
getPagesInConfluenceSpace: spaceId = "<id>"

# Get child pages of a parent
getConfluencePageDescendants: pageId = "<parentId>"
```

---

## Creating the Parent Index Page

Create this first — all other pages are children of it.

```
createConfluencePage:
  spaceId: <space id>
  title: "<PROJECT NAME>"
  contentFormat: markdown
  body: |
    This section documents the **<Project Name>** service.

    ## Pages in this section

    - **[Project Overview]** — Purpose, tech stack, key files, environment config, and current status
    - **[Architecture & Data Flow]** — Data flows, data models, infrastructure stacks
    - **[Local Dev Runbook]** — Step-by-step local setup and test run guide
    - **[API Reference]** — All public endpoints: auth, request/response, quirks
    - **[Known Issues & Technical Debt]** — Active bugs and architectural debt
    - **[Test Coverage Analysis]** — Coverage gaps ranked by risk

    ## Quick Links

    - GitHub: <repo URL>
    - Branch strategy: `develop` → dev + stage, `master` → prod
```

---

## Creating Child Pages

Always set `parentId` to the parent page created above.

```
createConfluencePage:
  spaceId: <space id>
  parentId: <parent page id>
  title: "<PROJECT> — Project Overview"
  contentFormat: markdown
  body: <full markdown content>
```

Create pages in order: Overview → Architecture → Runbook → API Reference → Known Issues → Test Coverage

---

## Updating an Existing Page

```
updateConfluencePage:
  cloudId: 9de6eb2b-2683-44e6-89ff-c622027e09b4
  pageId: <existing page id>
  title: <same or updated title>
  contentFormat: markdown
  body: <full updated markdown content>
  versionMessage: "Updated: <brief description of what changed>"
```

Always fetch the current page first to preserve any manually added content not in the codebase.

---

## Finding Project Docs for update-docs / archive-docs

Store page IDs in the project `MEMORY.md` after creating them. If IDs are not in memory, search:

```
searchConfluenceUsingCql:
  cql = "title ~ \"<PROJECT>\" AND space = \"<SPACE_KEY>\" AND ancestor = \"<parent page id>\""
```

---

## Markdown Formatting Tips

Confluence renders standard markdown well. Use:
- `## Heading` for sections
- `| Col | Col |` for tables (always include header separator row)
- ` ``` ` fenced code blocks with language hint for code and shell commands
- `**bold**` for emphasis, not ALL CAPS
- Bullet lists with `-` not `*`

Avoid HTML — use markdown equivalents. Confluence markdown does not support inline HTML reliably.

---

## After Creating Pages

Save page IDs to the project `MEMORY.md` under a "Confluence Pages" section:

```markdown
## Confluence Pages (<SPACE> space, parent page <id>)
- Parent index:       https://... (page ID <id>)
- Project Overview:   https://... (page ID <id>)
- Architecture:       https://... (page ID <id>)
- Runbook:            https://... (page ID <id>)
- API Reference:      https://... (page ID <id>)
- Known Issues:       https://... (page ID <id>)
- Test Coverage:      https://... (page ID <id>)
```
