# pr

Pull-request lifecycle plugin for Young Living. First command: **`/pr:review`**.

## What `/pr:review` does

Reviews the **current working diff** by orchestrating the Anthropic `pr-review-toolkit`
review agents and adding a portable YL **security pass** (OWASP Top 10 + active exploit
patterns), then merging everything into one consolidated report:
**Critical / Important / Suggestions / Strengths**. The report is headed with a **Context
block** — the detected story key + branch, and the suggested reviewers from `team.json`.

It **wraps** the toolkit — it does not reimplement it. The toolkit owns code-quality
review; this plugin adds the security scan, the story/branch + reviewer context header,
and (opt-in) post-back of the summary to Teams / Jira / GitHub.

## Prerequisite — pr-review-toolkit (REQUIRED)

`/pr:review` depends on **`pr-review-toolkit`**, which ships in the **Anthropic official**
marketplace (`claude-plugins-official`), *not* in `ajudd-claude-plugins`. Install it:

```
claude plugin marketplace add anthropics/claude-code
claude plugin install pr-review-toolkit@claude-plugins-official
```

If it is missing, `/pr:review` self-checks, tells you how to install it, and degrades
gracefully — running the embedded security pass alone rather than failing.

## Prerequisite — Teams post-back chain (only if you post to Teams)

The **Teams** leg of post-back rides a transitive chain: `pr` → **comms** (this marketplace)
→ the **`yl-msoffice` MCP server**, and yl-msoffice ships in a *different* marketplace
(`youngliving-claude-plugins`). It is only needed to post a review to Teams — the review
itself and the Jira/GitHub legs do not depend on it:

```
claude plugin install comms@ajudd-claude-plugins   # this marketplace
# plus the yl-msoffice MCP from youngliving-claude-plugins, and /setup:onboarding
```

`/pr:review` self-checks this chain before any Teams write and **degrades gracefully** — a
missing link skips the Teams leg only (printing the fix) and never fails the review.

## Install

```
claude plugin install pr@ajudd-claude-plugins
```

Restart Claude Code to load the command.

## Usage

```
/pr:review                # all applicable toolkit aspects + security, over the working diff
/pr:review security       # security pass only
/pr:review code errors    # general review + error handling + security
/pr:review all parallel   # everything, launched in parallel
/pr:review post teams     # review, then (after preview + confirm) post the summary to Teams
/pr:review post jira github  # review, then optionally post to Jira and GitHub
```

## Scope

Local working diff → one terminal report, headed with the detected story/branch and the
suggested reviewers from `team.json` (#25). The same summary can **optionally** be posted
back to Teams / Jira / GitHub (#26) — strictly opt-in (a `post` arg or a post-report prompt;
default posts nothing) and previewed + confirmed before each send. Fetching a PR by number
(reviewing something other than the working diff) is still out of scope.

The roster is read portably from `~/.claude/plugins/team.json` (never hardcoded); if it is
missing, the reviewer suggestion degrades to `team.json not found` and the review still runs.
