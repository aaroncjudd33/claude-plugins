---
name: review
description: Review the working diff with the pr-review-toolkit agents plus a portable YL OWASP/exploit security pass, then print one consolidated Critical/Important/Suggestions/Strengths report.
argument-hint: "[aspects: comments tests errors types code simplify security | all]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# PR Review (`/pr:review`)

Orchestrate a comprehensive review of the **current working diff**. This command **wraps** the Anthropic `pr-review-toolkit` review agents (it does not reimplement them) and adds a YL-specific, portable **security pass**, then merges everything into a single report.

**Requested aspects (optional):** "$ARGUMENTS"

Phase 1 scope: **local working diff only** (matches the toolkit). PR-number fetch, reviewer roster, and post-back to Teams/Jira/GitHub are later phases — do not attempt them here.

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

## Step 3 — Select review aspects

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

## Step 4 — Launch the agents

Launch each selected agent with the **Task** tool. Default to launching them in parallel (one message, multiple Task calls) unless the user asked for sequential; `code-simplifier` runs after the quality agents when included.

For **every toolkit agent**, prepend this YL guidance to the Task prompt so the toolkit's foreign-project assumptions don't produce noise (see the plugin's `CLAUDE.md` — this is the portable "counter via our own guidance, don't fork the agents" mechanism):

> **YL context for this review.** This is a Young Living repository. Ignore review rules that assume a specific foreign project's conventions — in particular do NOT flag the absence of `logForDebugging`, an `errorIds.ts` registry, or ES-module-only style; judge against the conventions actually present in this repo and its `CLAUDE.md`. Review the current working git diff. Report findings with file:line references, grouped by severity.

Launch the **security-reviewer** agent (this plugin) with a prompt to scan the working diff against its embedded OWASP Top 10 + active-exploit checklist and return findings in its documented section format.

## Step 5 — Consolidate into one report

Merge **all** agent outputs — toolkit findings and security findings together — into a single report. Fold the security agent's Critical/Important/Suggestions directly into the shared severity buckets, tagging each `[security]` so its origin is clear. De-duplicate overlapping findings (e.g. the code-reviewer and security agent both flagging the same injection). Attribute each finding to its agent.

```markdown
# PR Review Summary

_Scope: working diff (N files) · Aspects: <list> · Toolkit: present/skipped_

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

**Phase 1 ends at the terminal report.** Do not post to Teams, Jira, or GitHub — that is a later phase (`#26`). Do not attempt to fetch a PR by number or select reviewers — those are later phases (`#25`).

## Usage

```
/pr:review                     # all applicable toolkit aspects + security, over the working diff
/pr:review security            # security pass only
/pr:review code errors         # general review + error handling + security
/pr:review all parallel        # everything, launched in parallel
```
