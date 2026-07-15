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
  Handle:        <user.handle or "(not set)">
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
  Handle:   ajudd                   (derived from email prefix)
  Email:    ajudd@youngliving.com   (from git config)
  Jira ID:  620147d91fec260068...   (looked up from Atlassian)
  Teams ID: 4a1b2c3d-...            (looked up from Microsoft 365)

  Jira Project:  BPT2               (default)
```

**Handle** is the short @-tag used to attribute session history and inbox entries (e.g. `@ajudd`). It defaults to the email prefix — only change it if you want a different short identifier.

For any field that is blank or wrong, the user can correct it now.

Ask: "Does everything look right? Type a field name to change it (name / handle / email / jira / teams / project), or type 'go' to continue."

- If they type a field name (e.g. "name", "handle", "email", "jira", "teams", "project"): prompt for that field, then re-display the screen.
- If they type "go": proceed to step 5.

For blank fields that were not auto-detected, prompt for them explicitly before allowing the user to proceed:
- **Name**: "Your full display name (e.g. 'Jane Smith'):"
- **Email**: "Your work email (e.g. 'jsmith@example.com'):"
- **Jira ID**: "Your Jira account ID — or type 'lookup' to search by email:"
  - If "lookup": call `lookupJiraAccountId` and show results for selection.
  - If pasted directly: use as-is.
- **Teams ID**: "Your Microsoft 365 user ID — or type 'lookup' to retry, or type 'skip' to leave blank:"
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

   Ask: "Correct? Type a field name to change it (name / email / jira / teams / github), or type 'go' to continue."

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
**Auto-detect marketplace name:** List directories under `~/.claude/plugins/marketplaces/` and use the first one found as the default. This is the name Claude Code assigned when the marketplace was installed — users don't choose it, it comes from the repo's `marketplace.json`. Only falls back to `ajudd-claude-plugins` if detection fails.

Display a form. Type 'go' to accept all shown values, or type a field name to change one (marketplace / work / personal):

```
Workspace paths:

  Plugin marketplace name:  <current value or "ajudd-claude-plugins">
    (the name of your personal Claude Code plugin collection — matches what you used
     when running `claude plugin marketplace add <url>`)
    → plugins stored at: ~/.claude/plugins/marketplaces/<name>/

  Work repos directory:     <current value or detected or "(not set)">
    (parent folder for your work / company repositories — e.g. Young Living projects)

  Personal projects dir:    <current value or detected or "(not set)">    [optional]
    (parent folder for your own personal and experimental projects outside of work
     — e.g. side projects, experiments, anything not tied to an employer)
```

For any field left blank or skipped: write an empty string. The relevant plugin will prompt once and write the value when it first needs it.

Note: Playwright test directories are configured per-project when you first run `/e2e:start` — not stored here.

After the user confirms all values, proceed to Step 6a.

> **Note (acp-ajudd#1):** there is no longer a "session enforcement" opt-in. The session plugin never blocks edits — enforcement is now purely command-level (the session commands refuse to run without a session; editing files is never policed). The old `sessionGate.enforce` toggle and its `session-scope-guard.py` hook were removed. Nothing to configure here.

### 6a. Offer to install the `ccs` repo launcher

`ccs` is a shell shortcut that cds into a repo and launches Claude Code in one step:
`ccs vo` → virtual-office, `ccs plugins` → the marketplace clone, `ccs` alone → launch
Claude in the current directory; an unknown argument falls back to a starts-with scan of
your work repos. It ships with the setup plugin (`${CLAUDE_PLUGIN_ROOT}/scripts/ccs.sh`
and `ccs.ps1`) and is installed into your shell profile(s) here.

**Offer it explicitly — never install silently, and do not skip this step just because
it's optional.** Most people won't find it from docs; this active offer is how it reaches
the team, and word-of-mouth does the rest.

**1. Resolve inputs** from the values just configured in Step 6 (or the existing config file):
- `repos_base` = `paths.workReposDir` (e.g. `/c/dev`) — may be empty if skipped
- `marketplace` = `paths.pluginMarketplaceName` (e.g. `ajudd-claude-plugins`)

**2. Detect available shells** and whether `ccs` is already installed. Run:
```bash
BASHRC="$HOME/.bashrc"
PS_WIN="$HOME/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1"   # Windows PowerShell 5.1
PS_CORE="$HOME/Documents/PowerShell/Microsoft.PowerShell_profile.ps1"          # pwsh 7+
for f in "$BASHRC" "$PS_WIN" "$PS_CORE"; do
  if [ -f "$f" ]; then
    if grep -qF "# >>> ccs launcher" "$f"; then echo "$f: installed"; else echo "$f: present, ccs not installed"; fi
  else
    echo "$f: (no profile)"
  fi
done
```
On Windows most users have both a bash (`~/.bashrc`) and a PowerShell profile — offer whichever exist. If a shell has no profile yet, still offer it (you'll create the file).

**3. Offer** — plain-text routing (show the per-shell status from step 2):
```
Install the `ccs` repo launcher? — one command to cd into a repo + start Claude
  bash   — <not installed | installed (will update)>
  pwsh   — <not installed | installed (will update)>
  both / skip
```

**4. On accept**, for each chosen shell, read the shipped template, substitute the two
tokens, and install idempotently. Use a language that treats the values **literally** —
the Windows path contains backslashes, so `sed` is unsafe here; use python:

```bash
# Substitute tokens into a temp block file.
#   $TMPL = ${CLAUDE_PLUGIN_ROOT}/scripts/ccs.sh  (bash)  or  ccs.ps1  (PowerShell)
#   $BASE = repos_base   $MKT = marketplace   $WIN = 1 for the .ps1 (translate path form)
python3 - "$TMPL" "$BASE" "$MKT" "$WIN" > /tmp/ccs.block <<'PY'
import sys
tmpl, base, mkt, win = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] == "1"
def to_win(p):
    if not p: return ""
    if p.startswith('/') and len(p) > 2 and p[2] == '/':   # /c/dev -> C:\dev
        return p[1].upper() + ':' + p[2:].replace('/', '\\')
    return p.replace('/', '\\')
if win: base = to_win(base)
s = open(tmpl, encoding='utf-8').read()
sys.stdout.write(s.replace('__CCS_REPOS_BASE__', base).replace('__CCS_MARKETPLACE__', mkt))
PY
```
- **bash** uses `repos_base` as-is (`/c/dev`); **PowerShell** translates MSYS→Windows form
  (`/c/dev` → `C:\dev`). Empty `repos_base` substitutes an empty string — the function still
  works for `ccs` (cwd) and `ccs plugins`; the starts-with scan just reports "no repos base
  dir configured".

Then install the block into the profile using the marker sentinels that ship in the
template (`# >>> ccs launcher …` / `# <<< ccs launcher <<<`):

```bash
install_ccs_block() {   # $1 = profile path, $2 = block file
  local profile="$1" block="$2"
  mkdir -p "$(dirname "$profile")"; touch "$profile"
  if grep -qF "# >>> ccs launcher" "$profile"; then
    awk -v bf="$block" '
      BEGIN { while ((getline l < bf) > 0) blk = blk l ORS }
      /# >>> ccs launcher/ { print blk; skip=1; next }   # emit new block, drop old
      skip && /# <<< ccs launcher/ { skip=0; next }
      !skip { print }
    ' "$profile" > "$profile.tmp" && mv "$profile.tmp" "$profile"
  else
    printf '\n%s' "$(cat "$block")" >> "$profile"
  fi
}
```
- If both markers already exist → **replace in place** (never double-append).
- Else → append with a leading blank line.
- Profile targets: bash → `~/.bashrc`; PowerShell → whichever of `$PS_WIN` / `$PS_CORE`
  exists (both if both do), else create `$PS_WIN`.

**5. Tell the user to reload:**
```
Installed `ccs` into <profile(s)>. Open a new shell — or run `source ~/.bashrc`
(bash) / `. $PROFILE` (PowerShell) — to start using it: try `ccs plugins`.
```

On **skip**, note it's available later: "You can add it anytime by re-running `/setup:onboarding`."

Proceed to Step 7.

### 7. Confirm and write user config

Display a final summary:

```
About to write ~/.claude/plugins/user-config.json:

  name:                    <value>
  handle:                  <value>
  email:                   <value>
  jiraAccountId:           <value>
  teamsUserId:             <value or "(not set)">
  jiraProject:             <value>
  pluginMarketplaceName:   <value>
  workReposDir:            <value or "(not set)">
  personalProjectsDir:     <value or "(not set)">
  startFlow:               <value or "classic">   (advanced — controls the session plugin's start flow; see docs)
```

Ask: "Write this config? (y/n)"

If yes, **read the existing `~/.claude/plugins/user-config.json` first** (if it exists), then merge in the updated values — do not blindly overwrite. Any section the user skipped (e.g. identity was "n" in Step 1) keeps its existing values from the file. Write the merged result:

```json
{
  "user": {
    "name": "<collected or preserved>",
    "handle": "<collected or preserved>",
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
    "personalProjectsDir": "<collected or preserved or empty string>"
  },
  "startFlow": "<preserved, else \"classic\">"
}
```

**`startFlow` (acp-ajudd#120):** controls which `/session:start` flow file the session plugin's dispatcher loads for plugin/personal zones — `classic` (today's flow, and the only functional option right now) or `wizard` (a question-first flow, not yet built). Never overwrite an existing value on a re-run; write `"classic"` only when the key is absent. No prompt is asked for this — it's a forward-compatible placeholder until the wizard flow ships.

**No session-enforcement config.** The session plugin never blocks edits — enforcement is command-level only (acp-ajudd#1), so there is no `sessionGate` block to write. If a pre-existing `~/.claude/plugins/user-config.json` still carries a `sessionGate` key from an older install, it is inert (nothing reads it); preserve it as-is on a merge rather than churning the file, or drop it — either is fine.

Confirm with the following message — display it exactly as shown:

```
Config written. Here's how to get started:

─────────────────────────────────────────────────────────────
Daily Workflow

  Start of day:    /session:start  →  /setup:local
  Working a story: /story:dashboard  →  /story:create  →  /session:checkpoint  →  /session:commit
  Shipping it:     /release:create  →  /release:deploy  →  /session:finish
  Stay current:    /setup:update  →  restart Claude Code
  Jump to a repo:  ccs <acronym>  (shell shortcut — cd + launch Claude; e.g. ccs vo, ccs plugins)

─────────────────────────────────────────────────────────────
Key Commands to Know First

  /session:start      Start every working session here — loads your prior context
  /setup:local        Morning briefing — AWS login, open stories, calendar
  /story:dashboard    Your open BPT2 stories grouped by status
  /story:create       Create a new BPT2 story with all required fields
  /session:finish     End of day — saves state, updates Jira, posts Teams summary

─────────────────────────────────────────────────────────────
Session Security

  When you work on repos where teammates also use session files (.claude/sessions/),
  a local approval hash at ~/.claude/memory/sessions/<slug>/<name>.approved-hash
  tracks the last content you approved. If a teammate modifies a session file, you'll
  see a diff and approve the changes before they enter your context. This file is
  created automatically on first session load — no manual setup needed.

  To protect a new repo: run /session:migrate from any session in that repo.
  This moves session files into the repo and installs the pre-commit guard so
  injection content is blocked before it can even be committed.

─────────────────────────────────────────────────────────────

For a full reference on any plugin and its commands:

  /setup:guide               → overview of all plugins
  /setup:guide <plugin-name> → deep dive on a specific plugin
  Example: /setup:guide story
```

If no: "Config not saved." and stop.

## Error Handling

- If `git config` is unavailable (git not installed): skip silently, proceed to manual prompts.
- If Atlassian MCP is unavailable: skip Jira lookup, prompt manually.
- If yl-msoffice MCP is unavailable: skip Teams lookup, note Teams ID can be set later.
- Never block onboarding due to a lookup failure — always offer manual entry as a fallback.
