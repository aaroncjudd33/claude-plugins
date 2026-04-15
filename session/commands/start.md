---
name: start
description: Start a working session. Loads last session context and routes into the right workflow.
---

# Session Start

Begin a working session. Establishes session identity, Teams chat, and routes into the right workflow.

## Instructions

### 1. Load Last Session State

Read `C:\Users\ajudd\.claude\memory\session_active.md`.

If it exists, print:
```
Last session
  Type:       [type]
  Name:       [name]
  Teams chat: [teams_chat or "none"]
  Branch:     [branch]  (omit if n/a)
  Last work:  [1 sentence]
  Open items: [bullets or "none"]
  Next step:  [suggested action]
```

If the file does not exist, skip to step 2.

### 2. Detect Session Type

Run `pwd` and map to a default session type:
- **plugin** — path contains `ajudd-claude-plugins`
- **story / cab** — path contains `C:\dev\` or `C:/dev/`
- **general** — anything else

### 3. Present Options

**Plugin project:**

Read `.claude-plugin/marketplace.json` and list each plugin by name, then add:
- Resume [name] *(only if last session was plugin type)*
- [plugin-name] — [one-phrase description] *(one line per plugin)*
- New plugin
- Something else — describe it

**Work project:**
- Resume [BPT2-XXXX — title] *(only if last session was story type)*
- Pick up a story (Jira URL or key)
- Start a CAB
- Something else — describe it

**General / unknown project:**
- Resume [name] *(only if last session was general type)*
- Start something new — give it a name and category

### 4. Establish Session Identity

Once the user picks what they're working on, resolve:

| Type | name | teams_chat |
|------|------|------------|
| plugin | plugin name (e.g. `Session`, `Office`) | `<Name> - Claude Plugin` |
| story | story key (e.g. `BPT2-1234`) | `BPT2-XXXX — <title>` (from Jira) |
| cab | CAB number (e.g. `CAB-456`) | `CAB-XXX — <description>` (from Jira) |
| general | name the user provides | `<Name> - Claude <Category>` |

For **general**, also ask for a category if not obvious: Research / Prototype / Training / Other.

### 5. Teams Chat Setup

Look in `C:\Users\ajudd\.claude\plugins\marketplaces\ajudd-claude-plugins\office\skills\office\references\known-chats.md` for a chat whose Name or Topic matches the expected `teams_chat` value.

- **Found:** "Using Teams chat: [name]" — proceed, or offer to repoint if the user wants a different one
- **Not found:** "No chat found for `[teams_chat]`. Create it? (Yes / Skip / Use a different chat)"
  - **Yes:** create the chat via yl-msoffice MCP, add the entry to `known-chats.md`
  - **Skip:** set `teams_chat` to `none` — Teams steps in checkpoint will be skipped
  - **Different:** ask which existing chat to use, store that name instead

### 6. Write Initial Session State

Write `C:\Users\ajudd\.claude\memory\session_active.md` now so the session identity is persisted before work begins:

```
---
updated: [today's date]
---

# Active Session State

- **Type:** [type]
- **Name:** [name]
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Project:** [project name or path]
- **Branch:** [branch or "n/a"]
- **Last worked on:** [will be updated at checkpoint]
- **Open items:** [carried from previous session, or "none"]
- **Next step:** [will be updated at checkpoint]
```

### 7. Route Based on Choice

**Plugin — existing plugin:**
1. Read `plugin.json`, all command `.md` files, and `SKILL.md` if present
2. Ask what needs to change if not already stated
3. Confirm approach before making changes

**Plugin — new plugin:**
1. Ask for the plugin name and what it should do
2. Create the folder structure and files
3. Add entry to `marketplace.json`, commit, push, install

**Story — resume:**
1. `getJiraIssue` — verify status matches memory
2. Check git branch — confirm it matches, offer to switch if not
3. Summarize: what's done, what's open, what's next

**Story — new kickoff:**
1. `getJiraIssue` → transition to In Progress → create feature branch
2. Investigate codebase, confirm Teams chat exists, check Confluence page

**CAB — new:**
- Route to `/cab:create-cab`

**CAB — resume:**
1. Read the CAB card from Jira
2. Check release branch status

**General:**
1. Ensure `~/.claude/sessions/<name>/` exists (create if not)
2. Load any prior notes from that folder
3. Understand the task, confirm approach, proceed
