---
name: message
description: Format the current conversation context as a Teams message and send it to a named chat
argument-hint: "[chat-name]"
---

# /comms:message [chat-name]

Send a formatted Teams message based on the current conversation context.

## Steps

1. **Identify the target chat** from the argument (e.g. `notes-migration`). Look up the chat ID in `~/.claude/plugins/known-chats.md` (filter to `Active=yes`). Match priority: (1) exact Name, (2) any Aliases entry, (3) substring Topic match. If not found, ask the user which chat to send to.

2. **Determine the message content** from the current conversation context — what was just discussed, decided, or summarized. If the user gave explicit instructions about what to include, follow them. Otherwise use your judgment about what is relevant to share.

3. **Compose the message** following all rules in `references/teams-html-guide.md`:
   - Intro `<p>` paragraph
   - `<h2>` for section headers; `<p>&nbsp;</p>` between every section — never `<hr/>`
   - `<p><b>Label</b></p>` for minor labels within a section — never bare `<b>` or `<h3>`
   - `<ul>`/`<li>` for bullets, nested `<ul>` for hierarchy

4. **Show a preview in both formats:**
   - **Plain text** — readable prose so the user can verify content and tone
   - **HTML** — the exact markup that will be sent, so layout issues are visible before send
   Ask the user: "Ready to send, or would you like any changes?"

5. **Wait for explicit approval** before calling `send_chat_message`.

6. **Send and confirm** — call `send_chat_message`, then call `confirm_action` with the returned `actionId`.
