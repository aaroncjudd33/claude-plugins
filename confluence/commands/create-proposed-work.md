---
name: create-proposed-work
description: Create a Proposed Work planning page in Confluence for an upcoming feature — discovers relevant codebase context, drafts the page, and saves the ID to MEMORY.md
argument-hint: "[feature-name]"
---

# /confluence:create-proposed-work [feature-name]

Create a Proposed Work planning page for an upcoming feature. Use this when a feature is being actively designed or scoped — before implementation begins. The page lives as a child of the project parent and can be archived via `/confluence:archive-docs` when the feature ships.

## Steps

1. **Collect parameters** — If not provided as arguments, ask for:
   - Feature name (e.g. `Bulk Export`, `SSO Integration`)
   - Confluence space key — check `MEMORY.md` "Confluence Pages" section first; if not there, ask
   - Parent page ID — check `MEMORY.md`; if not found, search Confluence for the project parent

2. **Check for an existing page** — Search for a Proposed Work page with this feature name before creating:
   ```
   searchConfluenceUsingCql:
     cql: 'title = "<PROJECT> — Proposed Work: <Feature Name>" AND space = "<SPACE_KEY>"'
   ```
   If found, stop and tell the user: "A Proposed Work page for this feature already exists: [link]. Use `/confluence:update-docs` to edit it, or `/confluence:archive-docs` if it's ready to be archived."

3. **Discover relevant context** — Read the codebase areas most relevant to this feature:
   - Existing code in the affected modules or services
   - Related Jira stories or epics (search by feature name or ask user for a story key)
   - Any prior planning notes in `MEMORY.md` or `CLAUDE.md`

4. **Enter Plan Mode** — Use `EnterPlanMode`. Draft the Proposed Work page and present it for review before publishing.

5. **Draft the page** using this structure:

   ```markdown
   # <PROJECT> — Proposed Work: <Feature Name>

   ## Overview

   <2-3 sentences. What is this feature? What problem does it solve? Who requested it?>

   ## Scope

   - <What is in scope>
   - <What is explicitly out of scope>

   ## Approach

   <Describe the proposed implementation approach. Reference specific files, services, or patterns where relevant.>

   ## Open Questions

   | Question | Owner | Status |
   |----------|-------|--------|
   | <question> | <name> | Open |

   ## Acceptance Criteria

   - <criterion 1>
   - <criterion 2>

   ## Related

   - Jira: <story link or "TBD">
   - Branch: <branch name or "TBD">
   ```

6. **Exit Plan Mode** — Use `ExitPlanMode` to present the draft and get explicit approval before publishing.

7. **Publish to Confluence** — Create the page as a child of the project parent:

   ```
   createConfluencePage:
     spaceId: <space key>
     parentId: <project parent page ID>
     title: "<PROJECT> — Proposed Work: <Feature Name>"
     contentFormat: markdown
     body: <full drafted content>
   ```

8. **Save page ID** — Add the new page to `MEMORY.md` under the "Confluence Pages" section:

   ```markdown
   - **Proposed Work — <Feature Name>:** [<PROJECT> — Proposed Work: <Feature Name>](<url>) — ID: `<id>`
   ```

9. **Update parent index page** — Fetch the current parent index content and add the new page to the "Pages in this section" list.

## Notes

- Do not create this page for features that are already in progress — use `/confluence:update-docs` to document an existing feature's state instead
- When the feature ships, run `/confluence:archive-docs` to move this page to the Archive section
- Open Questions and Acceptance Criteria are the most valuable sections — don't leave them blank
