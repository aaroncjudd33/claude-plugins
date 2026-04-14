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

<br>

<h3>SECTION TITLE</h3>
<p>or list/table directly on next line — no <br> between h3 and its content</p>

<br>

<h3>ANOTHER SECTION</h3>
<ul>
  <li>Bullet point</li>
</ul>

<br>

<p><em>Posted by Claude on behalf of Aaron Judd</em></p>
```

Teams strips CSS `margin` and `padding` from inline styles — they have no effect. Use `<br>` tags between elements to create vertical spacing. Put a `<br>` after `</h3>` and after `</table>` before the signature.

### Tables

Use this pattern for all structured data (estimates, breakdowns, comparisons). Always include borders, cell padding, and a styled header row:

```html
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
  <tr style="background-color: #464775; color: #ffffff;">
    <th style="text-align: left; font-weight: normal;">Column A</th>
    <th style="text-align: left; font-weight: normal;">Column B</th>
  </tr>
  <tr>
    <td>Row 1 value</td>
    <td>Row 1 value</td>
  </tr>
  <tr>
    <td>Row 2 value</td>
    <td>Row 2 value</td>
  </tr>
</table>
```

Use `#464775` (Teams indigo) with `color: #ffffff` on the header row — this reads clearly in both light and dark Teams themes. Do NOT use light grays (`#e8e8e8`, `#f5f5f5`) for header backgrounds — they invert badly in dark mode. No alternating row shading.

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
