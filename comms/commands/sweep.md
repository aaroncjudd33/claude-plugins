---
name: sweep
description: Clean the inbox — applies sender routing rules silently, then interactive triage for unmatched emails.
argument-hint: "[limit]"
---

# /comms:sweep [limit]

Clean the inbox. Pass a `limit` for testing (e.g. `3`). Default is 50.

## Steps

1. Run `/comms:fetch inbox [limit]` — fetches inbox headers into `C:\temp\email-cache.json`
2. Run `/comms:triage` — classifies, silently processes matched senders, then interactive triage

## Behavior
- **All rule matches** → moved to target folder silently (Haiku sub-agent); marked read except Action items (Action stays unread)
- **Unmatched** → count shown, user picks review mode (all at once or one at a time), interactive triage
- **Triage actions**: skip / archive / action / move/\<folder\> / rule/\<folder\> / read / accept / remove / delete
