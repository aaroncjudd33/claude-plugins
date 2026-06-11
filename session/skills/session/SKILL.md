---
name: session
description: "This skill governs session lifecycle across all project types. Load whenever the user invokes a session command (/session:start, /session:checkpoint, /session:commit, /session:finish, /session:switch, /session:search, /session:status, /session:spawn, /session:resume, /session:prepare-clear, /session:worklog, /session:migrate), asks about session state, asks what they were working on, wants to save progress, wants to start or end a working session, or asks about their inbox, backlog, or open items. Provides path resolution logic, @handle tagging rules, epic context, context-recovery guidance, and Teams messaging rules used by all session commands."
---

# Session Skill

Governs session lifecycle across all project types (plugin, story, cab, personal, general).

---

## Path Resolution

**All session commands use this logic.** Do not hardcode `~/.claude/memory/sessions/<slug>/` — check for repo-based sessions first.

```
slug = last path component of pwd

repo_root = $(git rev-parse --show-toplevel 2>/dev/null) or pwd if not a git repo

if <repo_root>/.claude/sessions/ exists:
    session_root = <repo_root>/.claude/sessions/
    local_cfg    = ~/.claude/config/<slug>.json
    if local_cfg missing → run First-Run prompt (see below)
    handle = local_cfg.handle
else:
    session_root = ~/.claude/memory/sessions/<slug>/
    handle = user-config.json → user.handle (fallback: prefix of user.email)

Always local (never in repo, regardless of mode):
    _active        → ~/.claude/memory/sessions/<slug>/_active
    _resume_*      → ~/.claude/memory/sessions/<slug>/
```

**Scope resolution for the scope guard:** If the session file's `Scope:` value is relative (no leading `/`, `~`, or drive letter), resolve it as `local_cfg.projectRoot + "/" + scope_value`. If absolute (old format), use as-is.

**Cross-repo inbox writes** (e.g., story plugin writing to release plugin inbox): substitute the target slug and re-run path resolution to find the target session_root.

**Inbox / Outbox file naming:**
- Per-session inbox (any type): `_inbox_<session-name>.md` — e.g., `_inbox_BPT2-6479.md`, `_inbox_release.md`
- Global inbox (no known target session): `_inbox.md`
- Outbox (append-only send record): `_outbox_<session-name>.md`

All cross-session routing goes through `/session:inbox` — scope guards invoke it rather than writing directly.

### First-Run Auto-Config

Triggered once per developer per repo-based project when `~/.claude/config/<slug>.json` is missing. **No prompt needed** — derive everything silently:

```
projectRoot = git rev-parse --show-toplevel   ← always known
handle      = user-config.json → user.handle  ← already in user-config
```

Write `~/.claude/config/<slug>.json`:
```json
{ "projectRoot": "<derived>", "handle": "<derived>" }
```

Then show a one-time notice: `"Repo sessions active for <slug> — local config written to ~/.claude/config/<slug>.json"`

Only ask for `handle` if `user-config.json` is completely absent (plugin not set up at all — uncommon edge case).

---

## @handle Tagging

Every entry written to shared files (history, inbox, backlog) must carry the current user's handle.

**Handle lookup order:**
1. `~/.claude/config/<slug>.json` → `handle` field (repo-based projects)
2. `~/.claude/plugins/user-config.json` → `user.handle`
3. Fallback: prefix of `user.email` (e.g., `ajudd@youngliving.com` → `ajudd`)

**History entry format** (new and going forward):
```
[YYYY-MM-DD @<handle>] <session-name> — <accomplished sentence>
```

**Inbox/backlog entry header format** (new and going forward):
```
## [YYYY-MM-DD @<handle>] from <slug> / <session-name> — <description>
```

**`updated-by` field in session files** — written on every checkpoint/finish/commit/switch:
```
- **updated-by:** @<handle>
```
Position: in the session file body after `Name:`, before `Teams chat:`.

### "Mine" Filter

Any listing command (start, switch, status, search) supports filtering sessions to those where `updated-by` matches `@<handle>`.

- Argument `mine` → filter immediately (e.g., `/session:start mine`)
- Without argument → show all sessions; if multiple developers' sessions are visible, add hint: "(type `mine` to filter to yours)"
- In filtered mode, show label: `(filtered to @<handle>)`

---

## Epic Context — Cross-Story Research

When the active session has an `Epic` field, the epic file (`~/.claude/memory/epics/<key>.md`) is the canonical source for anything that crosses story boundaries: architecture decisions, blockers, open questions, and the story map.

**Check the epic file first** before investigating code or asking Jira when the question is architectural — decisions are already recorded there and re-investigating wastes time.

**Sibling story lookup:** When researching something that a sibling story may have already answered (data formats, API contracts, cross-repo contracts, design decisions), check the sibling's session file:
1. Open the epic file — find the story in the Stories table
2. Derive the repo slug from the story key or the Scope field in the sibling's session file
3. Read `~/.claude/memory/sessions/<repo-slug>/<story-key>.md`

Example: working on BPT2-6382 (frontend) and need the wire format for `periodId` — check BPT2-6379's session file (`~/.claude/memory/sessions/virtual-office/BPT2-6379.md`) before digging through code or calling Jira.

**When to use sibling sessions proactively:**
- Any question about data shapes, API contracts, or field formats that another story's SPIKE or backend work would have answered
- Cross-repo coordination ("what's the other side expecting?")
- When a blocker or open question in the epic points to a sibling story as owner

**Explicit "look across the epic":** If the user says "check what other stories found" or "look across the epic for X", read *all* sibling session files listed in the epic's Stories table and surface their open items, next steps, and relevant notes.

---

## Context Recovery After /clear

If the user asks "what was I working on", "did I work on BPT2-XXXX before", "find my session for X", or similar recall questions, suggest **`/session:search <query>`** — it searches session files and worklogs by story key or keyword without requiring an active session. For date-based review ("what did I do yesterday"), suggest **`/session:worklog`**.

If the user runs `/clear` or mentions that context was lost, **immediately suggest running `/session:resume`** (fastest post-`/clear` path — skips the menu and restores context directly) or **`/session:start`** for the full flow:

> "Context cleared — run `/session:resume` to restore context directly, or `/session:start` to pick up from the full session menu."

This is the primary recovery path. `/session:start` reads `_active` to identify the current session, then loads the session file and surfaces everything needed to resume. New developers especially should be nudged here — the workflow is not obvious without it.

---

## Planning Mode Enforcement

When `Mode: planning` is active in the session file, enforce read-only behavior: no code edits or file writes outside `~/.claude/memory/`. Implementation requests are routed to the session inbox instead. This is enforced via the global CLAUDE.md session check — the Mode field drives it.

---

## Reference Files

- `references/inbox-convention.md` — How to write cross-session/cross-project change instructions to plugin inbox files
- `references/epic-template.md` — Template structure for creating new epic memory files at `~/.claude/memory/epics/<key>.md`

---

## Teams Messaging

Whenever any session command posts a Teams message, apply these rules without exception:

1. **Always end with the Claude signature** — no exceptions:
   `<p><em>Posted by Claude Code on behalf of {USER_NAME}</em></p>` — use the display name from `user-config.json → user.name`, or fall back to `@<handle>`
2. **Always preview before sending.** Show the full message content and wait for explicit approval before calling `send_chat_message`.
3. **Always use HTML formatting.** `send_chat_message` body supports and renders HTML.
4. **Always open with an intro paragraph** (`<p>`) before the first section.
5. **Follow the HTML guide.** Read `~/.claude/plugins/marketplaces/<pluginMarketplaceName>/comms/skills/comms/references/teams-html-guide.md` (derive `pluginMarketplaceName` from `~/.claude/plugins/user-config.json`) before drafting any message.

Standard message template:

```html
<h2>Message Title</h2>
<p>&nbsp;</p>
<p>Intro — context, who this is for, why you're sending it.</p>
<p>&nbsp;</p>
<h2>Section One</h2>
<ul>
  <li><b>Item</b> — detail</li>
</ul>
<p>&nbsp;</p>
<p><em>Posted by Claude Code on behalf of {USER_NAME}</em></p>
```
