---
name: comms
description: "Governs all Microsoft 365 communication via the yl-msoffice MCP. Auto-loads when: sending Teams messages, reading a chat, triaging or fetching email, sweeping the inbox, scheduling a calendar event, or running any /comms command (/comms:message, /comms:fetch, /comms:triage, /comms:sweep)."
---

# Comms Skill

Governs all Microsoft 365 communication via the `yl-msoffice` MCP — Teams messages, email triage, and meeting invites.

---

## Teams Messaging

### Non-Negotiable Rules

These apply to every Teams message, no exceptions:

1. **Always preview before sending.** Show the full draft in BOTH formats and wait for explicit approval before calling `send_chat_message`. Never auto-confirm.
2. **Always use HTML formatting.** The `yl-msoffice` `send_chat_message` body supports HTML and renders it properly.
3. **Always open with an intro paragraph.** Before the first section, include a `<p>` that sets context — what this message is about and why you're sending it. Do NOT open with a greeting or self-introduction (see voice guide).
4. **Follow the HTML guide.** See `references/teams-html-guide.md` for what renders well vs. poorly. The short version: no `<pre>`, no `<code>`, no `<h1>`, no `<h3>`, no `<th>`. Use `<h2>` for section headers, `<b>` for labels, `<ul>` for structure, nested `<ul>` for hierarchical content.
5. **Apply Aaron's voice.** Read `references/aaron-voice.md` before drafting. Key rules: no greeting, paragraphs for conversational messages, brief on mistakes, "we/us" not "I", passive availability.
6. **Self-correct on wrong-chat mismatches.** When the user reports that a message went to the wrong chat (e.g. "I meant the CAB chat, not the story chat" or "that's the wrong chat"), immediately: (a) identify what phrase was used and what Name it incorrectly resolved to, (b) add the phrase as an alias on the correct chat's row in `~/.claude/plugins/known-chats.md`, (c) if the phrase is ambiguous (matches multiple chats), also note it in a comment on the wrong chat's row so future sessions avoid the conflict, (d) save a feedback memory documenting the correction. Do not ask permission — do it immediately as part of acknowledging the correction.

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

1. **Find the chat ID** — look up the chat name or phrase in `~/.claude/plugins/known-chats.md` (filter to `Active=yes`). Match priority: (1) exact Name match, (2) any Aliases entry (comma-separated, match each individually), (3) substring Topic match. When the user says something informal ("my team chat", "the group chat", "cab chat"), check Aliases before Topic. If matched via alias, confirm before sending: "Matched '[phrase]' → [Name]. Using that — ok?" If not found, call `list_chats` to check whether it already exists in Teams before creating a new one. If it truly does not exist, use `teams.create_chat`, then add the new chat ID to `~/.claude/plugins/known-chats.md`.
2. **Compose the message** using the template above. Read `references/aaron-voice.md` first.
3. **Show the full preview in both formats:**
   - **Plain text** — readable prose version so the user can verify content and tone
   - **HTML** — the exact markup that will be sent, so layout issues are visible before send
4. **Wait for explicit approval** — the user must say yes (or request edits) before proceeding. This approval authorizes calling `send_chat_message` in the next step.
5. **Call `send_chat_message`** — this queues the message and returns a pending `actionId`. The message has NOT been sent yet.
6. **Call `confirm_action`** with the returned `actionId`. This is a required API execution step — it is not a second human approval prompt. Do not skip it.

### Creating a New Chat

When creating a new group chat:
1. Use `teams.create_chat` with member emails and a topic. Do not include your own email — the authenticated user is added automatically.
2. Save the returned chat ID to `~/.claude/plugins/known-chats.md` with `Active=yes`.
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

The email commands (`fetch`, `triage`, `sweep`) work as a pipeline.

**Three-phase structure (`/comms:triage`):**
1. **Classify** — read cache and sender rules from `project_inbox_triage.md`, build `to_accept` (meeting invites matching accept rules), `to_move` (rule-matched senders), and `unmatched` arrays. No API calls. Show the plan and wait for confirmation.
2. **Silent execute** — Haiku sub-agent processes `to_accept` (accept invite + delete email) and `to_move` (move + mark read). `mail.move` and `mail.mark_read` return full message objects (5K–15K tokens each) — always delegate to Haiku to keep main context clean.
3. **Interactive triage** — for `unmatched` emails, offer Mode 1 (all at once, annotate by number) or Mode 2 (one at a time). Actions: skip / archive / action / move/X / rule/X / read / accept / remove / delete.

**Key behavioral rules:**
- **Cache contract.** All email commands read from / write to `C:\temp\email-cache.json`. If absent or stale, instruct the user to run `/comms:fetch` first.
- **Rule-saving.** When the user creates a `rule/X` during interactive triage, immediately update the `## Sender Rules` table in `project_inbox_triage.md` and auto-resolve any remaining emails from that sender in the current loop.
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

- `~/.claude/plugins/known-chats.md` — maps friendly chat names to Teams chat IDs (global file, Active=yes/no toggle, alias lookup)
- `references/teams-html-guide.md` — full HTML formatting rules for Teams messages
- `references/aaron-voice.md` — Aaron's communication voice and tone — read before drafting any message
