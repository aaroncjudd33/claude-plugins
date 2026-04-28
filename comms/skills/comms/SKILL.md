---
name: comms
description: "Background skill — do not run directly. Use /comms:message, /comms:sweep, or /comms:triage. Auto-loads when: sending Teams messages, managing email, or any Microsoft 365 communication."
---

# Comms Skill

Governs all Microsoft 365 communication via the `yl-msoffice` MCP — Teams messages, email triage, and meeting invites.

---

## Teams Messaging

### Non-Negotiable Rules

These apply to every Teams message, no exceptions:

1. **ALWAYS end every message with the Claude signature.** No exceptions — single-line messages, tables, reference docs, all of it:
   `<p><em>Posted by Claude on behalf of {USER_NAME}</em></p>`
2. **Always preview before sending.** Show the full message content to the user and wait for explicit approval before calling `send_chat_message`. Never auto-confirm.
3. **Always use HTML formatting.** The `yl-msoffice` `send_chat_message` body supports HTML and renders it properly.
4. **Always open with an intro paragraph.** Before the first section, include a `<p>` that sets context — who this is for and why you're sending it.
5. **Follow the HTML guide.** See `references/teams-html-guide.md` for what renders well vs. poorly. The short version: no `<pre>`, no `<code>`, no `<h1>`, no `<h3>`, no `<th>`. Use `<h2>` for section headers, `<b>` for labels, `<ul>` for structure, nested `<ul>` for hierarchical content.

### Standard Message Template

```html
<h2>Message Title</h2>
<p>&nbsp;</p>
<p>Intro — context, who this is for, why you're sending it.</p>
<p>&nbsp;</p>
<h2>Section One</h2>
<ul>
  <li><b>Item</b> — detail</li>
  <li><b>Item</b> — detail</li>
</ul>
<p>&nbsp;</p>
<h2>Section Two</h2>
<ul>
  <li>Top-level item
    <ul>
      <li>Sub-detail</li>
    </ul>
  </li>
</ul>
<p>&nbsp;</p>
<p><em>Posted by Claude on behalf of {USER_NAME}</em></p>
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

1. **Find the chat ID** — look up the chat name in `references/known-chats.md` (filter to `Active=yes`). If not found there, call `list_chats` to check whether it already exists in Teams before creating a new one. If it truly does not exist, use `teams.create_chat`, then add the new chat ID to `~/.claude/plugins/known-chats.md`.
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

## Reading Chat Messages — Image and Video Processing

Whenever `list_chat_messages` runs, automatically scan each message body for media content and process it inline. Do not wait to be asked.

### Images

Parse `<img src="...">` tags from the HTML message body. For each one found:

1. **Check for duplicates.** If there is an active session file, read its `## Teams Images Processed` section. If the message ID is already listed, skip it silently.
2. **Download.** Use PowerShell `Invoke-WebRequest` to save the file to `C:\temp\claude-uploads\`:
   ```
   {sender-slug}_{message-id}_{alt-text-slug}.{ext}
   ```
   Derive `sender-slug` from the `from` field (lowercase, spaces to hyphens). Derive `alt-text-slug` from the `<img alt="...">` value (first 3–4 words, lowercase, hyphens). Use the URL file extension (`.gif`, `.jpg`, `.png`).
3. **Display.** Read the downloaded file immediately so the image renders inline in the response.
4. **Archive.** Move the file to the archive folder using the existing screenshot archiving strategy — derive the project folder from the current working directory or active session context.
5. **Record in session file.** If an active session file exists, append to a `## Teams Images Processed` section:
   ```
   - {message_id}: {filename} — {YYYY-MM-DD}
   ```
   Create the section if it does not exist. This prevents re-processing the same image in the same session.

If there is no active session, skip deduplication — process all images found, download, display, and archive.

### Videos

Videos cannot be processed — Claude cannot analyze video content or extract meaningful information from video files. When a message contains a video indicator — a `.mp4` URL, an `<attachment>` tag referencing a video file, or any media clearly labeled as video — note it inline and skip:

```
{sender} shared a video at {HH:MM} — not processed.
```

Do not attempt to download or display video content. This is a permanent limitation, not a future enhancement.

### Inline images vs. file uploads

- **`<img src="...">` with a public URL** (Giphy, CDN links): download directly, no auth needed.
- **`<attachment id="...">` references**: these are either quoted messages or uploaded files. Quoted message attachments can be ignored. Uploaded file attachments (images someone photographed and shared) require Graph API hosted content access — skip with a note: "{sender} shared an uploaded image at {HH:MM} — hosted content, not processed."

### Context relevance in high-volume group chats

In active group chats with multiple people and banter (story chats, cross-team discussions), images are often unrelated to the work at hand — fun GIFs, reaction memes, off-topic content. **Always download and archive every image found** — the goal is complete capture. However, apply judgment when surfacing images in context:

- If an image is clearly a reaction GIF or meme (Giphy alt text, animated GIF from a fun exchange), note it briefly: "Heber shared a meme at {HH:MM} — archived."
- If an image appears to contain work-relevant content (a screenshot, a diagram, a log dump, an error message), display it prominently and call out what it shows.
- If you are genuinely unsure whether an image is work-related, ask before drawing conclusions from it: "This image from {sender} at {HH:MM} — is this relevant to what we're looking at?"

The rule: capture everything, but don't let non-work images crowd out or be mistaken for work context.

---

## Email Triage

The email commands (`fetch`, `triage`, `sweep`) work as a pipeline. Key behavioral rules:

- **Cache contract.** All email commands read from / write to `C:\temp\email-cache.json`. This file must be fresh before running triage. If it is absent or stale, instruct the user to run `/comms:fetch` first.
- **Always show the plan before executing.** Phase 1 of `triage` produces a move/mark-read plan. Display it and wait for confirmation before launching the Haiku sub-agent for batch execution.
- **Delegate batch moves to Haiku.** `mail.move` and `mail.mark_read` responses return full message objects (5K–15K tokens each). Batch these calls in a Haiku sub-agent to keep the main context clean.
- **No signature in emails.** The "Posted by Claude on behalf of {USER_NAME}" signature is for Teams messages only — do not append it to email bodies.
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
