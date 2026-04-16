---
name: comment
description: Add a comment to a Jira story — for progress notes, PR links, deploy status, decisions, and handoff notes. Does not modify story fields or requirements.
argument-hint: "[BPT2-XXXX] [comment text]"
---

# /story:comment [BPT2-XXXX] [comment text]

Add a comment to an existing Jira story. Use this for anything that happens *after* a story is in flight — progress updates, PR links, deployment notes, decisions made during implementation, handoff context. Comments do not alter the original requirements on the card.

## Steps

1. **Resolve the story key** — Use the argument if provided. If not, check the active session file at `~/.claude/memory/sessions/<slug>/_active` and read the corresponding session file to find the current story key. If still unclear, ask.

2. **Resolve the comment text** — Use the argument if provided. If not, ask what the comment should say. If the current conversation contains obvious context (e.g. a PR was just created, a deploy just ran), offer a draft based on that context and ask for confirmation before posting.

3. **Post the comment** — Call `addCommentToJiraIssue` with the story key and comment body. Markdown is supported — use it for links, bold, bullet lists, code blocks where helpful.

4. **Confirm** — Report the story key and a one-line summary of what was posted.

## Common Comment Patterns

- **PR submitted:** `PR submitted: [Title](url) — ready for review`
- **Deployed to env:** `Deployed to env6 — ready for test`
- **CAB note:** `Deploying in CAB-XXXX — [summary]\nScheduled: [date]\nRelease branch: release/CAB-XXXX\nPR: [title] — Pull Request #N ([link])`
- **Decision note:** `Decision: [what was decided and why]`
- **Handoff:** `Handing off to [name] — [context they need]`
- **Blocked:** `Blocked on [what] — [who needs to act]`

## Notes

- Comments are the right tool once a story is In Progress — they preserve the original requirements while keeping the card up to date
- The CAB plugin posts its own comment automatically when a CAB card is created — no need to duplicate that
- For state transitions (In Progress → In Review → Done), use `/story:update`
