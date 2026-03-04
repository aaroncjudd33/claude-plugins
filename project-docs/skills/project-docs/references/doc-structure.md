# Page Structure Templates

Detailed section-by-section structure for each page type. Use these as a checklist — every section must be populated with real content discovered from the codebase.

---

## Page 0: Parent Index

```markdown
# <Project Name>

<2-3 sentence plain-language description of what the service does.>

## Pages in this section

- **[Project Overview]** — Purpose, tech stack, key files, environment config, and current status
- **[Architecture & Data Flow]** — <brief description specific to this project>
- **[Local Dev Runbook]** — Step-by-step local setup and test run guide
- **[API Reference]** — All public endpoints (if applicable)
- **[Known Issues & Technical Debt]** — Active bugs and architectural debt
- **[Test Coverage Analysis]** — Coverage gaps ranked by risk

## Quick Links

- GitHub: <url>
- Branch strategy: <describe>
- Jira: <link to epic or board if known>
```

---

## Page 1: Project Overview

```markdown
# <Project Name> — Project Overview

## What It Does

<2-4 sentences. Plain language. What business problem does this solve? Who uses it?>

**Key capabilities:**
- <capability 1>
- <capability 2>
- <capability 3>

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Runtime | <e.g. Node.js 18.x (ARM_64)> |
| Language | <e.g. TypeScript> |
| IaC | <e.g. AWS CDK v2> |
| Package manager | <e.g. pnpm> |
| Testing | <e.g. Vitest 2.x> |
| <...> | <...> |

---

## Repository & Key Files

- **GitHub:** <url>
- **Branch strategy:** <describe>

| File | Purpose |
| --- | --- |
| <path/to/file.ts> | <one-line purpose> |
| <...> | <...> |

---

## Database

### <Database Name (e.g. Oracle)>

<Brief description of what data lives here and how it's used.>

| Env | Connection |
| --- | --- |
| Dev | <host:port/db> |
| Stage | <host:port/db> |
| Prod | <host:port/db> |

Key columns/fields: <describe any non-obvious fields, types, or constraints>

### <Database Name (e.g. DynamoDB)>

Table name: `<TableName[Env]-Suffix>`

| Partition Key | Sort Key | Description |
| --- | --- | --- |
| `<pk pattern>` | `<sk pattern>` | <what this record represents> |

---

## Design Patterns

- **<Pattern name>** — <brief explanation of how it's used in this codebase>
- **<Pattern name>** — <brief explanation>

---

## Status

- <Active/Deprecated/In Development>
- <Recent notable changes>
- <Known limitations that affect day-to-day development>
```

---

## Page 2: Architecture & Data Flow

```markdown
# <Project Name> — Architecture & Data Flow

## System Overview

<2-3 sentences describing the high-level system shape — how many flows, what systems are connected, what the service's role is.>

---

## <Flow Name> Flow (<Source> → <Destination>)

<One sentence describing when this flow triggers.>

\`\`\`
<Source System>
  │
  ▼
<Queue or Gateway>
  Batch size: N  |  <other config>
  │
  ▼
<Lambda or Handler>
  1. <step>
  2. <step>
  3. <step>
\`\`\`

### <Key Logic Name (e.g. Echo Prevention, Idempotency)>

<Explain the logic. Name the specific function/class that implements it.>

---

## Data Model

Table: `<TableName>`

### <EntityName>

<One sentence describing what this record represents.>

\`\`\`
{
  pk:    "<pattern>",
  sk:    "<pattern>",
  detail: {
    <field>: <type>,
    <field>: <type>
  }
}
\`\`\`

---

## Infrastructure Stacks

| Stack | Contents | Deletion Policy |
| --- | --- | --- |
| `<StackName>` | <what it provisions> | <Retained / Standard> |

---

## Known Architecture Concerns

| Severity | Issue |
| --- | --- |
| Critical | <description> |
| High | <description> |
| Medium | <description> |
```

---

## Page 3: Local Dev Runbook

```markdown
# <Project Name> — Local Dev Runbook

<One sentence: what does running through these steps accomplish?>

---

## Step 1 — <Prerequisites / Auth>

\`\`\`shell
<exact command>
\`\`\`

<Expected output or success indicator if the step is slow or non-obvious.>

---

## Step 2 — <Runtime Version>

\`\`\`shell
<exact command>
\`\`\`

---

## Step 3 — <Local Services>

<Service name> must be running before <next step>.

\`\`\`shell
<start command>
\`\`\`

Wait for: `<log message or indicator>`

Local connection details:

| Field | Value |
| --- | --- |
| Host | <value> |
| User | <value> |
| Password | <value> |

---

## Step 4 — Install & Build

\`\`\`shell
<commands>
\`\`\`

---

## Step 5 — Deploy (if required for tests)

<Explain what this deploys and why tests need it.>

\`\`\`shell
<command>
\`\`\`

---

## Step 6 — Run Tests

\`\`\`shell
<command>   # single run — use this
<command>   # watch mode — use during active development
\`\`\`

Expected: **<N> test files, <N> tests, ~<N> seconds**

> **Warning:** <any important caveats about test commands>

---

## <Service> Quick Reference (SQL / CLI / etc.)

\`\`\`shell
<connect command>
\`\`\`

\`\`\`sql
-- <description>
<query>;

-- <description>
<query>;
\`\`\`

---

## Break-Glass: Clean Reinstall

\`\`\`shell
<commands to fully reset and reinstall>
\`\`\`

---

## Notes

- <Gotcha 1>
- <Gotcha 2>
```

---

## Page 4: API Reference

```markdown
# <Project Name> — API Reference

## Authentication

<Describe auth mechanism. How does a caller authenticate? What validates the token?>

---

## POST /path/to/endpoint

<One sentence: what does this endpoint do?>

**Auth:** <Bearer token / API key / IP whitelist / none>

### Request Body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `<field>` | `<type>` | Yes/No | <description> |

### Response Codes

| Code | Meaning |
| --- | --- |
| 200 | <description> |
| 400 | <description> |
| 401 | <description> |
| 500 | <description> |

### Notes

- <Any quirks, edge cases, or gotchas>
```

---

## Page 5: Known Issues & Technical Debt

```markdown
# <Project Name> — Known Issues & Technical Debt

## Active Bugs

| Severity | Issue | Impact | Suggested Fix |
| --- | --- | --- | --- |
| Critical | <description> | <impact> | <fix> |

## Architectural Debt

| Severity | Issue | Impact | Suggested Fix |
| --- | --- | --- | --- |
| High | <description> | <impact> | <fix> |

## Missing Features / Gaps

| Priority | Gap | Notes |
| --- | --- | --- |
| High | <description> | <notes> |
```

---

## Page 6: Test Coverage Analysis

```markdown
# <Project Name> — Test Coverage Analysis

## Test Infrastructure

- **Framework:** <Vitest / Jest / xUnit / pytest>
- **Test database:** <real / mocked / in-memory> — <brief description>
- **External APIs:** <mocked / real>
- **Test data:** <how seed data is set up>
- **Run command:** `<command>` (~<N> seconds, <N> tests)

---

## Well Covered

| Area | What's Tested |
| --- | --- |
| <area> | <what behavioral outcomes are verified> |

---

## Partially Covered

| Area | What's Tested | What's Missing |
| --- | --- | --- |
| <area> | <what exists> | <what's missing> |

---

## Not Covered

| Area | Risk | Priority |
| --- | --- | --- |
| <area> | <why this matters> | High/Medium/Low |

---

## Priority Gaps

1. **<Gap>** — <why this is the highest priority to address>
2. **<Gap>** — <rationale>
3. **<Gap>** — <rationale>
```
