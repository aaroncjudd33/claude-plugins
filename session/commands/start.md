---
name: start
description: Start a working session. Loads last session context and routes into the right workflow.
---

# Session Start

Begin a working session. Establishes session identity, Teams chat, and routes into the right workflow.

## Instructions

### 1. Derive Repo Slug and Session Type

Run `pwd` and extract the **last path component** as the repo slug:
- `/c/Users/ajudd/.claude/plugins/marketplaces/ajudd-claude-plugins` → `ajudd-claude-plugins`
- `/c/dev/gen-leadership-bonus` → `gen-leadership-bonus`

Detect session type from the path:
- **plugin** — path contains `ajudd-claude-plugins`
- **story / cab** — path contains `/dev/`
- **personal** — path contains `/c/claude/`
- **general** — anything else

### 2. Load Repo Sessions

List all `.md` files in `~/.claude/memory/sessions/<slug>/` (skip `_active` and `_inbox*` files).

For each file, read it and extract: `Name`, `Branch`, `Last worked on`.

For **plugin sessions**, also check `~/.claude/memory/sessions/<slug>/_inbox_<name>.md` and count lines that contain actual content (skip the header line and blank lines). If count > 0, note it for display.

For **non-plugin sessions**, check `~/.claude/memory/sessions/<slug>/_inbox.md` and count content lines the same way.

If sessions exist, print a numbered list. Append `📬 N` at the end of any line with inbox items:
```
Sessions in <slug>
  [1]  <name>  |  <type>  |  <branch>  |  <last worked on — 1 sentence>
  [2]  <name>  |  <type>  |  <branch>  |  <last worked on — 1 sentence>  📬 3
```

If the directory does not exist or is empty, skip this section.

### 3. Present Options

**Plugin project** — read `.claude-plugin/marketplace.json` and list each plugin. For plugins with existing sessions, check the inbox count (already computed in step 2) and append `📬 N` if items exist:
- **[N] Resume <plugin-name>** — <last worked on>  📬 N *(if inbox items exist)*
- **<plugin-name>** — <one-phrase description> *(one line per plugin in marketplace.json not already in sessions list)*
- New plugin
- Something else — describe it

**Work project:**
- **[N] Resume <BPT2-XXXX>** — <last worked on> *(one line per existing session)*
- Pick up a story (Jira URL or key)
- Start a CAB
- Something else — describe it

**Personal project** (path under `/c/claude/`):
- **[N] Resume <name>** — <last worked on> *(one line per existing session)*
- Start something new — give it a name

**General / unknown project:**
- **[N] Resume <name>** — <last worked on> *(one line per existing session)*
- Start something new — give it a name and category

### 4. User Picks — Load or Create Session File

**Resume existing [N]:**
- Read `~/.claude/memory/sessions/<slug>/<name>.md`
- Display the full last session block:
  ```
  Resuming <name>
    Branch:          [branch]
    Last work:       [last worked on]
    Open items:      [bullets or "none"]
    Next step:       [next step]
    Related CAB:     [CAB-XXX]   ← story type only, omit if none
    Related stories: [BPT2-XXXX, ...]   ← cab type only, omit if none
  ```

**New story/plugin/personal/general — session filename:**
- story → `BPT2-XXXX.md`
- plugin → `<plugin-name>.md`
- cab → `CAB-XXX.md`
- personal → `<name>.md`
- general → `<name>.md`

### 5. Check Inbox

**For plugin sessions**, check `~/.claude/memory/sessions/<slug>/_inbox_<name>.md` (e.g. `_inbox_release.md`). This is the plugin-specific inbox where cross-scope work from other sessions is routed.

**For all other sessions**, check `~/.claude/memory/sessions/<slug>/_inbox.md`.

If the inbox file exists and has content beyond the header line, display it:

```
Inbox (<N> item(s))
  [date] from <source-slug> / <session-name>
    - <item>
```

Ask: "Clear inbox? (Yes / Keep)"
- **Yes:** overwrite the file with just the header (`# Inbox — <name> plugin` for plugin type, `# Inbox — <slug>` otherwise)
- **Keep:** leave it; note the inbox items in the `Open items` field of the session state

If the file does not exist or contains only the header, skip silently.

**Additionally**, for plugin sessions, check `~/.claude/memory/sessions/<slug>/_inbox.md` for any global items (new plugin ideas or undirected notes). If it has content, show it separately:

```
Global inbox (<N> item(s)) — new plugin ideas or undirected notes
  [date] from <source-slug> / <session-name>
    - <item>
```

Global inbox items are never auto-cleared — they stay until the user decides to act on them (create a new plugin) or explicitly discards them.

### 6. Establish Session Identity

| Type | name | teams_chat |
|------|------|------------|
| plugin | plugin name (e.g. `office`) | `<Name> - Claude Plugin` |
| story | story key (e.g. `BPT2-1234`) | `BPT2-XXXX — <title>` (from Jira) |
| cab | CAB number (e.g. `CAB-456`) | `CAB-XXX — <description>` (from Jira) |
| personal | name the user provides | `none` |
| general | name the user provides | `<Name> - Claude <Category>` |

For **general**, also ask for a category if not obvious: Research / Prototype / Training / Other.

For **personal**, no category prompt — and Teams chat is always `none` (no lookup or creation).

### 7. Teams Chat Setup

Look in `C:\Users\ajudd\.claude\plugins\marketplaces\ajudd-claude-plugins\office\skills\office\references\known-chats.md` for a chat whose Name or Topic matches the expected `teams_chat` value and has `Active=yes`.

Match on the Name column (exact, case-insensitive) first; fall back to substring match on Topic if no Name match.

- **Found:** "Using Teams chat: [name]" — proceed, or offer to repoint if the user wants a different one
- **Not found:** "No chat found for `[teams_chat]`. Create it? (Yes / Skip / Use a different chat)"
  - **Yes:** create the chat via yl-msoffice MCP, add the entry to `known-chats.md`
  - **Skip:** set `teams_chat` to `none` — Teams steps in checkpoint will be skipped
  - **Different:** ask which existing chat to use, store that name instead

### 8. Write Session State

Create `~/.claude/memory/sessions/<slug>/` if it does not exist.

Write `~/.claude/memory/sessions/<slug>/<name>.md`:

```
---
updated: [today's date]
---

# Session State — <name>

- **Type:** [type]
- **Name:** [name]
- **Title:** [Jira summary]   ← story/cab only — from getJiraIssue; omit for other types
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Project:** [project path]
- **Scope:** [scope path]   ← story/cab/personal: pwd; plugin: ~/.claude/plugins/marketplaces/ajudd-claude-plugins/<name>; omit for general
- **Branch:** [branch or "n/a"]
- **Last worked on:** [will be updated at checkpoint]
- **Open items:** [carried from previous session, or "none"]
- **Next step:** [will be updated at checkpoint]
- **Plugin reviewed:** [yes / no]   ← plugin type only, omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
```

For story and cab types, populate **Title** from the `summary` field of `getJiraIssue`. When resuming an existing session, preserve the existing Title if present. If the session file predates this field (no Title line), fetch from Jira during Step 9 routing and add it.

Write `~/.claude/memory/sessions/<slug>/_active` (plain text, just the name — no `.md` extension):
```
BPT2-1234
```

### 9. Route Based on Choice

**Plugin — existing plugin:**
1. Read `plugin.json`, all command `.md` files, and `SKILL.md` if present
2. Check the session file for `plugin_reviewed: yes`. If missing or `no`, show:
   > "⚠ This plugin has not been reviewed with plugin-dev tools yet. Run the code-reviewer agent against it when you get a chance."
   Continue regardless — this is a reminder, not a blocker.
3. Ask what needs to change if not already stated
4. Confirm approach before making changes

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
- Route to `/release:create-cab`

**CAB — resume:**
1. Read the CAB card from Jira
2. Check release branch status

**Personal — resume:**
1. Check git branch — confirm it matches the session file, offer to switch if not
2. Summarize: what's done, what's open, what's next

**Personal — new:**
1. Ask for the project name
2. Check current git branch, record it in the session file
3. Understand the task, confirm approach, proceed

**General:**
1. Ensure `~/.claude/memory/sessions/<slug>/<name>/` exists (create if not)
2. Load any prior notes from that folder
3. Understand the task, confirm approach, proceed
