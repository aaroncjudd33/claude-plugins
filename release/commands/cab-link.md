---
name: cab-link
description: Phase 3 — Populate all CAB card ADF fields, add deployment comments, and register browser links. Story links are established in Phase 1. Requires Phase 2 (branch + PR) to be complete.
---

# Release: Populate + Comment (Phase 3)

Populates the CAB card's ADF fields, adds deployment comments to BPT2 stories, and registers all artifacts in the browser links registry. Story-to-CAB issue links are already established in Phase 1.

## Instructions

### 1. Load session state

Run `pwd` and extract the repo slug (last path component). Read `~/.claude/memory/sessions/<slug>/_active` → read that session file.

Extract: **CAB key**, **Branch**, **PR number**, **PR URL**, **Related BPT2 stories**, **Related BPT2 CAB**.

Re-fetch the CAB card from Jira (`getJiraIssue`) to get: **summary**, **deploy date/time**, and any other context needed for ADF content.

Re-fetch each BPT2 story (`getJiraIssue`) to get **summaries** and **descriptions** for the ADF fields.

If no session state found, prompt for the CAB key.

### 2. Populate all ADF fields

Call `editJiraIssue` to set all ADF fields in one call:

- **Description** (ADF): What is being deployed, why, any phased approach — seeded from BPT2 story descriptions
- **Release Notes** (`customfield_10512`, ADF): Bullet list of BPT2 story summaries, one per story
- **Deployment Plan** (`customfield_13142`, ADF): Project-specific template from SKILL.md
- **Deployment Playbook** (`customfield_13143`, ADF): Same content as Deployment Plan
- **Rollback Plan** (`customfield_13101`, ADF): Project-specific template from SKILL.md
- **Pre-Deployment Tests** (`customfield_13099`, ADF): VO: "Tested in env6" / CDK: "Tested in dev/stage"
- **Post-Deployment Tests** (`customfield_13100`, ADF): "Tested in Prod"
- **Config/Settings Changes** (`customfield_13176`, ADF): As collected in Phase 1, or "None"
- **Component Version(s)** (`customfield_13141`, ADF): Table — Repository / `release/CAB-XXXX` / PR link (omit PR column on first-deploy)
- **PRs Deploying** (`customfield_14670`, ADF): `"<PR title> - Pull Request #<N> - <org>/<repo>"` with link (omit on first-deploy)

### 3. Comment on BPT2 stories and BPT2 CAB

For each BPT2 story (and the BPT2 CAB if present), call `addCommentToJiraIssue`:

```
Deploying in CAB-XXXX — [CAB card summary]
Scheduled: [deploy date/time in local time]
Release branch: release/CAB-XXXX
PR: [PR title] — Pull Request #N ([link])
```

Omit the PR line on first-deploy.

### 4. Register browser links

Read `~/.claude/browser-links.json`.

**Add to `links` section (if not already present):**
- `cab:CAB-XXX` → `https://younglivingeo.atlassian.net/browse/CAB-XXX`, description: CAB card summary
- `pr:repo-name#NNN` → PR URL, description: PR title *(skip on first-deploy)*

**Create `CAB-XXX` workspace** (type: `cab`):
```json
"CAB-XXX": {
  "description": "<CAB card summary>",
  "type": "cab",
  "links": ["cab:CAB-XXX", "pr:repo-name#NNN", "story:BPT2-XXXX", ...]
}
```
- Include `story:BPT2-XXXX` for each BPT2 story and the BPT2 CAB that exist in the `links` section
- Include `git:repo-name` if it exists in the `links` section
- Omit `pr:` entry on first-deploy

**Append to each BPT2 story workspace and the BPT2 CAB workspace** (if those workspaces exist in `browser-links.json`):
- `cab:CAB-XXX`
- `pr:repo-name#NNN` *(skip on first-deploy)*
- `git:repo-name` if it exists in the `links` section

Write back `~/.claude/browser-links.json`. Do not prompt during this step.

### 5. Update session state

Update `~/.claude/memory/sessions/<slug>/CAB-XXXX.md`:
- `Phase 3 complete`: yes

## Output

Report:
- ADF fields populated
- Stories linked and commented
- BPT2 CAB linked and commented (if present)
- Browser links registered
- Next: Phase 4 (send for review) via `/release:cab-review`, or submit manually in Jira
