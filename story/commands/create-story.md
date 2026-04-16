---
name: create-story
description: Create a Jira story in BPT2 with proper formatting, assignment, and optional status transition.
argument-hint: "[summary] [work-type] [assignee]"
---

# Create BPT2 Story

Create a fully-populated Jira story in the BPT2 project with properly formatted description, correct required fields, and optional assignment/transition.

## Instructions

When this command is invoked:

### 1. Collect inputs

If not provided as arguments or inferable from conversation context, ask the user for:
- **Summary** — short descriptive title for the story
- **Description** — what the story is about (can come from conversation context)
- **Work Allocation Type** — one of: Technical Debt, Maintenance, New Development, Production Issues (default: infer from context)
- **Expenditures** — Opex or Capex (default: Opex)
- **Assignee** — who to assign (default: Aaron Judd)
- **Initial status** — Backlog, In Progress, Ready For Work, etc. (default: Backlog)
- **Comment** — optional first comment to add (e.g. technical details, queries, etc.)

Infer as much as possible from conversation context. Minimize questions — if the user has been discussing a topic, use that as the description basis.

### 2. Create the issue (summary + required fields only)

Call `createJiraIssue` with:
- `cloudId`: `9de6eb2b-2683-44e6-89ff-c622027e09b4`
- `projectKey`: `BPT2`
- `issueTypeName`: `Story`
- `summary`: the story title
- `additional_fields`:
  - `customfield_10902`: Expenditures option (default Opex: `{"id": "10948"}`)
  - `customfield_13609`: Work Allocation Type array (e.g. `[{"id": "15097"}]` for Maintenance)

**Do NOT set the description here** — it will render as raw text. Leave it out entirely.

### 3. Set description + assignee via edit

Immediately call `editJiraIssue` to set:
- **description** — using proper markdown (headings, bullets, bold, code blocks). The edit tool converts markdown to ADF correctly.
- **assignee** — if specified (default: Aaron Judd `620147d91fec260068c1097d`)

### 4. Transition status (if not Backlog)

If the user wants a status other than Backlog, call `transitionJiraIssue` with the appropriate transition ID from the skill reference.

### 5. Add comment (if provided)

If there's additional content to add as a comment (technical details, queries, proposed solutions), call `addCommentToJiraIssue`. Markdown and code blocks work correctly in comments.

### 6. Link related issues (if any)

If the user mentions related Jira issues, link them using the `createIssueLink` MCP tool with `type="Relates"`.

### 7. Write session file

Run `pwd` and extract the last path component as `<slug>`.

Construct the feature branch name: `feature/BPT2-XXXX-<short-slug>` where `<short-slug>` is the story summary lowercased, spaces replaced with hyphens, special characters removed, truncated to ~40 chars.

Write `~/.claude/memory/sessions/<slug>/BPT2-XXXX.md`:

```
---
updated: <today's date>
---

# Session State — BPT2-XXXX

- **Type:** story
- **Name:** BPT2-XXXX
- **Teams chat:** none
- **Project:** <pwd>
- **Branch:** feature/BPT2-XXXX-<short-slug>
- **Last worked on:** Created — <summary>
- **Open items:** none
- **Next step:** Create feature branch: feature/BPT2-XXXX-<short-slug>
- **Related CAB:** none
```

Create `~/.claude/memory/sessions/<slug>/` if it does not exist.

## Output

Report:
- Story URL and key (e.g. `BPT2-6190`)
- Status (Backlog, In Progress, etc.)
- Assignee
- Feature branch name: `feature/BPT2-XXXX-<short-slug>`
- Whether description and comments rendered correctly
- Any fields that could not be populated and why
