---
name: pr
description: "Background skill — do not run directly. Use /pr:review to review a diff. Auto-loads when the user mentions: reviewing a PR or diff, running a code review before merge, checking changes for security issues / OWASP / vulnerabilities, pre-PR review, or the pr-review-toolkit. Covers the pr plugin's wrap-the-toolkit design, the embedded YL security pass, and the pr-review-toolkit prerequisite."
---

# pr Plugin Skill

The `pr` plugin covers the pull-request lifecycle at Young Living. Its first command is
`/pr:review`; create/status/link/merge commands join the same `/pr:*` prefix in later work.

## Core design: WRAP, don't build

`/pr:review` **orchestrates** the Anthropic `pr-review-toolkit` review agents — it does
**not** reimplement them. The toolkit's review logic is mature and prompt-based; copying it
would be waste. What the generic toolkit lacks is the YL connective tissue this marketplace
exists to add (same shape as story→Jira, release→CAB, comms→Teams):

1. a **security pass** (OWASP Top 10 + active exploit patterns) — Phase 1;
2. a **reviewer roster** from `team.json` + story/branch context in the report header —
   Phase 2 (#25, shipped);
3. **posting results back** to Teams / Jira / GitHub — Phase 3 (#26).

Gaps in the bare toolkit that motivate the wrap: no GitHub write-back (terminal output
only), working-diff only (no PR-number fetch), no team/roster/checklist config, and **no
OWASP/exploit scanning** (it defers security to the built-in `/security-review`).

## Prerequisite — pr-review-toolkit (different marketplace)

`/pr:review` depends on **`pr-review-toolkit`**, which ships in the **Anthropic official**
marketplace (`claude-plugins-official`), **not** in `ajudd-claude-plugins`. This is a
required prerequisite for the code-quality half of the review. Install it with:

```
claude plugin marketplace add anthropics/claude-code
claude plugin install pr-review-toolkit@claude-plugins-official
```

`/pr:review` **self-checks** for the toolkit (Step 1) and, if it is missing, prints the
fix and **degrades gracefully** — it still runs the embedded security pass rather than
failing the whole review.

The toolkit provides six review agents that `/pr:review` launches via Task:
`code-reviewer`, `silent-failure-hunter`, `pr-test-analyzer`, `type-design-analyzer`,
`comment-analyzer`, `code-simplifier`.

## The embedded security pass (portable)

`agents/security-reviewer.md` carries the full OWASP Top 10 + active-exploit checklist
**embedded in the agent file** — deliberately copied in, not read from any personal global
`~/.claude/CLAUDE.md`, so the scan works for every teammate who installs the plugin
("behavior ships IN the plugin"). It reviews the working diff and returns severity-grouped
findings that `/pr:review` folds into the consolidated report.

## Countering toolkit noise on YL repos

Two toolkit agents (`silent-failure-hunter`, `code-simplifier`) assume a foreign project's
conventions (`logForDebugging`, an `errorIds.ts` registry, ES-module-only style). Rather
than fork the agents, `/pr:review` injects YL guidance into each agent's Task prompt (and
the same guidance lives in the plugin's `CLAUDE.md`) telling them to judge against the
target repo's own conventions.

## Story / branch + reviewer context (Phase 2, #25)

Step 3 of `/pr:review` builds a **Context block** that heads the report:

- **Branch** from `git rev-parse --abbrev-ref HEAD`.
- **Story key** detected in order — an active story/CAB session (`_active`), else the
  `feature/BPT2-<STORY>-<desc>` branch convention (`grep -oE '[A-Z][A-Z0-9]*-[0-9]+'`,
  which matches digit-bearing keys like `BPT2-6155`), else `none detected`. Never invented.
- **Suggested reviewers** — members whose `roles` includes `pr-reviewer`, read from
  `~/.claude/plugins/team.json` (portable path, never hardcoded per global CLAUDE.md).
  Missing roster degrades to `team.json not found` — it never blocks the review.

This is *context only*: it names the story/branch and *suggests* reviewers. Assigning
reviewers on a real PR and posting the review back are #26.

## Current boundary

`/pr:review` reviews the **local working diff** and prints **one terminal report**
(Context header + Critical / Important / Suggestions / Strengths). No PR-number fetch,
no external post-back — those are #26.
