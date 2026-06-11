---
name: cab-prep
description: Write or update a [cab-prep] inbox item for the current story in the release plugin inbox. Run any time — before or after /story:finish. Overwrites if an entry already exists for this story key.
argument-hint: "[BPT2-XXXX]"
---

# /story:cab-prep [BPT2-XXXX]

Writes a `[cab-prep]` item to the release plugin inbox with everything needed to create the
CAB. Can be run any time — before the story is fully closed, after, or to refresh data if
something changes. If an entry already exists for this story key it is overwritten in place.

---

## Steps

### 1. Resolve story key

Use the argument if provided. If not, extract the repo slug from `pwd` (last path component),
read `~/.claude/memory/sessions/<slug>/_active`, and read the session file to find the story
key. If still unclear, ask.

Also read `~/.claude/memory/sessions/<slug>/<story-key>.md` if it exists — extract the
`Post-deployment checks:` list for inclusion in the inbox item.

### 2. Fetch story summary

Call `getJiraIssue` and pull the `summary` field.

> **Run steps 2 and 3 in parallel** � both can start immediately once the story key is resolved.

### 3. Detect merged PR

Try:

```bash
gh pr list --state merged --head "$(git branch --show-current)" --json number,title,url --limit 3
```

If one result is found, show it: "Found PR: [title] — correct? (yes / enter a different one)"

If nothing is found or the user declines, ask: "Paste the PR title and URL:"

### 4. Collect handoff details

Ask for urgency, risk, and rollback in one block — output and wait:

```
  Urgency:   standard (planned release window) / emergency (critical fix, skip CAB timeline)
  Risk:      low (no DB, backward-compatible) / medium (DB migration, config, non-trivial logic) / high (broad impact)
  Rollback:  <approach, e.g. "Revert PR #N and redeploy"> or skip

go = standard / low / skip
```

Parse defaults from "go" or accept any combination: `emergency high "Revert PR #452"`, `standard medium`, etc.

### 5. Write or update release inbox

Read `pluginMarketplaceName` from `~/.claude/plugins/user-config.json`
(default: `ajudd-claude-plugins`).

Target file: `~/.claude/memory/sessions/<pluginMarketplaceName>/_inbox_release.md`

Create the file with header `# Inbox — release plugin` if it does not exist.

**Check for an existing entry:** scan for a line matching `## [...] from .* / <story-key> [cab-prep]`.

- **Found:** replace that entry (from its `## ` header line through the blank line before the
  next `## ` header or end of file) with the new entry.
- **Not found:** append the new entry (blank line before it).

Entry format:
```
## [YYYY-MM-DD] from <slug>/<story-key> [cab-prep]
- **Story:** <story-key> — <summary>
- **PR:** <pr-title> (<pr-url>)
- **Urgency:** <urgency>
- **Risk:** <risk>
- **Rollback:** <approach>        ← omit line if user skipped
- **Post-deploy checks:**
  - <check 1>                     ← omit entire section if none
  - <check 2>
```

### 6. Report

```
/story:cab-prep — <story-key>
  <summary>

  PR:       <title>
  Urgency:  <urgency>
  Risk:     <risk>
  Rollback: <approach>   ← or "(none)"
  Checks:   N            ← or "none"

  ✓ Written to release inbox  ← or: ✓ Updated existing entry
```
