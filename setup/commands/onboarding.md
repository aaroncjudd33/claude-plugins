---
name: onboarding
description: First-run setup — collect your name, email, Jira account ID, and Teams user ID, then write ~/.claude/plugins/user-config.json. Run this before using any other plugin commands.
---

# Setup: Onboarding

Configure your identity for use across all plugins. Writes `~/.claude/plugins/user-config.json` with your personal details so commands no longer rely on hardcoded values.

## Instructions

### 1. Check for existing config

Read `~/.claude/plugins/user-config.json`. If it exists and has a non-empty `user.jiraAccountId`, display the current values:

```
Current config:
  Name:          <user.name>
  Email:         <user.email>
  Jira ID:       <user.jiraAccountId>
  Teams ID:      <user.teamsUserId or "(not set)">
  Jira Project:  <defaults.jiraProject>
  Chat members:  <defaults.storyChatMembers joined by ", " or "(none)">
```

Ask: "Update this config? (y/n)" — if no, stop.

### 2. Collect identity

Ask for each value in sequence. If a current config exists, show the current value as the default — the user can press Enter to keep it.

**Name** — full display name (e.g. "Aaron Judd")

**Email** — work email (e.g. "ajudd@youngliving.com")

**Jira Account ID** — used in all Jira JQL queries to scope results to this user. Two options:
- Type "lookup" to search Atlassian by the email provided above. Call `lookupJiraAccountId` with `cloudId: "9de6eb2b-2683-44e6-89ff-c622027e09b4"` and `query: <email>`. Display the name and account ID returned — ask the user to confirm before accepting.
- Or paste the account ID directly.

**Teams User ID** — Microsoft 365 user ID used when creating chats or sending messages. Two options:
- Type "lookup" to search via `search_actions` with `category: "people"` and the user's email. Extract the user GUID from the result and show it for confirmation.
- Or paste the user ID directly.
- Or press Enter to skip — this can be set later.

### 3. Collect defaults

**Jira project key** — the project key for JQL queries (default: `BPT2`). Press Enter to keep.

**Default story chat members** — emails of teammates to auto-add when creating new story chats. Enter as comma-separated values, or press Enter for none. Parse into an array, trimming whitespace from each entry.

### 4. Confirm and write

Display a summary of all values before writing:

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

If yes, write the file with this structure:

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

Fill in actual values for all fields. `storyChatMembers` should be an array of email strings (empty array if none provided).

Confirm: "Config written to ~/.claude/plugins/user-config.json. You're ready to use the plugins."

If no: "Config not saved." and stop.
