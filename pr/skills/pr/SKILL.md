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
3. **posting results back** to Teams / Jira / GitHub — Phase 3 (#26, shipped).

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

### Additional prerequisite — the Teams post-back chain (optional, Phase 3)

The **Teams** leg of post-back (Step 7c) rides a transitive chain: `pr` → the **comms**
plugin (this marketplace) → the **`yl-msoffice` MCP server** — and yl-msoffice ships in a
*different* marketplace, `youngliving-claude-plugins`. This chain is only needed if you post a
review to Teams; the review itself and the Jira/GitHub legs do not depend on it. Enable it
with:

```
claude plugin install comms@ajudd-claude-plugins        # this marketplace
# yl-msoffice MCP — from youngliving-claude-plugins (separate marketplace)
/setup:onboarding                                        # writes user-config.json (chat lookups)
```

Step 7c self-checks this chain and **degrades gracefully** — a missing link skips the Teams
leg only (printing the fix) and never fails the review or the other legs.

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
reviewers on a real PR is still out of scope; posting the review summary back shipped in
Phase 3 (below).

## Post-back to Teams / Jira / GitHub (Phase 3, #26)

Step 7 of `/pr:review` can post the consolidated summary back to three surfaces — the
connective tissue the bare toolkit lacks entirely (it has zero write-back). It is **strictly
opt-in and never automatic**, via a **two-gate** model:

1. **Selection** — either a `post` pre-arg (`/pr:review post teams jira`, `post all`) or, if
   none was passed, a single post-report prompt (`teams · jira · github · all · no`). Default
   is **post nothing** — with no selection the command stops at the terminal report.
2. **Preview + confirm** — every leg shows a full preview and waits for explicit approval
   before the actual write (Teams / Jira / GitHub are external surfaces).

The three legs are independent — one skipping or degrading never blocks the others:

- **Teams** rides the transitive chain `pr → comms → yl-msoffice` (yl-msoffice lives in the
  *different* `youngliving-claude-plugins` marketplace). Step 7c **self-checks** the chain
  (comms installed, `user-config.json` present, a `send_chat_message` tool available — matched
  by suffix, never a hardcoded namespace) and **degrades gracefully** — a missing link skips
  the Teams leg only and prints the fix, keeping the report + other legs. The send is handed to
  the **comms** send flow (its SKILL owns the HTML standard + `send_chat_message` →
  `confirm_action`) — the format is **not** re-invented here. The **No-Duplicates** rule
  applies: read the chat first, post only the delta, record a one-line note in the session.
- **Jira** posts a story comment (via the story plugin / `addCommentToJiraIssue`) — only when
  a story key was detected; otherwise skipped.
- **GitHub** posts a **PR summary comment** via `gh pr comment` (genuinely net-new — the
  toolkit has no GitHub write-back). Self-checks `gh` auth + that a PR exists for the branch;
  inline-per-finding comments are deferred (summary comment is the MVP).

## Current boundary

`/pr:review` reviews the **local working diff**, prints **one terminal report** (Context
header + Critical / Important / Suggestions / Strengths), and can **optionally** post a compact
summary of it to Teams / Jira / GitHub (Step 7, opt-in). What remains out of scope: fetching a
PR by number to review something other than the working diff, and assigning reviewers on a
real PR.
