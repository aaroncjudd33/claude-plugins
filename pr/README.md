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
and (in a later phase) post-back to Teams/Jira/GitHub.

## Prerequisite — pr-review-toolkit (REQUIRED)

`/pr:review` depends on **`pr-review-toolkit`**, which ships in the **Anthropic official**
marketplace (`claude-plugins-official`), *not* in `ajudd-claude-plugins`. Install it:

```
claude plugin marketplace add anthropics/claude-code
claude plugin install pr-review-toolkit@claude-plugins-official
```

If it is missing, `/pr:review` self-checks, tells you how to install it, and degrades
gracefully — running the embedded security pass alone rather than failing.

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
```

## Scope

Local working diff → one terminal report, headed with the detected story/branch and the
suggested reviewers from `team.json` (#25, shipped). Post-back to Teams/Jira/GitHub (#26)
is a later phase.

The roster is read portably from `~/.claude/plugins/team.json` (never hardcoded); if it is
missing, the reviewer suggestion degrades to `team.json not found` and the review still runs.
