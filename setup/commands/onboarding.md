---
name: onboarding
description: First-run setup — auto-detects your name, email, Jira ID, and Teams ID, then writes ~/.claude/plugins/user-config.json. Run this before using any other plugin commands.
---

# Setup: Onboarding

Configure your identity for use across all plugins. Auto-detects values where possible — you only need to correct or fill in what couldn't be found.

## Instructions

### 1. Check for existing config

Read `~/.claude/plugins/user-config.json`.

If it exists and has a non-empty `user.jiraAccountId`, display current values:

```
Existing config found:
  Name:          <user.name>
  Email:         <user.email>
  Jira ID:       <user.jiraAccountId>
  Teams ID:      <user.teamsUserId or "(not set)">
  Jira Project:  <defaults.jiraProject>
  Chat members:  <defaults.storyChatMembers joined by ", " or "(none)">
```

Ask: "Update this config? (y/n)" — if no, stop.

### 2. Auto-detect identity from git config

Run both commands:

```bash
git config user.name
git config user.email
```

Use whatever is returned. If a command fails or returns empty, that field stays blank and will be asked manually in step 3.

### 3. Auto-lookup Jira and Teams IDs

If an email was detected in step 2, attempt both lookups in parallel — do not wait for user input first.

**Jira account ID:**
Call `lookupJiraAccountId` with `cloudId: "9de6eb2b-2683-44e6-89ff-c622027e09b4"` and `query: <email>`.
- On success: extract `accountId` from the first result. Note it as "(looked up from Atlassian)".
- On transient error (proxy/network): retry once automatically before giving up.
- On failure after retry or no results: note as "(not found — will ask manually)".

**Teams user ID:**
Call `get_my_profile` — this returns the current authenticated user's Microsoft 365 profile directly.
- On success: extract the user `id` field. Note it as "(looked up from Microsoft 365)".
- On failure: note as "(not found — will ask manually)".
- Do NOT use `search_actions` for this — it is unreliable for user ID lookup.

### 4. Show confirm/correct screen

Display all detected values — whether auto-found or still blank:

```
Here's what I found:

  Name:     Aaron Judd              (from git config)
  Email:    ajudd@youngliving.com   (from git config)
  Jira ID:  620147d91fec260068...   (looked up from Atlassian)
  Teams ID: 4a1b2c3d-...            (looked up from Microsoft 365)

  Jira Project:  BPT2               (default)
  Chat members:  (none)             (default)
```

For any field that is blank or wrong, the user can correct it now.

Ask: "Does everything look right? Enter a field name to change it, or press Enter to continue."

- If they type a field name (e.g. "name", "email", "jira", "teams", "project", "members"): prompt for that field, then re-display the screen.
- If they press Enter: proceed to step 5.

For blank fields that were not auto-detected, prompt for them explicitly before allowing the user to proceed:
- **Name**: "Your full display name (e.g. 'Jane Smith'):"
- **Email**: "Your work email (e.g. 'jsmith@example.com'):"
- **Jira ID**: "Your Jira account ID — or type 'lookup' to search by email:"
  - If "lookup": call `lookupJiraAccountId` and show results for selection.
  - If pasted directly: use as-is.
- **Teams ID**: "Your Microsoft 365 user ID — or type 'lookup' to retry, or Enter to skip:"
  - If "lookup": call `get_my_profile` and extract the `id` field.
  - If skipped: leave as empty string (can be set later).

**Jira project key**: default is `BPT2`. Only ask if the user explicitly wants to change it.

**Default story chat members**: emails of teammates to auto-add to new story chats. Default is none. Only ask if the user explicitly wants to set them.

### 5. Confirm and write

Display a final summary:

```
About to write ~/.claude/plugins/user-config.json:

  name:             <value>
  email:            <value>
  jiraAccountId:    <value>
  teamsUserId:      <value or "(not set)">
  jiraProject:      <value>
  storyChatMembers: [<list or empty>]
```

Ask: "Write this config? (y/n)"

If yes, write the file:

```json
{
  "user": {
    "name": "<name>",
    "email": "<email>",
    "jiraAccountId": "<jiraAccountId>",
    "teamsUserId": "<teamsUserId or empty string>"
  },
  "defaults": {
    "storyChatMembers": [],
    "jiraProject": "<jiraProject>",
    "atlassianCloudId": "9de6eb2b-2683-44e6-89ff-c622027e09b4",
    "jiraProjectId": "12844"
  },
  "paths": {
    "browserLinksFile": "~/.claude/browser-links.json",
    "memoryRoot": "~/.claude"
  }
}
```

`storyChatMembers` is an array of email strings (empty array if none provided).

Confirm: "Config written. You're ready to use the plugins. Run /setup:local to start your day."

If no: "Config not saved." and stop.

## Error Handling

- If `git config` is unavailable (git not installed): skip silently, proceed to manual prompts.
- If Atlassian MCP is unavailable: skip Jira lookup, prompt manually.
- If yl-msoffice MCP is unavailable: skip Teams lookup, note Teams ID can be set later.
- Never block onboarding due to a lookup failure — always offer manual entry as a fallback.
