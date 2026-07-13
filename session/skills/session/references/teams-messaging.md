# Teams Messaging

Rules for any session command that posts a Teams message. Loaded on demand (the SKILL keeps a one-line pointer at § Teams Messaging).

Whenever any session command posts a Teams message (the `session:commit` chat draft, the `session:finish` closing update, or any other), apply these rules without exception — they mirror the comms plugin's **two Teams gates** (read-before-post + show-draft-before-send):

1. **Show the draft, get approval, then send — every message.** Show the full message content and wait for the user's explicit approval *for that specific message* before calling `send_chat_message`. Approval is per-message and never inferred: a general "go ahead" given earlier, or approval of a previous message, does NOT authorize sending the next one without showing it first. Never auto-confirm. (This is gate 2 of the comms two-gates rule — see `comms/skills/comms/SKILL.md`. Gate 1: read the recent chat with `list_chat_messages` before drafting, so you never duplicate what's already posted.)
2. **Always use HTML formatting.** `send_chat_message` body supports and renders HTML.
3. **Always open with an intro paragraph** (`<p>`) before the first section.
4. **Follow the HTML guide.** Read `~/.claude/plugins/marketplaces/<pluginMarketplaceName>/comms/skills/comms/references/teams-html-guide.md` (derive `pluginMarketplaceName` from `~/.claude/plugins/user-config.json`) before drafting any message.

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
```
