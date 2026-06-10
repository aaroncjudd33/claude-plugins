---
name: finish
description: Pass story information to the release inbox. Writes a pre-filled item with PR, risk, rollback, and post-deploy checks so the next CAB session has everything ready to pick up.
argument-hint: "[BPT2-XXXX]"
---

# /story:finish [BPT2-XXXX]

Pass key story details to the release plugin inbox. That's all this does — it writes a single
inbox item with the information the CAB creation flow needs. Nothing is created yet. The next
time the user starts a release session, the item is there to pick up (alone or alongside
other stories in the same CAB).

---

## Steps

### 1. Resolve story key

Use the argument if provided. If not, extract the repo slug from `pwd` (last path component),
read `~/.claude/memory/sessions/<slug>/_active`, and read the session file to find the story
key. If still unclear, ask.

Also read `~/.claude/memory/sessions/<slug>/<story-key>.md` if it exists — extract the
`Post-deployment checks:` list for inclusion in the inbox item.

### 2. Fetch story summary

Call `getJiraIssue` and pull the `summary` field. That's all that's needed from Jira here.

### 3. Detect merged PR

Try:

```bash
gh pr list --state merged --head "$(git branch --show-current)" --json number,title,url --limit 3
```

If one result is found, show it: "Found PR: [title] — correct? (yes / enter a different one)"

If nothing is found or the user declines, ask: "Paste the PR title and URL:"

### 4. Collect the rest

Use AskUserQuestion (single-select) for urgency and risk:

```
question: "Deploy urgency?"
header: "Urgency"
options:
  - Standard — planned release window (Recommended)
  - Emergency — critical fix, skip standard CAB timeline

question: "Risk level?"
header: "Risk"
options:
  - Low — no DB changes, fully backward-compatible (Recommended)
  - Medium — DB migration, config change, or non-trivial logic
  - High — broad impact, external dependencies, or novel patterns
```

Then ask (free text):
- "Rollback approach? (e.g. 'Revert PR #N and redeploy'  — or Enter to skip)"

### 5. Write to release inbox

Read `pluginMarketplaceName` from `~/.claude/plugins/user-config.json`
(default: `ajudd-claude-plugins`).

Target file: `~/.claude/memory/sessions/<pluginMarketplaceName>/_inbox_release.md`

Create the file with header `# Inbox — release plugin` if it does not exist.

Append the inbox entry (blank line before it):

```
## [YYYY-MM-DD] from <slug>/<story-key>
- **Story:** <story-key> — <summary>
- **PR:** <pr-title> (<pr-url>)
- **Urgency:** <urgency>
- **Risk:** <risk>
- **Rollback:** <approach>  ← omit line if user skipped
- **Post-deploy checks:**
  - <check 1>              ← omit entire section if none
  - <check 2>
```

### 6. Report

```
/story:finish — <story-key>
  <summary>

  PR:       <title>
  Urgency:  <urgency>
  Risk:     <risk>
  Rollback: <approach>   ← or "(none)"
  Post-deploy checks: N   ← or "none"

  ✓ Written to release inbox

Start a release session and pick this up when you're ready to create the CAB.
```
