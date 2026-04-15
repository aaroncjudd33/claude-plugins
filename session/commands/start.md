---
name: start
description: Start a working session. Loads last session context and routes into the right workflow.
---

# Session Start

Begin a working session. Loads existing work state and routes into the right workflow.

## Instructions

### 1. Load Last Session State

Read `C:\Users\ajudd\.claude\memory\session_active.md`.

If it exists, print a brief "where we left off":
```
Last session
  Project:    [project name or path]
  Story:      BPT2-XXXX — [title]  (omit if no active story)
  Branch:     [branch]
  Last work:  [1 sentence]
  Open items: [bullets or "none"]
  Next step:  [suggested action]
```

If the file does not exist, skip and go straight to step 2.

### 2. Ask What We're Doing

If last session state exists:
> "Resume [last context], or something different?"

If no last session state:
> "What are we working on?"

Options to present:
- **Resume** [story/project from last session]
- **Pick up a new story** (provide Jira URL or key)
- **Create a CAB**
- **Something else** — describe it

### 3. Route Based on Choice

**Resume story:**
1. Read the Jira issue (`getJiraIssue`) — verify current status matches memory
2. Check git branch — confirm it matches the story, offer to switch if not
3. Summarize current state: what's done, what's open, what's next

**Pick up new story (kickoff):**
- Read the Jira issue → transition to In Progress → create feature branch
- Investigate codebase, check for Teams chat, check for Confluence page
- Follow any kickoff workflow saved in project memory

**Create CAB:**
- Route to `/cab:create-cab`

**Something else:**
- Understand the task, load relevant context, confirm approach, proceed
