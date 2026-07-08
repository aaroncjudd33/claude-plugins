# pr

Pull-request lifecycle plugin for Young Living. First command: **`/pr:review`**.

## What `/pr:review` does

Reviews the **current working diff** by orchestrating the Anthropic `pr-review-toolkit`
review agents and adding a portable YL **security pass** (OWASP Top 10 + active exploit
patterns), then merging everything into one consolidated report:
**Critical / Important / Suggestions / Strengths**.

It **wraps** the toolkit — it does not reimplement it. The toolkit owns code-quality
review; this plugin adds the security scan, and (in later phases) reviewer roster,
story/branch context, and post-back to Teams/Jira/GitHub.

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

## Phase 1 scope

Local working diff → one terminal report. Reviewer roster + story/branch context (#25)
and post-back to Teams/Jira/GitHub (#26) are later phases.
