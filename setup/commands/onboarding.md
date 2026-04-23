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
```

Ask: "Update this config? (y/n)" — if no, skip to step 5 to check team registry.

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
```

For any field that is blank or wrong, the user can correct it now.

Ask: "Does everything look right? Enter a field name to change it, or press Enter to continue."

- If they type a field name (e.g. "name", "email", "jira", "teams", "project"): prompt for that field, then re-display the screen.
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

### 5. Team registry

After confirming the user's own identity, offer to populate `~/.claude/plugins/team.json` with teammates. This replaces the old `storyChatMembers` defaults — all team-based lookups (story chats, CAB approvals, PR reviewers) now read from this file.

**Check for existing registry:**

If `~/.claude/plugins/team.json` already exists, read it and display current members:

```
Team registry (~/.claude/plugins/team.json):

  1. Heber Iraheta — story-chat, qa-approver, code-review-approver
  2. Nivi Umasankar — story-chat
  ...
```

Ask: "Update team registry? (y/n)" — if no, skip to step 6.

**If yes (or no existing registry), explain briefly:**

```
The team registry stores colleagues by role so plugins can look up
the right person automatically (e.g. who approves CAB cards, who to
add to story chats, who reviews PRs).
```

**Add member loop:**

For each new member:

1. Ask only: **"Name:"** — first name, full name, or display name is all that's needed.

2. **Immediately fire parallel lookups** — do not ask for anything else first:

   **Jira lookup:**
   Call `lookupJiraAccountId` with `cloudId: "9de6eb2b-2683-44e6-89ff-c622027e09b4"` and `query: <name>`.
   - On success: extract `accountId` and `emailAddress` from the first result. Note both as "(looked up from Atlassian)".
   - If multiple results: show a numbered list and ask the user to pick — "Found multiple matches, which one?"
   - On transient error: retry once automatically.
   - On failure after retry or no results: note both as "(not found)".

   **Teams lookup — two-step (run in parallel with Jira if email not yet known, or after Jira resolves the email):**

   Step A: Call `search_actions` with action `people.search` and the name as the query. Extract the `email` from the result.
   Step B: Call `execute_action` with action `user.get` and the email from Step A. Extract the `id` field — this is the Teams user ID.
   - Note result as "(looked up from Microsoft 365)".
   - If Step A returns no email, or Step B fails: note Teams ID as "(not found)" — it is optional and can be filled in later.

   **Important:** Do NOT use `search_actions` with `category: "people"` as a single-call lookup — it fails with output validation errors. The correct pattern is always `people.search` → email, then `user.get` → id.

3. **GitHub lookup — derive from email prefix** (run in parallel with Teams lookup):

   GitHub name/email search is unreliable for YL users because work emails are private
   and contractor accounts use a `v-` prefix that doesn't appear in display names.
   Use the email from the Jira result to derive and verify the login instead.

   Step A: Extract the email prefix from the Jira result (part before `@`).
   Example: `hiraheta@youngliving.com` → prefix = `hiraheta`

   Step B: Try `v-{prefix}` first (contractor pattern — covers `v-mporras`, `v-hiraheta`, etc.):
   ```bash
   gh api "users/v-hiraheta"
   ```
   - If the API returns a user object: use `v-{prefix}` as the GitHub login. Note "(verified via GitHub API)".

   Step C: If `v-{prefix}` returns 404, try `{prefix}` without the `v-` prefix:
   ```bash
   gh api "users/hiraheta"
   ```
   - If found: use `{prefix}` as the GitHub login. Note "(verified via GitHub API)".

   Step D: If both return 404 or error: note GitHub as "(not found)" — prompt manually on the confirm screen.

4. **Show confirm/correct screen** with everything resolved:

   ```
   Member 1 — found:
     Name:      Heber Iraheta                          (from Jira)
     Email:     hiraheta@youngliving.com               (from Jira)
     Jira ID:   557058:055d4592-8fbf-4b3c-...         (looked up)
     Teams ID:  61045e43-487a-41db-abf8-862cbd3512d0  (looked up from Microsoft 365)
     GitHub:    (not set)
   ```

   Ask: "Correct? Enter a field name to change it (name/email/jira/teams/github), or press Enter to continue."

   - All fields except Name are optional — skip anything unknown and fill in later via `/setup:onboarding`.

5. **Assign roles** — show numbered list, user enters comma-separated numbers:

   ```
   Assign roles (comma-separated, e.g. "1,3"):

     1. story-chat           — added to new story Teams chats by default
     2. qa-approver          — QA sign-off on CAB cards
     3. code-review-approver — code review sign-off on CAB cards
     4. cab-assignee         — assigned after CAB Send For Review
     5. pr-reviewer          — pinged when prod GitHub environment gate needs approval

   Roles: _
   ```

6. Add to registry. Display: "Added <name> with roles: <role list>"

7. Ask: "Add another team member? (y/n)"
   - If yes: repeat from step 1
   - If no: proceed to write

**Write team.json:**

Write `~/.claude/plugins/team.json`:

```json
{
  "members": [
    {
      "name": "<name>",
      "email": "<email>",
      "jiraAccountId": "<accountId or empty string>",
      "teamsUserId": "<teamsUserId or empty string>",
      "githubLogin": "<login or empty string>",
      "roles": ["<role1>", "<role2>"]
    }
  ]
}
```

If the file already existed, merge new members in — do not overwrite existing entries unless the user corrected a field.

Confirm: "Team registry written to ~/.claude/plugins/team.json."

### 6. Workspace paths

Configure the file system paths that plugins use to find your repos, projects, and tools. Paths marked "(optional)" can be skipped now — a plugin will prompt for them on demand the first time it needs them.

**Read existing values first.** If `~/.claude/plugins/user-config.json` already has a `paths` section, use those values as the defaults in the form below — this preserves what was already set on a re-run.

**Auto-detect where possible** for any field not already set:
- **pluginMarketplaceName**: default to `ajudd-claude-plugins`
- **workReposDir**: check if `/c/dev` exists; if yes, suggest it
- **personalProjectsDir**: check if `/c/claude` exists; if yes, suggest it (optional)
- **voPlaywrightTestsDir**: if workReposDir is known and `<workReposDir>/vo-playwright-tests` exists, suggest it (optional)

Display a form. Press Enter to accept the shown value, or type a replacement:

```
Workspace paths:

  Plugin marketplace name:  <current value or "ajudd-claude-plugins">
    (name used when installing this marketplace — drives plugin scope paths)

  Work repos directory:     <current value or detected or "(not set)">
    (parent folder where your work repos are cloned)

  Personal projects dir:    <current value or detected or "(not set)">    [optional]
    (parent folder for personal side projects — skip if not applicable)

  VO Playwright tests dir:  <current value or detected or "(not set)">   [optional]
    (full path to vo-playwright-tests repo — only needed for /e2e:start)
```

For any field left blank or skipped: write an empty string. The relevant plugin will prompt once and write the value when it first needs it.

After the user confirms all values, proceed to Step 7.

### 7. Confirm and write user config

Display a final summary:

```
About to write ~/.claude/plugins/user-config.json:

  name:                    <value>
  email:                   <value>
  jiraAccountId:           <value>
  teamsUserId:             <value or "(not set)">
  jiraProject:             <value>
  pluginMarketplaceName:   <value>
  workReposDir:            <value or "(not set)">
  personalProjectsDir:     <value or "(not set)">
  voPlaywrightTestsDir:    <value or "(not set)">
```

Ask: "Write this config? (y/n)"

If yes, **read the existing `~/.claude/plugins/user-config.json` first** (if it exists), then merge in the updated values — do not blindly overwrite. Any section the user skipped (e.g. identity was "n" in Step 1) keeps its existing values from the file. Write the merged result:

```json
{
  "user": {
    "name": "<collected or preserved>",
    "email": "<collected or preserved>",
    "jiraAccountId": "<collected or preserved>",
    "teamsUserId": "<collected or preserved or empty string>"
  },
  "defaults": {
    "jiraProject": "<collected or preserved>",
    "atlassianCloudId": "9de6eb2b-2683-44e6-89ff-c622027e09b4",
    "jiraProjectId": "12844"
  },
  "paths": {
    "browserLinksFile": "~/.claude/browser-links.json",
    "memoryRoot": "~/.claude",
    "pluginMarketplaceName": "<collected or preserved>",
    "workReposDir": "<collected or preserved or empty string>",
    "personalProjectsDir": "<collected or preserved or empty string>",
    "voPlaywrightTestsDir": "<collected or preserved or empty string>"
  }
}
```

Confirm: "Config written. You're ready to use the plugins. Run /setup:local to start your day."

If no: "Config not saved." and stop.

## Error Handling

- If `git config` is unavailable (git not installed): skip silently, proceed to manual prompts.
- If Atlassian MCP is unavailable: skip Jira lookup, prompt manually.
- If yl-msoffice MCP is unavailable: skip Teams lookup, note Teams ID can be set later.
- Never block onboarding due to a lookup failure — always offer manual entry as a fallback.
