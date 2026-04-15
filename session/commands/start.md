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

### 2. Detect Project Context

Run `pwd` to get the current working directory and determine which type of project this is:

- **Plugins project**: path contains `ajudd-claude-plugins`
- **Work project**: path contains `C:\dev\` or `C:/dev/`
- **Unknown**: anything else

### 3. Ask What We're Doing

**If last session state exists:**
> "Resume [last context], or something different?"

**If no last session state:**
> "What are we working on?"

Present options based on project context:

**Plugins project options:**

Read `.claude-plugin/marketplace.json` and list each plugin by name, then add two more:
- Resume [last plugin work] *(only if session state exists)*
- [plugin-name] — [plugin description, one short phrase]  *(one line per plugin)*
- New plugin
- Something else — describe it

**Work project options:**
- Resume [story from last session] *(if session state exists)*
- Pick up a new story (provide Jira URL or key)
- Create a CAB
- Something else — describe it

**Unknown project options:**
- Resume [last context] *(if session state exists)*
- Start something new — describe it

### 4. Route Based on Choice

**Plugins — work on existing plugin:**
1. Read the plugin's files (`plugin.json`, command `.md` files, skill `SKILL.md` if present)
2. Ask what needs to change if not already stated
3. Confirm approach before making changes

**Plugins — new plugin:**
1. Ask for the plugin name and what it should do
2. Walk through the folder structure and create the files
3. Add entry to `marketplace.json`, commit, push, install

**Work — resume story:**
1. Read the Jira issue (`getJiraIssue`) — verify current status matches memory
2. Check git branch — confirm it matches the story, offer to switch if not
3. Summarize current state: what's done, what's open, what's next

**Work — pick up new story (kickoff):**
- Read the Jira issue → transition to In Progress → create feature branch
- Investigate codebase, check for Teams chat, check for Confluence page

**Work — create CAB:**
- Route to `/cab:create-cab`

**Something else (any project):**
- Understand the task, load relevant context, confirm approach, proceed
