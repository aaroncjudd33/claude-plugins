---
name: cab-review
description: Phase 4 — Submit the CAB card for review (Send For Review transition) and assign Sudhakar as the approving manager. Run when the CAB card content is complete and the release is ready for approval.
---

# Release: Send For Review (Phase 4)

Submits the CAB card for review via the Send For Review Jira transition and assigns Sudhakar Seerapu as the post-review assignee.

## Instructions

### 1. Load session state

Run `pwd` and extract the repo slug (last path component). Read `~/.claude/memory/sessions/<slug>/_active` → read that session file for: **CAB key**, **Branch**, **PR number**, **Related BPT2 stories**.

If no session state, prompt: "Which CAB? (e.g. CAB-456)" and `getJiraIssue` to fetch the summary.

### 2. Confirm readiness

Display a summary and ask for explicit confirmation before proceeding:

```
Ready to send CAB-XXXX for review?

  Summary: [CAB card summary]
  Branch:  release/CAB-XXXX
  PR:      #NNN [link]
  Stories: BPT2-XXXX, BPT2-YYYY

Proceed? (Yes / No)
```

Do not proceed without explicit "Yes."

### 3. Send For Review

Call `transitionJiraIssue` with transition ID `201` and the following transition screen fields:

- `customfield_13174` (QA Approved By): `557058:055d4592-8fbf-4b3c-8115-0dc48da8a1b4` (Heber Iraheta)
- `customfield_13612` (Code Review Approver): `557058:055d4592-8fbf-4b3c-8115-0dc48da8a1b4` (Heber Iraheta)
- `customfield_14671` (Date of Code Review): today's date (e.g. `2026-03-17`)
- `customfield_14664` (Clone/Stage Status): `16378` (Part of This Deployment) — or the value configured in Phase 1 if different

### 4. Assign Sudhakar

Call `editJiraIssue` to set the assignee to Sudhakar Seerapu: `60aeba90f3fab100683274d9`.

If the API rejects the edit (the card may be locked once in Change Review), report: "Assignee could not be set via API — assign Sudhakar Seerapu manually in Jira."

### 5. Update session state

Update `~/.claude/memory/sessions/<slug>/CAB-XXXX.md`:
- `Phase 4 complete`: yes

## Output

Report:
- CAB card transitioned to Change Review
- Assignee set to Sudhakar (or manual action required)
- Next: wait for approval (Implementation status), then run `/release:deploy`
