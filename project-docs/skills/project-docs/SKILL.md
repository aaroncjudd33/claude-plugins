# Project Documentation Skill

This skill guides Claude through deep codebase discovery and structured documentation generation, publishing results as a set of Confluence pages. It is used by the `init-docs`, `update-docs`, and `archive-docs` commands.

---

## Atlassian Connection

The global `CLAUDE.md` defines the Atlassian connection. Always use these without asking:

- Instance: `https://younglivingeo.atlassian.net`
- Cloud ID: `9de6eb2b-2683-44e6-89ff-c622027e09b4`
- Auth: Handled by the `claude.ai` Atlassian MCP

---

## Standard Page Set

Every project gets these pages under a parent index page:

| # | Page Title Pattern | Purpose |
|---|-------------------|---------|
| 0 | `<PROJECT>` | Parent/index page with quick links and page directory |
| 1 | `<PROJECT> — Project Overview` | What it does, tech stack, key files, database, design patterns, status |
| 2 | `<PROJECT> — Architecture & Data Flow` | System flows (with ASCII diagrams), data models, infrastructure stacks, known concerns |
| 3 | `<PROJECT> — Local Dev Runbook` | Step-by-step local setup, CLI reference, SQL/DB quick reference, break-glass steps |
| 4 | `<PROJECT> — API Reference` | Every public endpoint: method, path, auth, request body, response codes, quirks |
| 5 | `<PROJECT> — Known Issues & Technical Debt` | Active bugs, architectural debt, missing features — severity-ranked |
| 6 | `<PROJECT> — Test Coverage Analysis` | What is tested, what is not, coverage gaps ranked by risk |
| 7 | `<PROJECT> — Proposed Work: <Feature>` | Planning docs for upcoming features — created on demand, archived when complete |

---

## Discovery Checklist

Before writing any page, read these sources to extract information:

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

- `references/doc-structure.md` — Detailed section-by-section templates for each page type
- `references/confluence-patterns.md` — How to create and structure Confluence pages using the Atlassian MCP
