---
name: email-sweep
description: Clean the inbox — applies sender routing rules silently, then interactive triage for unmatched emails.
argument-hint: "[limit]"
---

# /office:email-sweep [limit]

Clean the inbox. Pass a `limit` for testing (e.g. `3`). Default is 50.

## Steps

1. Run `/office:email-grab inbox [limit]` — fetches inbox headers into `C:\temp\email-cache.json`
2. Run `/office:email-apply-rules` — classifies, silently processes matched senders, then interactive triage

## Behavior
- **Non-Archive rule matches** → marked read + moved to target folder (silent, Haiku sub-agent)
- **Archive-mapped senders** → marked read only, stay in inbox (user moves to Archive manually — avoids move token cost)
- **Unmatched** → count shown, user picks review mode (all at once or one at a time), interactive triage
- **Triage actions**: skip / archive / action / move/\<folder\> / rule/\<folder\> / read / accept / remove / delete
