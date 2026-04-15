---
name: teams-send
description: Format the current conversation context as a Teams message and send it to a named chat
argument-hint: "[chat-name]"
---

# /office:teams-send [chat-name]

Send a formatted Teams message based on the current conversation context.

## Steps

1. **Identify the target chat** from the argument (e.g. `notes-migration`). Look up the chat ID in `references/known-chats.md`. If the name is not found, ask the user which chat to send to.

2. **Determine the message content** from the current conversation context — what was just discussed, decided, or summarized. If the user gave explicit instructions about what to include, follow them. Otherwise use your judgment about what is relevant to share.

3. **Compose the message** following all rules in `references/teams-html-guide.md`:
   - Intro `<p>` paragraph
   - `<hr/>` between every section
   - `<p><b>Section Title</b></p>` for section labels — never bare `<b>` or `<h3>`
   - `<ul>`/`<li>` for bullets, nested `<ul>` for hierarchy

4. **Enforce signature** — before showing any preview, verify the composed HTML ends with:
   `<p><em>Posted by Claude on behalf of Aaron Judd</em></p>`
   If it is missing or malformed, add it now. Do not proceed to preview until it is present.

5. **Show a preview** of the full message in readable form. Ask the user: "Ready to send, or would you like any changes?"

6. **Wait for explicit approval** before calling `send_chat_message`.

7. **Send and confirm** — call `send_chat_message`, then call `confirm_action` with the returned `actionId`.
