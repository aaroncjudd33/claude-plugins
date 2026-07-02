# comms

Microsoft 365 communications for Claude Code — Teams messaging, email triage, and inbox sweep — layered over the `yl-msoffice` MCP server.

## Prerequisites

comms does not talk to Microsoft 365 directly; it drives the **`yl-msoffice` MCP server**, which is a **separate plugin from a different marketplace**. Installing comms will not bring it. On any machine:

| Requirement | How to get it | Why |
|-------------|---------------|-----|
| Identity config | `/setup:onboarding` → `~/.claude/plugins/user-config.json` | Chat lookups, voice, and defaults read it |
| yl-msoffice MCP | install/enable `yl-msoffice@youngliving-claude-plugins` | Provides `send_chat_message`, `list_chats`, `send_email`, `create_event`, etc. |

If either is missing, the comms skill will detect it at the first action and point you at the fix rather than failing silently. **No comms behavior depends on `~/.claude/memory/*`** — memory is personal and non-portable, so it never gates how the plugin works.

## Commands

- `/comms:message` — format the current context as a Teams message and send it to a named chat
- `/comms:fetch` — fetch email headers to `C:\temp\email-cache.json`
- `/comms:triage` — classify cached emails, auto-process rule-matched senders, interactively triage the rest
- `/comms:sweep` — clean the inbox: apply routing rules, then interactive triage
- `/comms:pto` — send an all-day OOF calendar invite

## Teams HTML enforcement

A `PreToolUse` hook (`hooks/hooks.json` → `hooks/scripts/teams-html-lint.py`) blocks any Teams **write** whose HTML violates `skills/comms/references/teams-html-guide.md` (no `<pre>`/`<code>`/`<h1>`/`<h3>`/`<hr>`/`<th>`; require `<p>&nbsp;</p>` spacers on 3+ paragraphs).

It **ships with the plugin** — enabled automatically when comms is enabled, no `~/.claude/settings.json` edit on any machine — and **matches on the tool-name suffix**, so a future MCP namespace rename can't silently disable it. It lints writes only (`send_chat_message`, teams/channel `execute_action`); email and all read tools are untouched.

The HTML guide is the single source of truth for the lint rules — keep the two in sync.
