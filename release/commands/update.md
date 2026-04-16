---
name: update
description: Update an existing CAB card — add or remove linked stories, update PR/branch info, or edit other fields. Keeps Jira issue links and session cross-references in sync.
argument-hint: "[cab-key]"
---

# CAB: Update Card

Update an existing CAB card and keep session cross-references in sync with any story changes.

## Instructions

### 1. Identify the CAB

Run `pwd` and extract the repo slug (last path component).

If a CAB key is provided as an argument, use it. Otherwise read `~/.claude/memory/sessions/<slug>/_active` to get the active session name, then read that session file for the CAB key.

If neither is available, prompt: "Which CAB card? (e.g. CAB-456)"

### 2. Confirm current state

Call `getJiraIssue` for the CAB. Display:
- Status
- Linked stories (from `issuelinks` field)
- `Related stories` from session memory (if session file exists)

### 3. Present update options

```
=== Update CAB-XXX ===

[1] Add a story
[2] Remove a story
[3] Update PR / branch info
[4] Update other fields
```

Accept multiple selections (e.g. "1, 3"). Run each selected update in sequence.

---

### 4a. Add a story

1. Prompt for the story key (e.g. `BPT2-XXXX`)
2. Call `createIssueLink` with `type="Deploy Location"` (outward: CAB deploys the story)
3. Append the story key to `Related stories` in the CAB session file
4. Check if `~/.claude/memory/sessions/<slug>/BPT2-XXXX.md` exists — if so, set its `Related CAB` field to `CAB-XXX`

---

### 4b. Remove a story

1. Prompt for the story key to remove
2. Call `getJiraIssue` for the CAB and find the issue link ID for that story in `fields.issuelinks`
3. Note to the user that deleting issue links must be done manually in the Jira UI — no MCP tool is available for this action
4. Remove the story key from `Related stories` in the CAB session file
5. If `~/.claude/memory/sessions/<slug>/BPT2-XXXX.md` exists, set its `Related CAB` field to `none`

---

### 4c. Update PR / branch info

1. Show current values of `Component Version(s)` (`customfield_13141`) and `PRs Deploying` (`customfield_14670`)
2. Prompt for the new repository, branch, and PR link
3. Call `editJiraIssue` to update both fields with ADF-formatted content

---

### 4d. Update other fields

Present a numbered list of editable fields with their current values:

```
[1] Summary
[2] Description
[3] Release Notes
[4] Deployment Plan / Playbook
[5] Rollback Plan
[6] Pre/Post-Deployment Tests
[7] Config/Settings Changes
[8] Requested Deploy Date/Time
[9] CAB Risk / Impact / Request Type
```

Prompt for which to change, accept new values, and call `editJiraIssue`.

---

## Output

Report:
- What changed in Jira (fields updated, links added/removed)
- What changed in session memory (which session files were updated)
- Any actions that required manual intervention in the Jira UI
