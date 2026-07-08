# pr plugin — review guidance

This file is the portable place to correct the `pr-review-toolkit` agents' assumptions
when they run over Young Living code. It is shipped **inside** the plugin, so it works
for every teammate who installs `pr` — we never fork the toolkit's agents.

`/pr:review` injects the substance of this guidance into each toolkit agent's Task
prompt (see `commands/review.md` Step 4). Keep this file and that injected block in sync.

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

Later phases (tracked separately): reviewer roster from `team.json` + story/branch
context (#25); post-back to Teams/Jira/GitHub (#26).
