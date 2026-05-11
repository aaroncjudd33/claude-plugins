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

Before calling the transition, read `~/.claude/plugins/team.json` to resolve the approver account IDs:
- QA Approved By: first member with role `qa-approver` → `jiraAccountId`
- Code Review Approver: first member with role `code-review-approver` → `jiraAccountId`

If team.json is missing or a role has no member, prompt the user to enter the Jira account ID manually.

Call `transitionJiraIssue` with transition ID `201` and the following transition screen fields:

- `customfield_13174` (QA Approved By): `jiraAccountId` of `qa-approver` member (from team.json)
- `customfield_13612` (Code Review Approver): `jiraAccountId` of `code-review-approver` member (from team.json)
- `customfield_14671` (Date of Code Review): today's date (e.g. `2026-03-17`)
- `customfield_14664` (Clone/Stage Status): `16378` (Part of This Deployment) — or the value configured in Phase 1 if different

### 4. Assign post-review manager

Read `~/.claude/plugins/team.json` → first member with role `cab-assignee` → use their `jiraAccountId`.

Call `editJiraIssue` to set the assignee to that account ID.

If the API rejects the edit (the card may be locked once in Change Review), report: "Assignee could not be set via API — assign Sudhakar Seerapu manually in Jira."

### 5. Post Teams notification

Read `~/.claude/memory/sessions/<slug>/CAB-XXXX.md` for the `Teams chat` field. Look up the chat ID in `~/.claude/plugins/known-chats.md`.

If `Teams chat` is `none` or not found in known-chats, skip this step.

Read `~/.claude/plugins/marketplaces/ajudd-claude-plugins/comms/skills/comms/references/teams-html-guide.md` before drafting.

Draft a message with:
- CAB key + Jira link
- Deploy date/time in both ET and MT (read `customfield_13137` from the CAB card; convert to both timezones)
- BPT2 stories bundled: key + summary for each
- PR link (if present)
- Signature: `<p><em>Posted by Claude Code on behalf of {USER_NAME}</em></p>`

**Preview the full message and wait for explicit "yes" before sending.**

Send via yl-msoffice `send_chat_message` → `confirm_action`.

### 6. Update session state

Update `~/.claude/memory/sessions/<slug>/CAB-XXXX.md`:
- `Phase 4 complete`: yes

## Output

Report:
- CAB card transitioned to Change Review
- Assignee set to Sudhakar (or manual action required)
- Teams notification sent (or skipped)
- Next: wait for approval (Implementation status), then run `/release:deploy`
