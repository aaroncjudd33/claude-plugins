---
name: review
description: Review the working diff with the pr-review-toolkit agents plus a portable YL OWASP/exploit security pass, then print one consolidated Critical/Important/Suggestions/Strengths report headed with the detected story/branch and the suggested reviewers from team.json — and optionally post the summary back to Teams, Jira, and/or GitHub (each opt-in, previewed and confirmed before sending).
argument-hint: "[aspects: comments tests errors types code simplify security | all] [post: teams jira github | all]"
---

# PR Review (`/pr:review`)

Orchestrate a comprehensive review of the **current working diff**. This command **wraps** the Anthropic `pr-review-toolkit` review agents (it does not reimplement them) and adds a YL-specific, portable **security pass**, then merges everything into a single report.

**Requested aspects (optional):** "$ARGUMENTS"

Scope: **local working diff only** (matches the toolkit). The report is headed with the detected **story key + branch** and the **suggested reviewers** from `team.json` (Phase 2). As of Phase 3 the same summary can **optionally** be posted back to Teams / Jira / GitHub — strictly opt-in, handled in Step 7. PR-number fetch (reviewing a PR that isn't your working diff) remains out of scope.

---

## Step 1 — Prerequisite self-check (do not fail silently)

The review agents come from the `pr-review-toolkit` plugin, which lives in the **Anthropic official** marketplace (`claude-plugins-official`), **not** in `ajudd-claude-plugins`. Confirm it is installed before relying on it:

```bash
# Is the toolkit present in either the marketplace clone or the install cache?
found=""
for base in "$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit" \
            "$HOME/.claude/plugins/cache"/*/pr-review-toolkit; do
  [ -d "$base" ] && found="$base" && break
done
if [ -n "$found" ]; then echo "toolkit-present: $found"; else echo "toolkit-missing"; fi
```

- **Present** → proceed with the full review (toolkit agents + security agent).
- **Missing** → print this notice, then **degrade gracefully**: continue with the security pass alone (still useful), and tell the user the toolkit agents were skipped.
  ```
  ⚠ pr-review-toolkit not found — the six code-quality review agents will be skipped.
    It ships in the Anthropic official marketplace, not ajudd-claude-plugins. To enable them:
      claude plugin marketplace add anthropics/claude-code
      claude plugin install pr-review-toolkit@claude-plugins-official
    Re-run /pr:review after installing. Running the security pass only for now.
  ```

## Step 2 — Determine scope

```bash
git diff --name-only              # unstaged changes
git diff --name-only --staged     # staged changes
git status --short
```

- Collect the set of changed files (staged + unstaged). If **nothing is changed**, say so and stop — there is nothing to review.
- Note file types present (source, tests, config, docs) — this drives which toolkit aspects apply.

## Step 3 — Gather review context (story / branch + reviewers)

This is the YL connective tissue the generic toolkit has no concept of. It feeds the
report header in Step 6 — it never changes what the review agents look at.

**Branch + story key.** Detect what this diff belongs to:

```bash
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null); echo "branch: ${branch:-unknown}"
# Story key detection, in order of preference:
# 1) an active session that is itself a story (BPT2-XXXX)
active=$(cat "$HOME/.claude/memory/sessions/$(basename "$(git rev-parse --show-toplevel 2>/dev/null)")/_active" 2>/dev/null)
# 2) fall back to parsing the branch name: feature/BPT2-<STORY>-<desc>
story=""
case "$active" in BPT2-*|CAB-*) story="$active";; esac
if [ -z "$story" ]; then
  # Jira key: uppercase letters + optional digits (e.g. BPT2), dash, number.
  story=$(printf '%s\n' "$branch" | grep -oE '[A-Z][A-Z0-9]*-[0-9]+' | head -1)
fi
echo "story: ${story:-none}"
```

- **Active session** — if the current session (per `_active`, or the session named in this
  conversation) is a story/CAB session, use that key directly.
- **Branch parse** — otherwise recover the key from the `feature/BPT2-<STORY>-<desc>`
  convention. The regex `[A-Z][A-Z0-9]*-[0-9]+` handles keys that carry a digit like
  `BPT2-6155` (a plain `[A-Z]+-…` would stop at `BPT` and miss the match) as well as
  digit-free keys like `CAB-9260`.
- **Neither** — report `Story: none detected`. Never invent a key.

**Suggested reviewers from `team.json`.** Read the roster and select everyone whose
`roles` includes `pr-reviewer`. **Never hardcode team data** (per global CLAUDE.md) — always
read the file. Use the portable path `~/.claude/plugins/team.json` so the command works for
any teammate who installs `pr`, not just the author:

```bash
TEAM="$HOME/.claude/plugins/team.json"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
if [ -f "$TEAM" ] && command -v "$PY" >/dev/null 2>&1; then
  "$PY" - "$TEAM" <<'PYEOF'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
names = [m.get("name", "?") for m in data.get("members", [])
         if "pr-reviewer" in (m.get("roles") or [])]
print(", ".join(names) if names else "none defined")
PYEOF
else
  echo "team.json not found"
fi
```

- **Found** → carry the list into the report's Context block as *Suggested reviewers*.
- **Missing / no `pr-reviewer` members** → **degrade gracefully**: header shows
  `Suggested reviewers: team.json not found` (or `none defined`) and the review proceeds
  normally. A missing roster never blocks a review.

Reviewer *selection* only surfaces the suggestions here — Step 3 itself posts nothing and
never assigns reviewers on a real PR (that assignment stays out of scope). Posting the
review summary back to Teams / Jira / GitHub is opt-in and handled later in Step 7.

## Step 4 — Select review aspects

Parse `$ARGUMENTS`. Recognized aspects: `comments`, `tests`, `errors`, `types`, `code`, `simplify`, `security`, `all`, plus `parallel` as a launch modifier.

The token `post` and everything after it (`teams` / `jira` / `github` / `all`) is a **post-back
selection**, not a review aspect — it is consumed by Step 7. Ignore it here (so `/pr:review post
teams` still runs the default full review, then posts).

- **No aspects given or `all`** → run every *applicable* toolkit aspect (see mapping below) **plus** the security pass. The security pass **always runs** unless the user explicitly narrows to non-security aspects only.
- **Specific aspects given** → run exactly those. If the user lists any aspect and omits `security`, still run security **unless** they pass an explicit narrow set that clearly excludes it (e.g. `/pr:review comments`); when in doubt, include security — it is the value this wrapper adds.

Applicability mapping (skip a toolkit agent when its trigger is absent, to reduce noise):

| Aspect | Toolkit agent | Run when |
|--------|---------------|----------|
| code | `pr-review-toolkit:code-reviewer` | always (general quality) |
| errors | `pr-review-toolkit:silent-failure-hunter` | error handling / catch / fallback changed |
| tests | `pr-review-toolkit:pr-test-analyzer` | test files changed |
| types | `pr-review-toolkit:type-design-analyzer` | new/modified types |
| comments | `pr-review-toolkit:comment-analyzer` | comments/docs added or changed |
| simplify | `pr-review-toolkit:code-simplifier` | run last, only on request or with `all` |
| security | this plugin's `security-reviewer` | **always** |

## Step 5 — Launch the agents

Launch each selected agent with the **Task** tool. Default to launching them in parallel (one message, multiple Task calls) unless the user asked for sequential; `code-simplifier` runs after the quality agents when included.

Launching the agents is independent of Step 3's context — the agents review the diff; the story/branch/reviewer context only decorates the report.

For **every toolkit agent**, prepend this YL guidance to the Task prompt so the toolkit's foreign-project assumptions don't produce noise (see the plugin's `CLAUDE.md` — this is the portable "counter via our own guidance, don't fork the agents" mechanism):

> **YL context for this review.** This is a Young Living repository. Ignore review rules that assume a specific foreign project's conventions — in particular do NOT flag the absence of `logForDebugging`, an `errorIds.ts` registry, or ES-module-only style; judge against the conventions actually present in this repo and its `CLAUDE.md`. Review the current working git diff. Report findings with file:line references, grouped by severity.

Launch the **security-reviewer** agent (this plugin) with a prompt to scan the working diff against its embedded OWASP Top 10 + active-exploit checklist and return findings in its documented section format.

## Step 6 — Consolidate into one report

Merge **all** agent outputs — toolkit findings and security findings together — into a single report. Fold the security agent's Critical/Important/Suggestions directly into the shared severity buckets, tagging each `[security]` so its origin is clear. De-duplicate overlapping findings (e.g. the code-reviewer and security agent both flagging the same injection). Attribute each finding to its agent.

Head the report with a **Context** block built from Step 3 — story key, branch, and the suggested reviewers — so the report states what it is reviewing and who should review the PR. Show each field's fallback verbatim (`none detected`, `team.json not found`) when the value is absent; never omit the block.

```markdown
# PR Review Summary

_Scope: working diff (N files) · Aspects: <list> · Toolkit: present/skipped_

## Context
- **Story:** BPT2-XXXX  (from active session / feature branch — or "none detected")
- **Branch:** <branch>
- **Suggested reviewers:** <names from team.json pr-reviewer role — or "team.json not found" / "none defined">

## Critical Issues (X)
- [security] <issue> — file:line
- [code-reviewer] <issue> — file:line

## Important Issues (X)
- [agent] <issue> — file:line

## Suggestions (X)
- [agent] <suggestion> — file:line

## Strengths
- <what's well done, including security-positive choices>

## Recommended Action
1. Fix critical issues first
2. Address important issues
3. Consider suggestions
4. Re-run /pr:review after fixes
```

**Step 6 always ends with this terminal report — it is complete on its own.** Posting the report anywhere is **opt-in** and handled next in Step 7; with no post selection the command stops here, exactly as in Phase 2. The Context block still only *suggests* reviewers and *names* the story/branch — assigning reviewers on a real PR, and fetching a PR by number, remain out of scope.

## Step 7 — Post-back (opt-in)

The Step 6 report is always printed and complete on its own. Step 7 lets you **also** send a
compact summary of it to Teams, Jira, and/or GitHub — the YL connective tissue the bare
toolkit has no concept of (the toolkit has zero write-back; this is the whole reason to wrap
it rather than call `/pr-review-toolkit:review-pr` directly).

**Nothing posts automatically.** Post-back happens only when the user opts in, and every send
is previewed and explicitly confirmed first — Teams / Jira / GitHub are external surfaces.

### 7a — Selection (which destinations)

Two ways to opt in; the default is **post nothing**:

- **Pre-arg** — a `post` token in `$ARGUMENTS` followed by destinations: `post teams`,
  `post jira github`, or `post all` (= every applicable destination).
- **Post-report prompt** — if the user did not pass `post`, offer once, after the report:
  ```
  Post this review?  teams · jira · github · all · no
  ```
  `no` (or no reply) → stop at the terminal report, exactly as Phase 2.

Only the destinations the user names are attempted. Each leg is independent — one being
skipped, degraded, or failing never blocks the others or the terminal report.

### 7b — Build the summary payload

From the Step 6 report, build a **compact digest** (not the whole report):
- the scope line (files, aspects);
- the Context block (story, branch, suggested reviewers);
- severity counts + a one-line **verdict** — e.g. "2 critical, 3 important — changes
  requested" vs "no critical/important — looks good";
- the **Critical and Important** items with `file:line` (omit the Suggestions/Strengths
  detail — tell the reader to re-run `/pr:review` for the full report).

This one digest is rendered per-surface in 7c–7e. Do **not** invent new wording per surface —
it is the same digest, formatted for each target's markup.

### 7c — Teams leg (rides `pr → comms → yl-msoffice`)

**Prerequisite chain + self-check (declare it — same pattern as the Step 1 toolkit check).**
The Teams post rides a transitive chain: `pr` → the **comms** plugin → the **`yl-msoffice`
MCP server**, and yl-msoffice ships in a *different* marketplace
(`youngliving-claude-plugins`). Per repo `CLAUDE.md` ("Declare cross-plugin / MCP
dependencies explicitly"), self-check the chain before any Teams write:

```bash
# comms present in the marketplace clone or the install cache?
comms=""
for base in "$HOME/.claude/plugins/marketplaces"/*/comms "$HOME/.claude/plugins/cache"/*/comms; do
  [ -d "$base" ] && comms="$base" && break
done
[ -n "$comms" ] && echo "comms-present: $comms" || echo "comms-missing"
# user identity — chat lookups + voice rules read it
[ -f "$HOME/.claude/plugins/user-config.json" ] && echo "user-config-present" || echo "user-config-missing"
```

Also confirm the yl-msoffice **send tool** is actually available in this session — a
`send_chat_message` tool. Its name may be rehosted (`mcp__plugin_yl-msoffice_*`,
`mcp__claude_ai_*`, …), so match on the **`send_chat_message` suffix**, never a hardcoded
namespace (the same fragility the comms hook guards against).

- **Chain intact** → proceed with the Teams post.
- **Anything missing** → print the fix and **degrade gracefully** — skip the Teams leg *only*,
  keep the terminal report and any Jira/GitHub legs:
  ```
  ⚠ Teams post-back skipped — the pr → comms → yl-msoffice chain is incomplete:
      comms missing        → claude plugin install comms@ajudd-claude-plugins
      user-config missing  → /setup:onboarding
      send_chat_message absent → install/enable yl-msoffice@youngliving-claude-plugins
    The review report above is complete; Jira/GitHub legs (if selected) still run.
  ```

**Target chat.** Resolve which chat this review belongs to:
- **Plugin work** (this is a plugin session) → the consolidated **Plugin — Aaron Work** chat.
- **Story session** → the story's chat (the active story session's `Teams chat` field, or the
  `known-chats.md` entry for the story key).
- Unresolved → ask which chat, or skip.

**No-Duplicates (required — per global `CLAUDE.md`).** Before drafting, **read the chat first**
(`list_chat_messages`, last ~20–50) and check whether a `/pr:review` summary for this same
story/branch was already posted. If so, post only the **delta** (what changed since — e.g.
"critical 2 → 0 after fixes"), not a re-summary. After sending, record a one-line note in the
session file's `## Teams Chat` section.

**Send via the comms flow — do NOT re-invent the format.** Hand the digest to the comms Teams
send sequence (the comms SKILL governs it): format to the **Teams HTML standard** — `<h2>`
section headers, `<b>` labels, `<ul>` structure, `<p>&nbsp;</p>` spacers; **no** `<hr>`,
`<pre>`, `<code>`, `<h1>`, `<h3>`, `<th>` (the comms `teams-html-lint` hook enforces exactly
this) — show the full preview in both plain + HTML, wait for explicit approval, then
`send_chat_message` → `confirm_action`.

### 7d — Jira leg (via the story plugin)

Only when a **story key was detected** in Step 3 (the Context block). No story → skip with a
note ("Jira leg skipped — no story detected").

Post the digest as a **comment** on the story — `/story:comment BPT2-XXXX`, or
`addCommentToJiraIssue`. Jira comments render markdown, so the digest goes as markdown (counts,
verdict, critical/important items with `file:line`). Preview the comment text and wait for
explicit approval before posting. A comment never modifies story fields or requirements.

### 7e — GitHub leg (via `gh` — net-new capability)

Self-check first — `gh` installed and authenticated, and a PR exists for the branch:

```bash
command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1 && echo "gh-ready" || echo "gh-unavailable"
gh pr view --json number,url 2>/dev/null || echo "no-pr-for-branch"
```

- **gh-ready + a PR exists** → post the digest as a **PR summary comment** (the MVP — one
  top-level comment, not inline-per-finding). Write the digest to a temp file and:
  ```bash
  gh pr comment <number> --body-file <digest.md>
  ```
  Preview the comment body and wait for explicit approval before running `gh pr comment`.
- **gh unavailable / not authenticated / no PR for the branch** → skip with a note; never
  block the other legs or the terminal report.

Inline-per-finding PR comments are deferred to a later item — the summary comment is the MVP.

### 7f — Report what posted

After the selected legs run, print one line per destination so the outcome is explicit:
```
Posted: Teams ✓ (Plugin — Aaron Work)  ·  Jira ✓ (BPT2-6155)  ·  GitHub — skipped (no PR)
```

## Usage

```
/pr:review                     # all applicable toolkit aspects + security, over the working diff
/pr:review security            # security pass only
/pr:review code errors         # general review + error handling + security
/pr:review all parallel        # everything, launched in parallel
/pr:review post teams          # review, then (after preview + confirm) post the summary to Teams
/pr:review post jira github     # review, then optionally post to Jira and GitHub
/pr:review all post all        # full review, then offer to post to every applicable destination
```

Post-back is always opt-in: with no `post` token the command prints the report and offers the
`teams · jira · github · all · no` prompt once; answer `no` (or nothing) to stop at the report.
