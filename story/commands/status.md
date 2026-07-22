---
name: status
description: Show where a BPT2 story is in the creation/handoff process — read from the local session file only, no live Jira calls.
argument-hint: "[BPT2-XXXX]"
---

# /story:status [BPT2-XXXX]

Read-only "where am I" checklist for a story, sourced entirely from the local session file
and the links registry — no Jira reads.

## Steps

### 1. Resolve story key

Use the argument if provided. If not, extract the repo slug from `pwd` (last path component),
read `~/.claude/memory/sessions/<slug>/_active`, and use that story key. If still unclear, ask.

### 2. Read the session file

Resolve `session_root`: check `<git-repo-root>/.claude/sessions/`; if it exists use it,
otherwise `~/.claude/memory/sessions/<slug>/`.

Read `<session_root>/<story-key>.md`. If it does not exist, report:
```
No local session found for <story-key>. Run /story:create or /session:start to establish one.
```
and stop.

### 3. Check the links registry

Read `~/.claude/browser-links.json`. Check whether a `story:<story-key>` entry exists under
`links` and a `<story-key>` entry exists under `workspaces`.

### 4. Build the checklist

`/story:create` runs its steps synchronously in a single pass, so a session file existing at
all means the required steps (issue creation, description + assignee, status transition,
session file write) already completed. The two link-related steps in `/story:create` are
optional (comment, related-issue linking) and aren't captured in the session file, so mark
them unverified rather than guessing. The links-workspace step **is** independently checkable
against `browser-links.json` from step 3.

Display:

```
<story-key> — <one-line summary from the session file's "Last worked on" field>

  Process checklist:
  [x] Issue created
  [x] Description + assignee set
  [x] Status transitioned            (default: Ready For Work, unless Backlog was requested)
  [ ] Comment added                  — optional step, not tracked locally; check the Jira issue directly
  [ ] Related issues linked          — optional step, not tracked locally; check the Jira issue directly
  [x or  ] Links workspace registered — from the browser-links.json check above
  [x] Session file written

  Branch:        <Branch field>
  Related CAB:   <Related CAB field>
  Open items:    <Open items field>
  Next step:     <Next step field>
```

Mark "Links workspace registered" `[x]` only if both the `story:<key>` link and `<key>`
workspace were found in step 3; otherwise `[ ]`.

### 5. Report

Print the block above. This is a read-only view — no Jira calls, no writes.
