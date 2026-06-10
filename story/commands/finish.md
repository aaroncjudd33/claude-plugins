---
name: finish
description: Hand off a completed story for production deploy. Captures PR, risk, rollback, and post-deploy validation steps and writes a CAB-ready spawn entry to the release inbox.
argument-hint: "[BPT2-XXXX]"
---

# /story:finish [BPT2-XXXX]

Hand off a completed story to the release workflow. Creates a `[spawn]` entry in the plugin global inbox so the next `/release:create-cab` session has all required fields pre-filled.

The spawn entry is **not** a CAB — it is a pre-loaded handoff. The user still runs `/session:start` in the plugin directory, picks up the spawn, and CAB creation runs with the collected data already present. `/release:create-cab` remains fully usable standalone for multi-story CABs.

---

## Steps

### 1. Resolve story key

Use the argument if provided. If not, extract the repo slug from `pwd` (last path component), read `~/.claude/memory/sessions/<slug>/_active`, then read the active session file to find the current story key. If still unclear, ask.

Also read the story session file at `~/.claude/memory/sessions/<slug>/<story-key>.md` if it exists — extract the `Post-deployment checks:` field (a checkbox list) for use in step 5.

### 2. Fetch Jira state

Call `getJiraIssue` to retrieve: `summary`, `status`.

If the story is not in a deployable state (Done, Approved for Release, Ready For Test, QA In-Progress, Ready for UAT), warn:

> "This story is [status] — are you sure it's ready for production deploy? (yes / cancel)"

Cancel if the user declines.

### 3. Detect PR

Try to find the merged PR for the current branch:

```bash
gh pr list --state merged --head "$(git branch --show-current)" --json number,title,url --limit 3
```

If exactly one result is found, use it — show it to the user for confirmation:
> "Found PR: [title] ([url]) — correct? (yes / enter a different one)"

If no result, or the user declines, ask:
> "Paste the PR title and URL:"

### 4. Collect handoff details

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
- "Rollback approach? (e.g. 'Revert PR #N and redeploy')"
- "Any additional post-deploy validation steps beyond what's in the session file? (Enter to skip)"

### 5. Build spawn entry

Read `pluginMarketplaceName` from `~/.claude/plugins/user-config.json` (default: `ajudd-claude-plugins`).

Compile post-deploy checks: merge the `Post-deployment checks:` list from the story session file (strip checkbox markers — render as plain bullets) with any additional steps the user provided. If neither source has checks, omit the section.

Spawn entry format:
```
## [YYYY-MM-DD] from <slug>/<story-key> [spawn]
[spawn — release, create-cab]
- **Story:** <story-key> — <summary>
- **PR:** <pr-title> (<pr-url>)
- **Urgency:** <urgency>
- **Risk:** <risk>
- **Rollback:** <approach>
- **Post-deploy checks:**
  - <check 1>
  - <check 2>
  (omit entire section if no checks)
```

### 6. Write to global inbox

Read `~/.claude/memory/sessions/<pluginMarketplaceName>/_inbox.md`.

If the file does not exist, create it with:
```
# Inbox — <pluginMarketplaceName>
```

Append the spawn entry (blank line before it). Write back.

### 7. Transition Jira (optional)

Ask:
> "Transition story to 'Approved for Release' in Jira? (yes / skip)"

If yes, call `transitionJiraIssue` with transition ID `261`.

### 8. Update story session file (if applicable)

If the story session file at `~/.claude/memory/sessions/<slug>/<story-key>.md` exists, update:
- `Open items` — remove any items related to this handoff, or set to `none`
- `Next step` — `none — CAB spawn written to release inbox`

### 9. Report

```
/story:finish — <story-key>
  Story:    <summary>
  PR:       <title> (<url>)
  Urgency:  <urgency>
  Risk:     <risk>
  Rollback: <approach>
  Post-deploy checks: N step(s)   ← or "none"

  ✓ Spawn entry written → ~/.claude/memory/sessions/<pluginMarketplaceName>/_inbox.md
  ✓ Jira transitioned to Approved for Release   ← or: "(skipped)"

Next: run /session:start in the plugin directory and pick up the ★ spawn
entry to create the CAB.
```
