---
name: archive-docs
description: Archive completed proposed work / planning pages in Confluence
argument-hint: [page-title | page-id]
---

# Project Documentation: Archive

Move a completed planning or proposed work page to an Archive section under the project's Confluence parent page. Use this when a feature has shipped and its planning doc is no longer active reference material — but shouldn't be deleted.

## Instructions

When this command is invoked:

1. **Identify the page to archive** — Use the argument if provided (page title or ID). If not provided, list the project's Proposed Work pages found in `MEMORY.md` or via Confluence search and ask the user which to archive.

2. **Find or create the Archive section** — Look for a child page titled `Archive` under the project parent page. If it doesn't exist, create it:
   ```
   createConfluencePage:
     parentId: <project parent page id>
     title: "Archive"
     body: "Completed planning and proposed work documents."
   ```

3. **Move the page** — Update the page to set its `parentId` to the Archive page:
   ```
   updateConfluencePage:
     pageId: <page to archive>
     parentId: <archive page id>
     versionMessage: "Archived — feature completed"
   ```

4. **Update the parent index page** — Remove the archived page from the "Pages in this section" list and optionally add an "Archive" entry linking to the Archive page.

5. **Update MEMORY.md** — Move the page reference from the active pages section to an "Archived Pages" section.

6. **Confirm completion** — Report the archived page URL and the Archive section URL.

## Notes

- Archiving does not delete the page — it remains searchable and linkable
- Only archive pages that are truly complete — if a feature was deferred or cancelled, leave it in place with a note at the top
- If archiving multiple pages at once, repeat steps 2–5 for each
