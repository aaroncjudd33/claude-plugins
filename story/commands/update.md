---
name: update
description: Update a Jira story — fields, status transitions, and assignment. Enforces lifecycle rules (description locked once In Progress or beyond).
argument-hint: "[BPT2-XXXX]"
---

# /story:update [BPT2-XXXX]

Update fields, status, or assignment on an existing BPT2 story. Enforces lifecycle-aware field rules — description is protected once the story is in implementation.

## Steps

### 1. Resolve story key

Use the argument if provided. If not, check `~/.claude/memory/sessions/<slug>/_active` and read the corresponding session file to find the current story key. If still unclear, ask.

### 2. Fetch current story state

Call `getJiraIssue` to retrieve current values for:
`summary`, `status`, `description`, `assignee`, `priority`, `labels`, `customfield_10016` (story points), `customfield_10902` (Expenditures), `customfield_13609` (Work Allocation Type)

### 3. Determine what to update

If the user hasn't specified what to change, ask. Accept any combination of:

- **summary** — story title
- **description** — story body (lifecycle-gated, see step 4)
- **assignee** — Aaron Judd, Maikol Porras, Fernando Magana, Angela Valdez, or unassigned
- **priority** — Highest / High / Medium / Low / Lowest
- **labels** — ask whether to add, remove, or replace existing labels
- **story points** — numeric estimate (customfield_10016)
- **status** — transition to a new status (see transitions in skill reference)
- **comment** — optional note to attach alongside any changes

### 4. Apply lifecycle rules

**Determine the story's phase from its current status:**

**Pre-implementation** — Backlog, Ready For Work, Ready for Grooming, Gathering Requirements, Waiting on Business, Architecture Review, Deferred:
- All fields freely editable, no warnings

**In implementation** — In Progress, Ready for Code Review, Ready For Test, QA In-Progress, Ready for UAT, Failed Testing, Blocked:
- **Description changes require explicit confirmation:**
  > "This story is [status] — changing the description alters the original requirements. Proceed? (yes / no)"
- All other fields (summary, assignee, priority, labels, story points) remain freely editable

**Closed** — Done, Cancelled, Released:
- Warn before any edit: "This story is [status]. Are you sure you want to edit it? (yes / no)"
- Require explicit `yes` before proceeding

### 5. Apply field edits

Call `editJiraIssue` for any field changes. Use markdown for description — the edit tool converts to ADF correctly. Do NOT use `editJiraIssue` for status — handle that in step 6.

### 6. Apply status transition (if requested)

Call `transitionJiraIssue` with the appropriate transition ID from the skill reference. Common transitions:

| From | To | Transition ID |
|------|----|---------------|
| Any | In Progress | `421` |
| Any | Ready for Code Review | `191` |
| Any | Ready For Test | `21` |
| Any | Ready for UAT | `591` |
| Any | Done | `331` |
| Any | Blocked | `31` |
| Any | Cancelled | `41` |

### 7. Add comment

If the user provided a comment, post it via `addCommentToJiraIssue`.

If a status transition occurred and no comment was provided, auto-draft one and ask for confirmation before posting:
- → Ready for Code Review: `"Ready for code review."`
- → Ready For Test: `"Ready for QA."`
- → Done: `"Done."`
- → Blocked: `"Blocked — [ask user for reason]"`
- → any other status: `"Status updated to [status]."`

If the user declines, skip the comment.

### 8. Report

```
BPT2-XXXX updated
  Summary:      [old] → [new]   (if changed)
  Status:       [old] → [new]   (if changed)
  Assignee:     [old] → [new]   (if changed)
  Priority:     [old] → [new]   (if changed)
  Story points: [old] → [new]   (if changed)
  Labels:       added [x], removed [y]   (if changed)
  Description:  updated   (if changed)
  Comment:      posted   (if added)
```

If nothing changed, say: "No changes made to BPT2-XXXX."
