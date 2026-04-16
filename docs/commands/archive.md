---
name: archive
description: Archive a completed planning page — moves it under an Archive section, updates the parent index, and records the change in MEMORY.md
argument-hint: "[page-title | page-id]"
---

# /docs:archive [page-title | page-id]

Move a completed planning or proposed work page to an Archive section under the project's Confluence parent page. Use this when a feature has shipped and its planning doc is no longer active reference material.

## Steps

1. **Identify the page to archive** — Use the argument if provided. If not, list the project's Proposed Work pages from `MEMORY.md` or via Confluence search and ask the user which to archive.

2. **Find or create the Archive page** — Look for a child page titled `Archive` under the project parent. If it doesn't exist, create it as a child of the parent index page with body: `Completed planning and proposed work documents.`

3. **Move the page** — Update the page's `parentId` to the Archive page ID. See `references/confluence-patterns.md` for the update pattern. Version message: `Archived — feature completed`.

4. **Update the parent index page** — Remove the archived page from the "Pages in this section" list. Add an "Archive" entry linking to the Archive page if one isn't there yet.

5. **Update MEMORY.md** — Move the page reference from active pages to an "Archived Pages" section.

6. **Confirm completion** — Report the archived page URL and the Archive section URL.

## Notes

- Archiving does not delete the page — it remains searchable and linkable
- Only archive pages that are truly complete — if a feature was deferred or cancelled, leave it in place with a note at the top
- To archive multiple pages at once, repeat steps 2–5 for each
