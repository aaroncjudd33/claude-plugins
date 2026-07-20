---
name: cab-review
description: Phase 4 — Submit the CAB card for review (Send For Review transition) and assign Sudhakar as the approving manager. Run when the CAB card content is complete and the release is ready for approval.
---

# Release: Send For Review (Phase 4)

Submits the CAB card for review via the Send For Review Jira transition and assigns Sudhakar Seerapu as the post-review assignee.

**Print progress as you go — one line per major step (acp-ajudd#146).** Print one line immediately after each step completes, before starting the next:
```
✓ Session state loaded, readiness confirmed
✓ Sent for review
✓ Post-review manager assigned
✓ CAB chat notified               ← or "skipped"
✓ Story chats notified            ← or "skipped"
✓ Calendar invite sent            ← or "skipped"
✓ Session state updated
```

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

### 5. Post Teams notification to CAB chat

Read `~/.claude/memory/sessions/<slug>/CAB-XXXX.md` for the `Teams chat` field. Look up the chat ID in `~/.claude/plugins/known-chats.md`.

If not found in known-chats, the CAB chat was not created in Phase 1 — create it now before proceeding:
- Read `~/.claude/plugins/team.json`, filter `story-chat` role, collect `teamsUserId` fields (do not include the authenticated user's email)
- Create the chat with topic `CAB-XXXX — [CAB summary]`
- Add to `~/.claude/plugins/known-chats.md`
- Update the session file `Teams chat` field with the new chat name

Read `~/.claude/plugins/marketplaces/ajudd-claude-plugins/comms/skills/comms/references/teams-html-guide.md` before drafting.

Draft a message with:
- CAB key + Jira link
- Deploy date/time in both ET and MT (read `customfield_13137` from the CAB card; convert to both timezones)
- BPT2 stories bundled: key + summary for each
- PR link (if present)

**Preview the full message and wait for explicit "yes" before sending.**

Send via yl-msoffice `send_chat_message` → `confirm_action`.

### 6. Post status update to all related story chats

For **each** story key in the session file's `Related stories` field, **run these in parallel for all stories at once**:

1. Read `~/.claude/memory/sessions/<slug>/<BPT2-XXXX>.md` for the story's `Teams chat` field. Look up the chat ID in `~/.claude/plugins/known-chats.md`. If not found or `none`, skip that story.
2. Call `getJiraIssue` on the story to get its current Jira status.

After all reads and Jira calls complete, draft messages for each story that has a valid chat.

Read `~/.claude/plugins/marketplaces/ajudd-claude-plugins/comms/skills/comms/references/teams-html-guide.md` before drafting.

Draft a message for each story chat including:
- CAB card link + status (now In Change Review)
- Story link + current Jira status
- PR link (if present)
- Deploy date/time in both MDT and UTC
- Post-deployment checks from that story's session file `Post-deployment checks` field (list them unchecked)

**Preview all messages together and wait for explicit "yes" before sending any.**

Send each via yl-msoffice `send_chat_message` → `confirm_action`.

### 7. Send calendar invite for deploy window

Read `~/.claude/plugins/team.json`. Filter members with the `cab-invite` role and collect their `email` fields.

Read the deploy date/time from the CAB session file (or `customfield_13137` from the CAB card — ISO 8601 UTC). Convert to local time (MDT/MST as appropriate).

Build a 1-hour calendar event:
- **Subject:** `[CAB-XXXX] [one-liner on what's deploying]`
- **Start:** deploy date/time
- **End:** deploy date/time + 1 hour
- **Attendees:** `cab-invite` role members
- **Body:** CAB Jira link, primary story link, PR link, brief description of what's deploying

**Preview before sending:**
```
Subject:   [CAB-XXXX] ...
Time:      [day, date, time MDT / UTC]
Attendees: [name1, name2, ...]
```

Wait for explicit approval, then call `create_event` → `confirm_action`.

### 8. Update session state

Update `~/.claude/memory/sessions/<slug>/CAB-XXXX.md`:
- `Phase 4 complete`: yes

## Output

Report:
- CAB card transitioned to Change Review
- Assignee set to Sudhakar (or manual action required)
- Teams notification sent (or skipped)
- Story chat status updates sent to all related story chats (or skipped where chat not found)
- Calendar invite sent (or skipped)
- Next: wait for approval (Implementation status), then run `/release:deploy`
