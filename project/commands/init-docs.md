---
name: init-docs
description: Deep-discover a codebase and generate a full set of Confluence documentation pages
argument-hint: "[confluence-space-key] [parent-page-title]"
---

# Project Documentation: Init

Perform a deep codebase discovery and generate the full standard set of Confluence documentation pages for this project. This command should be run once when a project is new to you or has never been documented.

## Instructions

When this command is invoked:

1. **Check for CLAUDE.md** — If no `CLAUDE.md` exists at the repo root, run `/init` to create one. Wait for completion.

2. **Collect parameters** — If not provided as arguments, ask the user for:
   - Confluence space key (e.g. `BP2`)
   - Parent page title or ID (create a new parent if none exists)
   - Project name / acronym (e.g. `MMC`, `Mass Marketing Consent`)
   - GitHub repo URL (check git remote if not provided)

3. **Enter Plan Mode** — Use `EnterPlanMode`. In plan mode, perform the full discovery below and present the documentation plan before writing anything to Confluence.

4. **Deep Discovery Phase** — Follow the `project-docs` skill discovery checklist. Read:
   - `CLAUDE.md`, `README.md`
   - All build/package files (`package.json`, `*.csproj`, `pyproject.toml`, `build.gradle`)
   - Environment/config files (`cdk.json`, `cdk.config.ts`, `.env.example`, `appsettings.json`)
   - Lambda/handler entry points — trace each data flow end to end
   - IaC files (CDK stacks, Terraform, CloudFormation) — inventory all infrastructure
   - Route/controller definitions — every public API endpoint
   - Test setup files and a sample of test files — understand what is and isn't tested
   - `MEMORY.md` in the project memory directory
   - Search source for TODO/FIXME/HACK comments

5. **Query Jira (optional)** — Search for open epics, bugs, or tech debt tickets linked to this project. Use findings to populate Known Issues.

6. **Draft all pages** in the plan — show the outline and key content for each of the 7 standard pages (see skill). Present this for user approval before publishing.

7. **Exit Plan Mode** — Use `ExitPlanMode` to present the plan and get approval.

8. **Publish to Confluence** — After approval, create pages in this order:
   - Parent index page first
   - Then child pages: Overview → Architecture → Runbook → API Reference → Known Issues → Test Coverage
   - Use the Atlassian MCP `createConfluencePage` with `parentId` for all child pages
   - Content format: `markdown`

9. **Save page IDs** — After creation, save all page URLs and IDs to the project `MEMORY.md` under a "Confluence Pages" section.

10. **Update CLAUDE.md** — Add a "Documentation" section to `CLAUDE.md` with links to the Confluence parent page.

## Output

When complete, report:
- Links to all created pages
- Any sections where discovery was incomplete (ask user to fill in)
- Suggested next steps (e.g. Proposed Work page if feature planning is active)
