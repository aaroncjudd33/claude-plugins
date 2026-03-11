# Jira Stories Skill — BPT2

Everything needed to create, populate, and manage stories in the BPT2 (Brand Partner Team Two) Jira project.

---

## Atlassian Connection

Always use these without asking — defined in global `CLAUDE.md`:

- Instance: `https://younglivingeo.atlassian.net`
- Cloud ID: `9de6eb2b-2683-44e6-89ff-c622027e09b4`
- Auth: Handled by the `claude.ai` Atlassian MCP

---

## Project / Issue Type

| Field | Value |
|-------|-------|
| Project Key | `BPT2` |
| Project ID | `12844` |
| Issue Type | `Story` |
| Issue Type ID | `10001` |

---

## Required Fields

These fields are required when creating a BPT2 story:

| Field | API Key | Type | Notes |
|-------|---------|------|-------|
| Summary | `summary` | string | Short descriptive title |
| Expenditures | `customfield_10902` | option ID | **Opex: `10948`**, Capex: `10949`. Default: Opex. |
| Work Allocation Type | `customfield_13609` | array of option IDs | Multi-checkbox. See values below. |

### Work Allocation Type Options

| Value | ID |
|-------|-----|
| Technical Debt (Principle) | `15096` |
| Maintenance (Interest) | `15097` |
| New Development (Stories) | `15098` |
| Production Issues (Problems) | `16361` |

---

## Common Optional Fields

| Field | API Key | Type | Notes |
|-------|---------|------|-------|
| Description | `description` | markdown (via edit) | **Must be set via `editJiraIssue`, not at creation.** See MCP quirks below. |
| Assignee | `assignee` | user (accountId) | Aaron Judd: `620147d91fec260068c1097d` |
| Epic Link | `customfield_10001` | string | Epic key, e.g. `BPT2-1234` |
| Sprint | `customfield_10005` | sprint ID | Set via board if needed |
| Labels | `labels` | array of strings | e.g. `["decommission", "virtual-office"]` |

---

## People

| Person | Role | Account ID |
|--------|------|-----------|
| Aaron Judd | Default assignee / reporter | `620147d91fec260068c1097d` |
| Maikol Porras | Dev team member | (look up if needed) |
| Fernando Magana | Dev team member | (look up if needed) |
| Angela Valdez | Dev team member | (look up if needed) |

---

## MCP Tool Quirks — CRITICAL

### Description formatting

**`createJiraIssue`** treats the `description` field as a literal string. Markdown is NOT converted — `\n`, `**bold**`, `- bullets` all render as raw text.

**`editJiraIssue`** DOES convert markdown to ADF correctly.

**Always use a two-step pattern:**
1. Create the issue with `createJiraIssue` — set summary + required custom fields only, skip or omit description
2. Immediately call `editJiraIssue` to set the description with proper markdown formatting

### Comments

**`addCommentToJiraIssue`** handles markdown correctly, including code blocks with syntax highlighting.

---

## Workflow / Status Transitions

Available transitions from Backlog (starting state):

| Transition | ID | Target Status |
|-----------|-----|---------------|
| In Progress | `421` | In Progress |
| Ready For Work | `181` | Ready For Work |
| Ready for Grooming | `431` | Ready for Grooming |
| Gathering Requirements | `581` | Gathering Requirements |
| Blocked | `31` | Blocked |
| Ready For Test | `21` | Ready For Test |
| Ready for Code Review | `191` | Ready for Code Review |
| Ready for UAT | `591` | Ready for UAT |
| Done | `331` | Done (has screen) |
| Cancelled | `41` | Cancelled (has screen) |
| Released | `231` | Released |
| Approved for Release | `261` | Approved for Release |
| Deferred | `571` | Deferred |
| Waiting on Business | `491` | Waiting on Business |
| Architecture Review | `511` | Architecture Review |
| Failed Testing | `211` | Failed Testing |
| QA In-Progress | `601` | QA In-Progress |

---

## Creation Pattern

```
Step 1: createJiraIssue
  - summary: "Story title"
  - additional_fields:
      customfield_10902: { id: "10948" }       # Opex
      customfield_13609: [{ id: "15097" }]     # Maintenance (or appropriate type)

Step 2: editJiraIssue
  - description: "### Heading\n- Bullet 1\n- Bullet 2"
  - assignee: { accountId: "620147d91fec260068c1097d" }

Step 3 (optional): transitionJiraIssue
  - transition: { id: "421" }    # Move to In Progress

Step 4 (optional): addCommentToJiraIssue
  - commentBody: "Additional details with **markdown** and ```code blocks```"
```
