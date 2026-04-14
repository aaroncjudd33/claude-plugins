# Office Communications Skill

Governs all Microsoft 365 messages sent via the `yl-msoffice` MCP tools. Load this skill any time a Teams message, email, or meeting invite is being composed or sent.

---

## Teams Messaging

### Non-Negotiable Rules

These apply to every Teams message, no exceptions:

1. **Always preview before sending.** Show the full message content to the user and wait for explicit approval before calling `confirm_action`. Never auto-confirm.
2. **Always include a signature.** Every message ends with: `<p><em>Posted by Claude on behalf of Aaron Judd</em></p>`
3. **Always use HTML formatting.** The `yl-msoffice` `send_chat_message` body supports HTML and renders it properly. Never send plain text for multi-section messages.
4. **Always open with an intro paragraph.** Before the first section header, include a `<p>` that sets context — who this is for and why you're sending it.

### HTML Message Template

```html
<p>[Intro — who this is for and why you're sending it]</p>

<h3>SECTION TITLE</h3>
<p>or <ul> content here</p>

<h3>ANOTHER SECTION</h3>
<ul>
  <li>Bullet point</li>
</ul>

<p><em>Posted by Claude on behalf of Aaron Judd</em></p>
```

Do NOT put `<br>` after `</h3>` — Teams already gives `<h3>` enough bottom margin.

### Tables

Use this pattern for all structured data (estimates, breakdowns, comparisons). Always include borders, cell padding, and a styled header row:

```html
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
  <tr style="background-color: #e8e8e8;">
    <th style="text-align: left;">Column A</th>
    <th style="text-align: left;">Column B</th>
  </tr>
  <tr>
    <td>Row 1 value</td>
    <td>Row 1 value</td>
  </tr>
  <tr style="background-color: #f5f5f5;">
    <td>Row 2 value (alternating shade)</td>
    <td>Row 2 value</td>
  </tr>
</table>
```

Alternate row background colors (`#f5f5f5` / none) for readability on longer tables.

### Sending a Message

Use the `yl-msoffice` MCP tools in this order:

1. **Find the chat ID** — look up the chat name in `references/known-chats.md`. If not listed, use `list_chats` or `teams.create_chat` to find or create it, then add it to `known-chats.md`.
2. **Compose the message** using the HTML template above.
3. **Show the full preview** to the user in plain readable text (not raw HTML).
4. **Wait for approval** — the user must say yes (or request edits) before proceeding.
5. **Call `send_chat_message`** — this returns a pending `actionId`.
6. **Call `confirm_action`** with that `actionId` only after user approval.

### Creating a New Chat

When creating a new group chat:
1. Use `teams.create_chat` with member emails and a topic.
2. Save the returned chat ID to `references/known-chats.md` under a friendly name.
3. Confirm the chat was created before sending the first message.

---

## Reference Files

- `references/known-chats.md` — maps friendly chat names to Teams chat IDs
