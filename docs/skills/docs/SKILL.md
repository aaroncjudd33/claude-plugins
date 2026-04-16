---
name: docs
description: >
  Provides implementation context for the /docs:init,
  /docs:update, /docs:archive, and
  /docs:propose commands.
  Load only when one of those commands is actively running — not in
  response to general requests to document, write up, or describe anything.
---

# Docs Skill

Guides Claude through deep codebase discovery and structured documentation generation, publishing results as a structured set of Confluence pages. Used by the `init`, `update`, and `archive` commands.

---

## Atlassian Connection

Defined in the global `CLAUDE.md`. Always use these without asking:

- Instance: `https://younglivingeo.atlassian.net`
- Cloud ID: `9de6eb2b-2683-44e6-89ff-c622027e09b4`
- Auth: Handled by the `claude.ai` Atlassian MCP

For tool usage patterns (createConfluencePage, updateConfluencePage, parentId structure, version messages), see `references/confluence-patterns.md`.

---

## Page Hierarchy

Every project gets a parent index page in Confluence. All other pages are children of that parent — think of it as a folder. The Archive page (created by `archive-docs`) is also a child of the parent, with completed Proposed Work pages nested under it.

```
<PROJECT>                          ← parent index page (the "folder")
  ├── <PROJECT> — Project Overview
  ├── <PROJECT> — Architecture & Data Flow
  ├── <PROJECT> — Local Dev Runbook
  ├── <PROJECT> — API Reference
  ├── <PROJECT> — Known Issues & Technical Debt
  ├── <PROJECT> — Test Coverage Analysis
  ├── <PROJECT> — Proposed Work: <Feature>   ← created by propose
  └── Archive                                ← created by archive
        └── <PROJECT> — Proposed Work: <completed feature>
```

| # | Page Title Pattern | Purpose |
|---|-------------------|---------|
| 0 | `<PROJECT>` | Parent index — quick links and page directory |
| 1 | `<PROJECT> — Project Overview` | What it does, tech stack, key files, database, design patterns, status |
| 2 | `<PROJECT> — Architecture & Data Flow` | System flows (with ASCII diagrams), data models, infrastructure stacks, known concerns |
| 3 | `<PROJECT> — Local Dev Runbook` | Step-by-step local setup, CLI reference, SQL/DB quick reference, break-glass steps |
| 4 | `<PROJECT> — API Reference` | Every public endpoint: method, path, auth, request body, response codes, quirks |
| 5 | `<PROJECT> — Known Issues & Technical Debt` | Active bugs, architectural debt, missing features — severity-ranked |
| 6 | `<PROJECT> — Test Coverage Analysis` | What is tested, what is not, coverage gaps ranked by risk |
| 7 | `<PROJECT> — Proposed Work: <Feature>` | Planning docs for upcoming features — created by `propose`, archived when complete |

---

## Discovery Checklist

Before writing any page, read these sources.

**Monorepo note:** If the repo root contains multiple services or packages, ask the user which service to document before starting discovery. Scope all file reads to that service's subdirectory — do not attempt to document the entire monorepo as a single project.

### Always Read
- `CLAUDE.md` at repo root — commands, architecture summary, key constants
- `README.md` if present
- `package.json` / `pyproject.toml` / `*.csproj` / `build.gradle` — tech stack, scripts, dependencies
- `cdk.json` / `cdk.config.ts` / environment config files — environments, accounts, feature flags
- `.github/workflows/` — CI/CD pipeline structure

### Architecture & Data Flow
- Lambda/handler entry points — trace the full request/event path
- IaC files (CDK stacks, Terraform modules, CloudFormation) — what infrastructure exists
- Queue/event definitions — EventBridge rules, SQS queues, SNS topics
- External API clients — what third-party services are called and how

### Local Dev Runbook
- Scripts in `package.json` / `Makefile` — what commands exist and what they do
- Docker-related files — `docker-compose.yml`, any `docker run` commands in CLAUDE.md
- Test setup files — `setup-tests.ts`, `conftest.py`, etc.
- Any `.env.example` or config template files

### API Reference
- Route/controller definitions — every exposed HTTP endpoint
- Request/response types — input validation schemas, response shapes
- Auth middleware — how requests are authenticated and authorized

### Known Issues & Tech Debt
- TODO/FIXME/HACK comments in source code
- `MEMORY.md` "Known Issues" section in the project memory
- Any open Jira epics or bugs related to this project

### Test Coverage
- Test files — what is tested behaviorally (not just which files have tests)
- Coverage reports if present (`coverage/` directory)
- What is explicitly NOT tested (integration gaps, mocked-out dependencies)

---

## Page Content Standards

### Project Overview
Must include:
- Plain-language "What It Does" section (2–4 sentences, no jargon)
- Tech stack table (Layer → Technology)
- Key files table (File path → Purpose) — only the 6–10 most important files
- Database section: schema overview, connection details per environment, key tables/columns
- Design patterns used (with brief explanation of each)
- Status section: active/deprecated, recent changes, known limitations

### Architecture & Data Flow
Must include:
- System overview paragraph
- One ASCII flow diagram per data flow direction (inbound/outbound/both)
- Echo prevention or idempotency logic if present
- Data model definitions (key fields only, not every attribute)
- Infrastructure stacks table (Stack → Contents → Deletion policy)
- Known architecture concerns table (Severity → Issue)

ASCII diagram format:
```
Source System
  │
  ▼
Queue / Gateway
  │
  ▼
Lambda Handler
  1. Step one
  2. Step two
  3. Step three
```

### Local Dev Runbook
Must include:
- Numbered steps in order (auth → runtime version → dependencies → local services → build → deploy → test)
- Exact commands — copy-pasteable, no paraphrasing
- Expected output or success indicators for slow steps
- Connection details table for any local services (host, user, password)
- SQL/DB quick reference section if the project uses a database
- Break-glass reinstall steps for dependency issues

### API Reference
Must include:
- One section per endpoint
- Method + path as heading
- Auth requirements
- Request body with field types and whether required/optional
- Response codes and what each means
- Any rate limits, quirks, or gotchas

### Known Issues & Technical Debt
Must include:
- Severity-ranked table (Critical → High → Medium → Low)
- Each row: Severity | Description | Impact | Suggested Fix
- Separate sections for active bugs vs. architectural debt vs. missing features

### Test Coverage Analysis
Must include:
- What is well-covered (behavioral tests that validate real outcomes)
- What is partially covered (tested but with gaps)
- What is not covered (missing entirely)
- Priority ranking for coverage gaps (ranked by risk/impact)
- Notes on test infrastructure (real vs. mocked, integration vs. unit)

---

## Writing Style

- Write for a developer who is new to this codebase — assume they know the tech stack but not this service
- Prefer tables over prose for structured data
- Use ASCII diagrams for data flows — never describe flows in prose only
- Be specific: name actual files, actual table names, actual environment variables
- Flag "gotchas" explicitly — things that would surprise a new developer
- Never write placeholder text — every section must have real content discovered from the codebase

---

## Reference Files

**Always read both reference files before drafting or updating any pages.**

- `references/doc-structure.md` — Full markdown templates for each page type, section by section. Use as a checklist when drafting pages — every placeholder must be filled with real content.
- `references/confluence-patterns.md` — Atlassian MCP tool usage: createConfluencePage, updateConfluencePage, parentId structure, content format, version messages
