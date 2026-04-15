---
name: update-docs
description: Update existing Confluence project documentation to reflect current codebase state
argument-hint: "[page-name | all]"
---

# /confluence:update-docs [page-name | all]

Refresh existing Confluence documentation to reflect the current state of the codebase. Use this after a significant feature, refactor, or bug fix — not after every commit.

## Steps

1. **Find existing pages** — Check `MEMORY.md` for saved Confluence page IDs. If not found, search using `searchConfluenceUsingCql` for pages matching the project name in the target space.

2. **Determine scope** — If an argument is provided (e.g. `architecture`, `runbook`, `all`), update only those pages. If no argument, ask the user which pages need updating or default to `all`.

3. **For each page to update:**

   a. **Fetch current content** using `getConfluencePage` — read what's already there.

   b. **Re-discover relevant codebase sections** using the `confluence` skill discovery checklist for that page type.

   c. **Identify what's changed or stale** — compare doc content against current code. Look for:
      - File paths that no longer exist
      - New files or components not yet documented
      - Changed schemas, endpoints, or environment config
      - Resolved issues still listed as open
      - New issues not yet documented

   d. **Update only what has changed** — preserve accurate sections. Add a brief change note at the top of updated sections: `> Updated: <date> — <what changed>`

4. **Publish updates** using `updateConfluencePage`. See `references/confluence-patterns.md` for version messages and update patterns.

5. **Update MEMORY.md** if any page IDs have changed.

## Scope Keywords

| Argument | Pages Updated |
|----------|--------------|
| `overview` | Project Overview |
| `architecture` | Architecture & Data Flow |
| `runbook` | Local Dev Runbook |
| `api` | API Reference |
| `issues` | Known Issues & Technical Debt |
| `coverage` | Test Coverage Analysis |
| `index` | Parent index page only |
| `all` | All pages |
| *(none)* | Ask the user |

## Notes

- Always fetch current page content before updating — never overwrite manually curated content
- If a major restructure is needed, run `init-docs` instead
- Proposed Work pages are intentionally excluded from all scope keywords including `all` — they are planning documents, not state-of-the-world docs. Edit them directly in Confluence or recreate via `/confluence:create-proposed-work`. When a feature ships, archive the page with `/confluence:archive-docs`
