---
name: setup
description: "Background skill — do not run directly. Use /setup:local to start your day. Auto-loads when: 'start my day', 'morning setup', 'log into AWS', 'check my tickets', or any /setup: command."
---

# Setup Skill

Reference data and formatting rules for the morning setup routine.

---

## Atlassian Connection

- Instance: `https://younglivingeo.atlassian.net`
- Cloud ID: `9de6eb2b-2683-44e6-89ff-c622027e09b4`
- Auth: Handled by the `claude.ai` Atlassian MCP
- User Account ID: read from `~/.claude/plugins/user-config.json` > `user.jiraAccountId` — used as `{ACCOUNT_ID}` in all queries

---

## Jira

<!-- SYNC NOTE: These 3 JQL queries are duplicated in setup/commands/jira.md, setup/commands/local.md, story/commands/my-stories.md, and this file.
     CANONICAL SOURCE: story/skills/story/SKILL.md — update there first, then sync all four. -->

### Query 1 — Currently assigned to me

```jql
project = BPT2 AND assignee = "{ACCOUNT_ID}" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, duedate ASC
```

### Query 2 — Previously assigned to me (reassigned to someone else)

```jql
project = BPT2 AND assignee WAS "{ACCOUNT_ID}" AND assignee != "{ACCOUNT_ID}" AND assignee is not EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

### Query 3 — Previously assigned to me (now unassigned)

```jql
project = BPT2 AND assignee WAS "{ACCOUNT_ID}" AND assignee is EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

### Status Grouping Order

Display in this order (skip groups with zero tickets):
1. In Progress
2. Ready For Test / In Review / In QA
3. Open / To Do / Backlog
4. Any other statuses

### Flagging Rules

- `DUE TODAY` — duedate equals today
- `OVERDUE (YYYY-MM-DD)` — duedate is before today (always show the date)
- No flag if duedate is null or in the future

---

## Confluence

### Recently Modified Pages Queries

```cql
watcher = "{ACCOUNT_ID}" AND lastmodified > now("-7d") ORDER BY lastmodified DESC
```

```cql
mention = "{ACCOUNT_ID}" AND lastmodified > now("-7d") ORDER BY lastmodified DESC
```

Deduplicate results by page ID. Show max 10 pages. Use relative dates: "today", "yesterday", "2 days ago", or the date if older.

---

## AWS

### SSO Check and Login

```bash
aws sts get-caller-identity 2>/dev/null
```

Run this first. If it fails, run `aws sso login` (opens browser, blocks until complete). Parse `~/.aws/sso/cache/*.json` for expiry — warn if < 2 hours remaining.

### CodeArtifact Logins

Run both in parallel after SSO is confirmed:

```bash
aws --profile devops codeartifact login --tool dotnet --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```

```bash
aws --profile devops codeartifact login --tool npm --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```

---

## Output Format

Plain text, no markdown rendering:
- Date header at top with `===` underline
- ALL CAPS section labels with a blank line before each
- Bullet points with dashes
- Indented details under each item
- Concise — entire briefing readable in under 60 seconds

---

## Error Handling

If any section fails (MCP auth issue, network error, etc.), print the error under that section header and continue. Never let one failure block the full briefing.

---

## `ccs` Repo Launcher

A shell shortcut shipped with this plugin and installed by `/setup:onboarding` (Step 6a).
`ccs <acronym>` cds into a repo and launches Claude Code; `ccs` alone launches in the
current directory; an unknown argument falls back to a starts-with scan of the work-repos
base dir.

- **Source templates:** `${CLAUDE_PLUGIN_ROOT}/scripts/ccs.sh` (bash) and `ccs.ps1` (PowerShell), behavior-identical.
- **Config-driven, baked at install:** onboarding substitutes two tokens — `__CCS_REPOS_BASE__`
  (from `paths.workReposDir`; MSYS→Windows-translated for the `.ps1`) and `__CCS_MARKETPLACE__`
  (from `paths.pluginMarketplaceName`). Nothing is hardcoded to `C:\dev`.
- **Idempotent install:** the function is written between the marker sentinels
  `# >>> ccs launcher …` / `# <<< ccs launcher <<<`. Re-running onboarding replaces the block
  in place (never double-appends). To update the shipped map/logic on a machine, edit the
  template here, then re-run `/setup:onboarding` and choose to install.
- **Default acronym map** covers the common YL repos; the starts-with fallback covers the rest,
  so it need not be exhaustive. `plugins` is special-cased to the marketplace clone.

---

## Claude Output Conventions

A shared block of output-formatting conventions, installed into a dev's global
`~/.claude/CLAUDE.md` by `/setup:onboarding` (Step 6b) and re-synced by `/setup:update`.
Absorbs the verdict-placement (acp-ajudd#111) and read-priority-tier (acp-ajudd#112)
preferences that previously existed only in Aaron's personal CLAUDE.md — this makes them
portable, so every teammate gets the same conventions with zero manual editing
(acp-ajudd#116).

- **Source template:** `${CLAUDE_PLUGIN_ROOT}/scripts/output-conventions.md` — content:
  read-priority tiers (`✓` skippable / no-marker standard / `⚠ read before proceeding:`
  hard gate), verdict-at-bottom, no-all-caps, and the verbosity dial definition.
- **Config-driven, baked at install:** onboarding substitutes one token —
  `__VERBOSITY_DEFAULT__` — from `defaults.verbosityDefault` in `user-config.json`
  (default `v1` if never set). The dial *definition* is shared; the default *level* is
  per-user, same shared-content-plus-per-user-token split the `ccs` launcher uses above.
- **Copy-body-with-markers, NOT dot-source** — same rationale as `ccs`: the plugin-root
  path is version-stamped and goes stale every `/setup:update`. The block is written
  between `<!-- begin acp-output-conventions -->` / `<!-- end acp-output-conventions -->`
  in `~/.claude/CLAUDE.md`.
- **Idempotent install + explicit re-sync:** re-running onboarding replaces the block in
  place. Unlike `ccs`, `/setup:update` **also** re-syncs this block automatically (but only
  if already installed — it never performs the first install) so content changes reach
  every dev without them remembering to re-run onboarding.
- **Two hard gotchas (same as `ccs`):** (1) substitute the token with **python, not sed**;
  (2) write with explicit `encoding='utf-8'` — never PowerShell `Set-Content` /
  `Get-Content -Raw` on `~/.claude/CLAUDE.md` (cp1252 round-trip risk, #114). This file is
  load-bearing for every plugin, so a corrupting write here is worse than for a shell
  profile.
- `/setup:wipe` Step 4b offers to strip the block on teardown, mirroring `ccs`'s 4a.
- **Reconciles, does not duplicate,** the existing "format signals type" rule some devs
  (Aaron) may already have hand-written in their personal `~/.claude/CLAUDE.md` — the
  block's read-priority-tiers section extends that same rule (✓-skippable / bold-decision)
  into a third explicit tier, rather than introducing a second, parallel scheme.

---

## Calendar

<!-- SYNC NOTE: Mirrors setup/commands/calendar.md. Update both together. -->

Tool: `mcp__claude_ai_yl-msoffice__list_events`

Date range: today 00:00–23:59 local time in UTC. Mountain Time — MDT (UTC-6) April–October, MST (UTC-7) otherwise.

Parameters: `startDateTime`, `endDateTime` (ISO 8601 UTC), `top: 20`.

Post-processing:
- Filter out events where response status is `declined`
- Sort by start time ascending
- Duration = end − start; format as `(30 min)`, `(1h)`, `(1h 30m)`
- Location hint: `— Teams` if `isOnlineMeeting` or Teams join URL present; else location name if non-empty

Output format:
```
CALENDAR (N events)

  9:00 AM   Daily Standup                 (30 min)  — Teams
  10:30 AM  Sprint Planning               (1h)
```

No events → `CALENDAR — No events today`. Failure → `CALENDAR — Unavailable`.
