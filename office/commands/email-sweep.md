---
name: email-sweep
description: Clean the inbox — applies sender routing rules silently, moves matched emails to their folders, routes everything else to Action (unread). Fast, no prompts.
argument-hint: "[limit]"
---

# /office:email-sweep [limit]

Clean the inbox. Pass a `limit` for testing (e.g. `3`). Default is 50.

## Steps

1. Run `/office:email-grab inbox [limit]` — fetches inbox headers into `C:\temp\email-cache.json`
2. Run `/office:email-apply-rules` — classifies, shows plan, executes moves via Haiku, cleans up

## Rules
- Matched sender → correct folder (marked read first)
- No match → Action (left unread)
- No prompts. No rule wizard. Rule management happens when processing Action folder.
