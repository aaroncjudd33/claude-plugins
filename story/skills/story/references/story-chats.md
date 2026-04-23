# Finding Story Teams Chats

When looking for a Teams chat associated with a Jira story, always scan `list_chats` results for the 4-digit story number (e.g., "6337" for BPT2-6337). The chat topic will contain the number even if the session file says `teams_chat: none` or the entry is missing from `known-chats.md`.

**Why:** Story chats are created in various Claude Code sessions and may not be registered in `known-chats.md` or the session file yet. The chat topic always contains the story number, so a string scan finds it reliably.

**How to apply:** Before concluding a story chat doesn't exist, always call `list_chats` and scan all topics for the 4-digit story number. Only after confirming it's truly absent should you offer to create one.
