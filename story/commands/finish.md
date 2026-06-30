---
name: finish
description: Close out a story session — transition Jira status, clear open items, and optionally send a [cab-prep] handoff to the release inbox.
argument-hint: "[BPT2-XXXX]"
---

# /story:finish [BPT2-XXXX]

Close out a completed story. Transitions Jira, cleans up the session file, and optionally
creates or updates a `[cab-prep]` item in the release inbox if the story is heading to prod.

---

## Steps

### 1. Resolve story key

Use the argument if provided. If not, extract the repo slug from `pwd` (last path component),
read `~/.claude/memory/sessions/<slug>/_active`, and read the session file to find the story
key. If still unclear, ask.

### 2. Fetch current Jira state

Call `getJiraIssue` to get: `summary`, `status`.

### 3. Transition Jira (optional)

Ask:
> "Transition story status? (current: [status])"

Output and wait:
```
  done  ·  approved-for-release  ·  skip
```

Apply the transition if selected (see transition IDs in the story skill reference).

### 4. Update session file

Resolve `session_root` for this repo: check `<git-repo-root>/.claude/sessions/`; if it exists use it, otherwise use `~/.claude/memory/sessions/<slug>/`.

If a session file exists at `<session_root>/<story-key>.md`, update:
- `Status` → `complete`
- `Open items` → `none`
- `Next step` → `none`

### 5. CAB handoff (optional)

Resolve `session_root` for this repo: check `<git-repo-root>/.claude/sessions/`; if it exists
use it, otherwise use `~/.claude/memory/sessions/<slug>/`.

Check `<session_root>/_inbox.md` for an existing entry matching
`## [...] from .* / <story-key> [cab-prep]`.

- **Entry exists:** "A cab-prep item already exists for <story-key> — update it? (yes / skip)"
- **No entry:** "Send to project inbox for CAB handoff? (yes / skip)"

If the user says yes (either case), run the `/story:cab-prep` steps (steps 1–5 of that
command) using the story key already resolved. Skip steps 1–2 of cab-prep since the story
key and summary are already in hand.

### 6. Commit session files (repo-based sessions only)

Skip this step entirely if `session_root` is `~/.claude/memory/sessions/<slug>/` (local-only session — nothing to commit).

Only run when `session_root` is `<git-repo-root>/.claude/sessions/`. Determine the case from git state:

```bash
git rev-parse --show-toplevel   # confirm we're in a repo
git branch --show-current       # current branch
git ls-remote --heads origin "feature/*<story-key>*"  # does feature branch exist on remote?
```

**Case A — currently on the feature branch:**
Commit and push. Stay on the feature branch.
```bash
git add .claude/sessions/<story-key>.md .claude/sessions/_history.md .claude/sessions/_inbox.md
git commit -m "<story-key>: Close session — update state and cab-prep handoff"
git push
```

**Case B — not on feature branch, but it still exists on remote:**
Switch to it, commit, push, open a new PR to develop. Stay on the feature branch.
```bash
git checkout feature/<branch-name>
git add .claude/sessions/<story-key>.md .claude/sessions/_history.md .claude/sessions/_inbox.md
git commit -m "<story-key>: Close session — update state and cab-prep handoff"
git push
gh pr create --base develop --title "<story-key>: Close session files" --body "Session state and cab-prep handoff after story close."
```

**Case C — feature branch deleted (not found on remote):**
Create a cleanup branch from develop, commit, push, PR. Stay on the cleanup branch.
```bash
git checkout develop && git pull
git checkout -b feature/<story-key>-session-close
git add .claude/sessions/<story-key>.md .claude/sessions/_history.md .claude/sessions/_inbox.md
git commit -m "<story-key>: Close session — update state and cab-prep handoff"
git push -u origin feature/<story-key>-session-close
gh pr create --base develop --title "<story-key>: Close session files" --body "Session state and cab-prep handoff after story close."
```

**Branching rules (non-negotiable):**
- Never commit directly to `develop` or `master` — always via PR
- Stay on the feature/cleanup branch when done — do not switch back to develop
- No two open PRs to the same target branch at once

### 7. Report

```
/story:finish — <story-key>
  <summary>

  Jira:        [status] → [new status]   ← or "unchanged"
  Session:     closed
  CAB handoff: ✓ written / ✓ updated / skipped
  Committed:   Case A — pushed to feature/<branch>  ← or Case B/C detail, or "local session — skipped"
```
