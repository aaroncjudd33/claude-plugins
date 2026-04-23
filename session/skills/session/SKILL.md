---
name: session
description: "Background skill — do not run directly. Use /session:start, /session:checkpoint, or /session:finish. Auto-loads when: any session command is invoked or session state is relevant."
---

# Session Skill

Governs session lifecycle across all project types (plugin, story, cab, personal, general).

---

## Reference Files

- `references/inbox-convention.md` — How to write cross-session/cross-project change instructions to plugin inbox files

---

## Teams Messaging

Whenever any session command posts a Teams message, apply these rules without exception:

1. **Always end with the Claude signature** — no exceptions:
   `<p><em>Posted by Claude on behalf of {USER_NAME}</em></p>`
2. **Always preview before sending.** Show the full message content and wait for explicit approval before calling `send_chat_message`.
3. **Always use HTML formatting.** `send_chat_message` body supports and renders HTML.
4. **Always open with an intro paragraph** (`<p>`) before the first section.
5. **Follow the HTML guide.** Read `~/.claude/plugins/marketplaces/ajudd-claude-plugins/comms/skills/comms/references/teams-html-guide.md` before drafting any message.

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
<p><em>Posted by Claude on behalf of {USER_NAME}</em></p>
```
