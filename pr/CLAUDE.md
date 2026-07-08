# pr plugin — review guidance

This file is the portable place to correct the `pr-review-toolkit` agents' assumptions
when they run over Young Living code. It is shipped **inside** the plugin, so it works
for every teammate who installs `pr` — we never fork the toolkit's agents.

`/pr:review` injects the substance of this guidance into each toolkit agent's Task
prompt (see `commands/review.md` Step 5). Keep this file and that injected block in sync.

## Counter the toolkit's foreign-project assumptions

Two of the toolkit agents (`silent-failure-hunter`, `code-simplifier`) carry hardcoded
conventions from the project they were authored against. On YL repos these produce noise:

- **`logForDebugging`** — the toolkit expects a logging helper by this name. YL code does
  not use it. Do not flag its absence; judge logging against what the repo actually uses.
- **`errorIds.ts` registry** — the toolkit expects a centralized error-id registry. YL
  code does not have one. Do not flag its absence.
- **ES-module-only style** — the toolkit may assume ESM. YL repos mix CommonJS/ESM/TS
  per project. Judge module style against the repo's own configuration.

General rule for reviewers: **review against the conventions actually present in the
target repo and its own `CLAUDE.md`, not against a remembered foreign baseline.**

## What this plugin adds on top of the toolkit

- A portable **security pass** (`agents/security-reviewer.md`) — OWASP Top 10 + active
  exploit patterns, embedded so it ships with the plugin (never read from a personal
  global `~/.claude/CLAUDE.md`).
- A single **consolidated report** merging toolkit + security findings.
- A **Context header** on the report (Phase 2, #25): the detected story key + branch, and
  the suggested reviewers read from `team.json` (the `pr-reviewer` role). Read the roster
  from `~/.claude/plugins/team.json` — never hardcode team data — and degrade gracefully
  when it is absent (`team.json not found`) rather than failing the review.
- **Opt-in post-back** of the summary to Teams / Jira / GitHub (Phase 3, #26): a new
  additive Step 7, default-off, two-gate (selection → preview + confirm per leg). The Teams
  leg rides `pr → comms → yl-msoffice` (yl-msoffice is in a different marketplace) and
  self-checks the chain, degrading gracefully; it hands the send to the **comms** flow rather
  than re-inventing the Teams HTML standard. GitHub post-back (`gh pr comment`) is net-new —
  the toolkit has no write-back at all.
