---
name: init-docs
description: Deep-discover a codebase and generate a full set of Confluence documentation pages
argument-hint: "[space-key] [parent-page-title]"
---

# /confluence:init-docs

Perform a deep codebase discovery and generate the full standard set of Confluence documentation pages for this project. Run once when a project has never been documented.

## Steps

1. **Check for CLAUDE.md** — If none exists at the repo root, run `/session:start` to initialize the project (which creates CLAUDE.md). If `session` is not installed, create a minimal CLAUDE.md manually: include the project name, tech stack, key commands, and any gotchas. Wait for completion before proceeding.

2. **Collect parameters** — If not provided as arguments, ask for:
   - Confluence space key (e.g. `BP2`)
   - Parent page title (or confirm a new one should be created)
   - Project name / acronym (e.g. `MMC`, `Mass Marketing Consent`)
   - GitHub repo URL (check `git remote` if not provided)

3. **Enter Plan Mode** — Use `EnterPlanMode`. Perform full discovery and present the documentation plan before writing anything.

4. **Deep Discovery Phase** — Follow the `confluence` skill discovery checklist. The skill defines exactly what to read for each page type.

5. **Query Jira (optional)** — Search for open epics, bugs, or tech debt tickets linked to this project. Use findings to populate Known Issues.

6. **Draft all pages** following the `confluence` skill page content standards. Show the full outline and key content for each page. Wait for approval before publishing.

7. **Exit Plan Mode** — Use `ExitPlanMode` to present the plan and get explicit approval.

8. **Publish to Confluence** — After approval, create pages using the Atlassian MCP. See `references/confluence-patterns.md` for exact tool usage, parent/child structure, and content format. Create in this order:
   - Parent index page first
   - Child pages in order: Overview → Architecture → Runbook → API Reference → Known Issues → Test Coverage

9. **Save page IDs** — After creation, save all page URLs and IDs to the project `MEMORY.md` under a "Confluence Pages" section.

10. **Update CLAUDE.md** — Add a "Documentation" section with a link to the Confluence parent page.

## Output

Report:
- Links to all created pages
- Any sections where discovery was incomplete (ask user to fill in)

After reporting, ask: "Is any feature currently being planned or scoped for this project? If so, run `/confluence:create-proposed-work` to create a Proposed Work planning page."
