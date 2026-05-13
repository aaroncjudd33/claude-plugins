---
name: cab-branch
description: Phase 2 — Create the release branch and GitHub PR. Run after all feature PRs are merged to develop (CDK) or feature branches are ready (VO). Reads CAB key and story context from the session file.
---

# Release: Branch + PR (Phase 2)

Creates the release branch and GitHub PR. This phase requires code to be ready — feature PRs merged (CDK) or feature branches built (VO).

## Instructions

### 1. Load session state

Run `pwd` and extract the repo slug (last path component). Read `~/.claude/memory/sessions/<slug>/_active` to get the active session name.

If the active session starts with `CAB-`, read `~/.claude/memory/sessions/<slug>/<name>.md` to load: **CAB key**, **Related BPT2 stories**, **Related BPT2 CAB**, **Deploy date/time** (re-read CAB card from Jira if needed).

If no active CAB session is found, prompt: "Which CAB? (e.g. CAB-456)"

### 2. Confirm readiness

**CDK:** "Are all feature PRs merged into `develop` and tests passing? [Y/N]"
- If No: stop. "Merge outstanding feature PRs into `develop` first, then re-run."

**VO:** "Are all feature branches ready to merge into the release branch? [Y/N]"
- If No: stop. "Prepare feature branches first, then re-run."

### 3. Create the release branch

Branch name: `release/CAB-XXXX` (using the key from Phase 1).

**Virtual Office:**
```bash
git checkout -b release/CAB-XXXX
```
Guide the user to merge each BPT2 story's feature branch:
```bash
git merge feature/BPT2-XXXX
git merge feature/BPT2-YYYY
```
Resolve merge conflicts before continuing.

Confirm: "Has this release branch been deployed to env6 and tested? [Y/N]"
- If No: stop. "Deploy `release/CAB-XXXX` to env6, complete QA testing, then return."

**CDK:**
```bash
git checkout -b release/CAB-XXXX develop
```

Push:
```bash
git push -u origin release/CAB-XXXX
```

### 4. Create the PR

Check if master exists first (CDK first-deploy detection):
```bash
git ls-remote --exit-code origin master
```

**Standard deploy:**
```bash
gh pr create --base master --head release/CAB-XXXX
```
- **Title:** deploy title matching the CAB card summary
- **Body:** include the CAB key (`CAB-XXXX`) for GitHub-Jira auto-link, list of BPT2 story keys, brief description of what's deploying

**CDK first deploy** (master does not exist on remote):
- Skip PR creation. Note in CAB card (via `editJiraIssue` on Component Version(s)): "First deploy — direct push to master (no PR)."
- Store PR number as `none`.

Store the PR number and URL.

Open the PR in the browser (skip on first-deploy). Read `~/.claude/browser-links.json` and look up `prefixDefaults["pr"]` to resolve the window name (default: `"GitHub"` if not found):
```bash
powershell -ExecutionPolicy Bypass -File "~\.claude\scripts\Open-EdgeUrl.ps1" -Url "<PR-URL>" -WindowName "<resolved-window-name>"
```

### 5. Request PR approval (Virtual Office only)

After the PR is created, send a message to the CAB Teams chat requesting approval. Look up the chat ID from `~/.claude/plugins/known-chats.md` using the CAB key.

Message format:
```
<h2 style="color:#464775;">CAB-XXXX — PR Approval Needed</h2>
Release branch is ready. Please approve PR #NNN before [deploy date/time]:

PR: [title + link]
Story: BPT2-XXXX — [summary]
Deploy: [date and time MDT]
Branch: release/CAB-XXXX → master

Posted by Claude Code on behalf of Aaron Judd
```

Skip this step for CDK/non-VO repos — they do not require a separate PR approval request.

### 6. Update session state

Update `~/.claude/memory/sessions/<slug>/CAB-XXXX.md`:
- `Branch`: `release/CAB-XXXX`
- `PR number`: NNN (or `none` on first-deploy)
- `PR URL`: URL (or `none` on first-deploy)
- `Phase 2 complete`: yes

## Output

Report:
- Release branch created and pushed
- PR created (or first-deploy note)
- Next: Phase 3 (populate ADF fields, link stories, register links)
