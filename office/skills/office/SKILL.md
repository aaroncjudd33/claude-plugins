# Office Communications Skill

Governs all Microsoft 365 messages sent via the `yl-msoffice` MCP tools. Load this skill any time a Teams message, email, or meeting invite is being composed or sent.

---

## Teams Messaging

### Non-Negotiable Rules

These apply to every Teams message, no exceptions:

1. **Always preview before sending.** Show the full message content to the user and wait for explicit approval before calling `confirm_action`. Never auto-confirm.
2. **Always include a signature.** Every message ends with: `<p><em>Posted by Claude on behalf of Aaron Judd</em></p>`
3. **Always use HTML formatting.** The `yl-msoffice` `send_chat_message` body supports HTML and renders it properly.
4. **Always open with an intro paragraph.** Before the first section, include a `<p>` that sets context — who this is for and why you're sending it.
5. **Follow the HTML guide.** See `references/teams-html-guide.md` for what renders well vs. poorly. The short version: no `<pre>`, no `<code>`, no `<h3>`, no `<th>`. Use `<b>` for labels, `<ul>` for structure, nested `<ul>` for hierarchical content.

### Standard Message Template

```html
<b>Message Title</b>
<hr/>
<p>Intro — context, who this is for, why you're sending it.</p>
<hr/>
<b>Section One</b>
<ul>
  <li><b>Item</b> — detail</li>
  <li><b>Item</b> — detail</li>
</ul>
<hr/>
<b>Section Two</b>
<ul>
  <li>Top-level item
    <ul>
      <li>Sub-detail</li>
    </ul>
  </li>
</ul>
<hr/>
<p><em>Posted by Claude on behalf of Aaron Judd</em></p>
```

### Tables

Only use for genuinely tabular data with 2–3 columns. Use `<td>` for ALL cells (never `<th>` — it produces dark bold headers). Bold the first row manually:

```html
<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse;">
  <tr>
    <td><b>Column A</b></td>
    <td><b>Column B</b></td>
  </tr>
  <tr>
    <td>value</td>
    <td>value</td>
  </tr>
</table>
```

For 4+ columns or long text values, use a bullet list with bold labels instead of a table.

### Sending a Message

Use the `yl-msoffice` MCP tools in this order:

1. **Find the chat ID** — look up the chat name in `references/known-chats.md` (filter to `Active=yes`). If not listed, use `teams.create_chat` to create it, then add it to `known-chats.md`.
2. **Compose the message** using the template above.
3. **Show the full preview** to the user in plain readable text (not raw HTML).
4. **Wait for approval** — the user must say yes (or request edits) before proceeding.
5. **Call `send_chat_message`** — this returns a pending `actionId`.
6. **Call `confirm_action`** with that `actionId` only after user approval.

### Creating a New Chat

When creating a new group chat:
1. Use `teams.create_chat` with member emails and a topic. Do not include your own email — the authenticated user is added automatically.
2. Save the returned chat ID to `references/known-chats.md` with `Active=yes`.
3. Confirm the chat was created before sending the first message.

---

## Reference Files

- `references/known-chats.md` — maps friendly chat names to Teams chat IDs (supports Active=yes/no toggle)
- `references/teams-html-guide.md` — full HTML formatting rules for Teams messages
