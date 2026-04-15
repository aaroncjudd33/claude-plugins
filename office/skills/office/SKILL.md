---
name: office
description: This skill should be used when the user wants to send a Teams chat message, post an update to a Teams chat, compose or send an email, run an inbox sweep, schedule a meeting, or perform any Microsoft 365 communication via the yl-msoffice MCP. Trigger phrases include: "send a Teams message", "message the team", "post to the chat", "send an email to", "draft an email", "email sweep", "clean the inbox", "schedule a meeting", "create a meeting invite", "notify Heber", "let the team know via Teams".
---

# Office Communications Skill

Governs all Microsoft 365 communication via the `yl-msoffice` MCP — Teams messages, email triage, and meeting invites.

---

## Teams Messaging

### Non-Negotiable Rules

These apply to every Teams message, no exceptions:

1. **ALWAYS end every message with the Claude signature.** No exceptions — single-line messages, tables, reference docs, all of it:
   `<p><em>Posted by Claude on behalf of Aaron Judd</em></p>`
2. **Always preview before sending.** Show the full message content to the user and wait for explicit approval before calling `send_chat_message`. Never auto-confirm.
3. **Always use HTML formatting.** The `yl-msoffice` `send_chat_message` body supports HTML and renders it properly.
4. **Always open with an intro paragraph.** Before the first section, include a `<p>` that sets context — who this is for and why you're sending it.
5. **Follow the HTML guide.** See `references/teams-html-guide.md` for what renders well vs. poorly. The short version: no `<pre>`, no `<code>`, no `<h3>`, no `<th>`. Use `<b>` for labels, `<ul>` for structure, nested `<ul>` for hierarchical content.

### Standard Message Template

```html
<p><b>Message Title</b></p>
<hr/>
<p>Intro — context, who this is for, why you're sending it.</p>
<hr/>
<p><b>Section One</b></p>
<ul>
  <li><b>Item</b> — detail</li>
  <li><b>Item</b> — detail</li>
</ul>
<hr/>
<p><b>Section Two</b></p>
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

Only use for genuinely tabular data with 2–3 columns. See `references/teams-html-guide.md` for full table rules. Quick reference:

```html
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
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

### Sending a Message

Use the `yl-msoffice` MCP tools in this order:

1. **Find the chat ID** — look up the chat name in `references/known-chats.md` (filter to `Active=yes`). If not found there, call `list_chats` to check whether it already exists in Teams before creating a new one. If it truly does not exist, use `teams.create_chat`, then add the new chat ID to `known-chats.md`.
2. **Compose the message** using the template above.
3. **Show the full preview** to the user in plain readable text (not raw HTML).
4. **Wait for explicit approval** — the user must say yes (or request edits) before proceeding. This approval authorizes calling `send_chat_message` in the next step.
5. **Call `send_chat_message`** — this queues the message and returns a pending `actionId`. The message has NOT been sent yet.
6. **Call `confirm_action`** with the returned `actionId`. This is a required API execution step — it is not a second human approval prompt. Do not skip it.

### Creating a New Chat

When creating a new group chat:
1. Use `teams.create_chat` with member emails and a topic. Do not include your own email — the authenticated user is added automatically.
2. Save the returned chat ID to `references/known-chats.md` with `Active=yes`.
3. Confirm the chat was created before sending the first message.

---

## Email Triage

The email commands (`email-grab`, `email-apply-rules`, `email-sweep`) work as a pipeline. Key behavioral rules:

- **Cache contract.** All email commands read from / write to `C:\temp\email-cache.json`. This file must be fresh before running triage. If it is absent or stale, instruct the user to run `/office:email-grab` first.
- **Always show the plan before executing.** Phase 1 of `email-apply-rules` produces a move/mark-read plan. Display it and wait for confirmation before launching the Haiku sub-agent for batch execution.
- **Delegate batch moves to Haiku.** `mail.move` and `mail.mark_read` responses return full message objects (5K–15K tokens each). Batch these calls in a Haiku sub-agent to keep the main context clean.
- **No signature in emails.** The "Posted by Claude on behalf of Aaron Judd" signature is for Teams messages only — do not append it to email bodies.
- **`mail.move` to `deleteditems` for deletes.** There is no `mail.delete` action — use `mail.move` with `folder=deleteditems` for all delete operations.

---

## Meetings

- **Use `create_event`, not `meetings.create`.** `create_event` is the correct tool for scheduling — it creates calendar entries with Teams links automatically.
- **Events with attendees require `confirm_action`.** After calling `create_event`, a pending `actionId` is returned. Call `confirm_action` to execute. Do not skip this step.
- **Resolve attendee IDs first.** Use `search_actions` with category `"people"` to look up user IDs by name or email before creating the event.
- **Always preview before creating.** Show the event title, time, attendees, and description to the user and wait for explicit approval before calling `create_event`.
- **Optionally check availability first.** Use `get_free_busy` before scheduling to avoid conflicts, especially for multi-person or external attendee meetings.

---

## Reference Files

- `references/known-chats.md` — maps friendly chat names to Teams chat IDs (supports Active=yes/no toggle)
- `references/teams-html-guide.md` — full HTML formatting rules for Teams messages
