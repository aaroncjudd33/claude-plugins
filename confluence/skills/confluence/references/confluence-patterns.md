# Confluence MCP Patterns

How to create and manage Confluence pages using the `claude.ai` Atlassian MCP.

Connection details (from global CLAUDE.md):
- Instance: `https://younglivingeo.atlassian.net`
- Cloud ID: `9de6eb2b-2683-44e6-89ff-c622027e09b4`

---

## Finding Pages

**By saved ID** — check the project's `MEMORY.md` "Confluence Pages" section first.

**By title search:**
```
searchConfluenceUsingCql:
  cql: 'title = "<Project Name>" AND space = "<SPACE_KEY>"'
```

**All children of a parent page:**
```
searchConfluenceUsingCql:
  cql: 'ancestor = <parent page ID> AND space = "<SPACE_KEY>"'
```

**Get a specific page by ID:**
```
getConfluencePage: pageId = "<id>"
```

---

## Creating the Parent Index Page

Create this first — it is the "folder" that all other pages live under.

```
createConfluencePage:
  spaceId: <space key, e.g. "BP2">
  title: "<PROJECT NAME>"
  contentFormat: markdown
  body: |
    This section documents the **<Project Name>** service.

    ## Pages in this section

    - **Project Overview** — Purpose, tech stack, key files, environment config, and current status
    - **Architecture & Data Flow** — Data flows, data models, infrastructure stacks
    - **Local Dev Runbook** — Step-by-step local setup and test run guide
    - **API Reference** — All public endpoints: auth, request/response, quirks
    - **Known Issues & Technical Debt** — Active bugs and architectural debt
    - **Test Coverage Analysis** — Coverage gaps ranked by risk

    ## Quick Links

    - GitHub: <repo URL>
    - Branch strategy: `develop` → dev/stage, `master` → prod
```

Save the returned page ID immediately — it is the `parentId` for every child page.

---

## Creating Child Pages

Always include `parentId` pointing to the parent index page.

```
createConfluencePage:
  spaceId: <space key>
  parentId: <parent page ID>
  title: "<PROJECT> — <Page Name>"
  contentFormat: markdown
  body: <full markdown content>
```

Create in order: Overview → Architecture → Runbook → API Reference → Known Issues → Test Coverage

---

## Updating a Page

Always fetch current content first with `getConfluencePage` so you don't overwrite manually curated sections.

```
updateConfluencePage:
  pageId: <existing page ID>
  title: <same title — must be included>
  contentFormat: markdown
  body: <full updated markdown content>
  versionMessage: "<brief description of what changed>"
```

Version message examples:
- `"Added new Lambda handler to architecture diagram"`
- `"Updated SSM parameter list after prod deploy"`
- `"Archived — feature completed"`

---

## Moving a Page (used by archive-docs)

To move a Proposed Work page under the Archive page, update its `parentId`. Always fetch and preserve the existing body.

```
updateConfluencePage:
  pageId: <page to move>
  parentId: <archive page ID>
  title: <existing title — unchanged>
  contentFormat: markdown
  body: <existing body — fetched with getConfluencePage>
  versionMessage: "Archived — feature completed"
```

---

## Saving Page IDs to MEMORY.md

After creating pages, save all IDs and URLs to the project `MEMORY.md` under a "Confluence Pages" section:

```markdown
## Confluence Pages

- **Parent:** [<PROJECT>](<url>) — ID: `<id>`
- **Overview:** [<PROJECT> — Project Overview](<url>) — ID: `<id>`
- **Architecture:** [<PROJECT> — Architecture & Data Flow](<url>) — ID: `<id>`
- **Runbook:** [<PROJECT> — Local Dev Runbook](<url>) — ID: `<id>`
- **API Reference:** [<PROJECT> — API Reference](<url>) — ID: `<id>`
- **Known Issues:** [<PROJECT> — Known Issues & Technical Debt](<url>) — ID: `<id>`
- **Test Coverage:** [<PROJECT> — Test Coverage Analysis](<url>) — ID: `<id>`
```

Page URL pattern:
```
https://younglivingeo.atlassian.net/wiki/spaces/<SPACE>/pages/<PAGE_ID>
```

---

## Markdown Formatting Tips

Confluence renders standard markdown well:
- `## Heading` for sections
- `| Col | Col |` tables (always include the separator row `|---|---|`)
- Fenced code blocks with language hint: ` ```bash `, ` ```typescript `
- `**bold**` for emphasis
- Bullet lists with `-`

Avoid inline HTML — use markdown equivalents. Confluence markdown does not render inline HTML reliably.
