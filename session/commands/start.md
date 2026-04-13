---
name: start
description: Start a working session. Loads last session context and routes into the right workflow.
---

# Session Start

Begin a working session. Loads existing work state and routes into the right workflow.

## Instructions

### 1. Load Last Session State

Read `project_active_session.md` from the memory system at:
`C:\Users\ajudd\.claude\projects\C--dev-virtual-office\memory\project_active_session.md`

If it exists, print a brief "where we left off":
```
Last session
  Story:      BPT2-XXXX — [title]
  Status:     [Jira status]
  Branch:     [branch]
  Last work:  [1 sentence]
  Open items: [bullets or "none"]
  Next step:  [suggested action]
```

If nothing is there, skip and go straight to step 2.

### 2. Ask What We're Doing

If last session state exists:
> "Resume [BPT2-XXXX], or something different?"

If no last session state:
> "What are we working on?"

Options to present:
- **Resume [story from last session]**
- **Pick up a new story** (provide Jira URL or key)
- **Create a CAB**
- **Something else** — describe it

### 3. Route Based on Choice

**Resume story:**
1. Read the Jira issue (`getJiraIssue`) — verify current status matches memory
2. Check git branch — confirm it matches the story, offer to switch if not
3. Load local story doc if it exists (`C:\Users\ajudd\claude\jira-stories\<project>\<slug>.md`)
4. Summarize current state: what's done, what's open, what's next
5. Check if a Teams chat exists for the story
6. Register story in `~/.claude/jira-stories.json` if not already there

**Pick up new story (kickoff):**
- Follow the story kickoff workflow from memory (`feedback_story_kickoff_workflow.md`)
- Steps: read Jira → transition to In Progress → register in registry → create feature branch → investigate codebase → Teams chat prompt → Confluence prompt → Playwright tasks prompt

**Create CAB:**
- Route to `/cab:create-cab`

**Something else:**
- Understand the task, load relevant context, confirm approach, proceed
