---
name: review
description: Review the working diff with the pr-review-toolkit agents plus a portable YL OWASP/exploit security pass, then print one consolidated Critical/Important/Suggestions/Strengths report headed with the detected story/branch and the suggested reviewers from team.json.
argument-hint: "[aspects: comments tests errors types code simplify security | all]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# PR Review (`/pr:review`)

Orchestrate a comprehensive review of the **current working diff**. This command **wraps** the Anthropic `pr-review-toolkit` review agents (it does not reimplement them) and adds a YL-specific, portable **security pass**, then merges everything into a single report.

**Requested aspects (optional):** "$ARGUMENTS"

Scope: **local working diff only** (matches the toolkit). As of Phase 2 the report is also headed with the detected **story key + branch** and the **suggested reviewers** from `team.json`. PR-number fetch and post-back to Teams/Jira/GitHub remain a later phase (#26) — do not attempt them here.

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

Reviewer *selection* only surfaces the suggestions here — assigning them on a real PR and
posting the review back are #26. Do not post anything.

## Step 4 — Select review aspects

Parse `$ARGUMENTS`. Recognized aspects: `comments`, `tests`, `errors`, `types`, `code`, `simplify`, `security`, `all`, plus `parallel` as a launch modifier.

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

**This ends at the terminal report.** The Context block *suggests* reviewers and *names* the story/branch, but does not act on them. Do not post to Teams, Jira, or GitHub, assign the reviewers on a PR, or fetch a PR by number — those are a later phase (`#26`).

## Usage

```
/pr:review                     # all applicable toolkit aspects + security, over the working diff
/pr:review security            # security pass only
/pr:review code errors         # general review + error handling + security
/pr:review all parallel        # everything, launched in parallel
```
