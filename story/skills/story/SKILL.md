---
name: story
description: "Background skill — do not run directly. Use /story:create, /story:dashboard, or /story:update. Auto-loads when: creating Jira stories, checking open tickets, or any BPT2 key is mentioned."
---

# Jira Stories Skill — BPT2

Everything needed to create, populate, and manage stories in the BPT2 (Brand Partner Team Two) Jira project.

---

## Atlassian Connection

Always use these without asking — defined in global `CLAUDE.md`:

- Instance: `https://younglivingeo.atlassian.net`
- Cloud ID: `9de6eb2b-2683-44e6-89ff-c622027e09b4`
- Auth: Handled by the `claude.ai` Atlassian MCP

---

## Project / Issue Type

| Field | Value |
|-------|-------|
| Project Key | `BPT2` |
| Project ID | `12844` |
| Issue Type | `Story` |
| Issue Type ID | `10001` |

---

## Required Fields

These fields are required when creating a BPT2 story:

| Field | API Key | Type | Notes |
|-------|---------|------|-------|
| Summary | `summary` | string | Short descriptive title |
| Expenditures | `customfield_10902` | option ID | **Opex: `10948`**, Capex: `10949`. Default: Opex. |
| Work Allocation Type | `customfield_13609` | array of option IDs | Multi-checkbox. See values below. |

### Work Allocation Type Options

| Value | ID |
|-------|-----|
| Technical Debt (Principle) | `15096` |
| Maintenance (Interest) | `15097` |
| New Development (Stories) | `15098` |
| Production Issues (Problems) | `16361` |

---

## Common Optional Fields

| Field | API Key | Type | Notes |
|-------|---------|------|-------|
| Description | `description` | markdown (via edit) | **Must be set via `editJiraIssue`, not at creation.** See MCP quirks below. |
| Assignee | `assignee` | user (accountId) | Current user — read from `~/.claude/plugins/user-config.json` > `user.jiraAccountId` |
| Epic Link | `customfield_10001` | string | Epic key, e.g. `BPT2-1234` |
| Sprint | `customfield_10005` | sprint ID | Set via board if needed |
| Labels | `labels` | array of strings | e.g. `["decommission", "virtual-office"]` |

---

## People

| Person | Role | How to Look Up |
|--------|------|---------------|
| Current user | Default assignee / reporter | `user.jiraAccountId` from `~/.claude/plugins/user-config.json` |
| PR reviewers (Maikol, Fernando, Angela) | Dev team | Read `~/.claude/plugins/team.json` → members with role `pr-reviewer` |
| Story chat members (Heber, Nivi, …) | Default Teams chat | Read `~/.claude/plugins/team.json` → members with role `story-chat` → use `teamsUserId` |

---

## MCP Tool Quirks — CRITICAL

### Description formatting

**`createJiraIssue`** treats the `description` field as a literal string. Markdown is NOT converted — `\n`, `**bold**`, `- bullets` all render as raw text.

**`editJiraIssue`** DOES convert markdown to ADF correctly.

**Always use a two-step pattern:**
1. Create the issue with `createJiraIssue` — set summary + required custom fields only, skip or omit description
2. Immediately call `editJiraIssue` to set the description with proper markdown formatting

### Comments

**`addCommentToJiraIssue`** handles markdown correctly, including code blocks with syntax highlighting.

---

## Workflow / Status Transitions

Available transitions from Backlog (starting state):

| Transition | ID | Target Status |
|-----------|-----|---------------|
| In Progress | `421` | In Progress |
| Ready For Work | `181` | Ready For Work |
| Ready for Grooming | `431` | Ready for Grooming |
| Gathering Requirements | `581` | Gathering Requirements |
| Blocked | `31` | Blocked |
| Ready For Test | `21` | Ready For Test |
| Ready for Code Review | `191` | Ready for Code Review |
| Ready for UAT | `591` | Ready for UAT |
| Done | `331` | Done (has screen) |
| Cancelled | `41` | Cancelled (has screen) |
| Released | `231` | Released |
| Approved for Release | `261` | Approved for Release |
| Deferred | `571` | Deferred |
| Waiting on Business | `491` | Waiting on Business |
| Architecture Review | `511` | Architecture Review |
| Failed Testing | `211` | Failed Testing |
| QA In-Progress | `601` | QA In-Progress |

---

## Registry Schema — `~/.claude/jira-stories.json`

Flat JSON object keyed by story key (e.g. `"BPT2-6190"`). Each value:

| Field | Type | Description |
|-------|------|-------------|
| `hidden` | boolean | Whether the story is suppressed from default view |
| `hideReason` | string \| null | User-provided reason for hiding |
| `hiddenDate` | string \| null | ISO date the story was hidden (reserved for future auto-expiry) |
| `lastStatus` | string | Status as of last `/story:my-stories` run — used for change detection |
| `lastAssignee` | string | Assignee as of last run — used for change detection |
| `lastSeen` | string | ISO date of last run that touched this entry |

Do not add extra fields without updating this schema.

---

## Canonical JQL Queries

<!-- CANONICAL SOURCE — update here first, then sync to: story/commands/dashboard.md, setup/commands/jira.md, setup/commands/local.md, setup/skills/setup/SKILL.md -->
<!-- {ACCOUNT_ID} = value from ~/.claude/plugins/user-config.json > user.jiraAccountId -->

**Currently assigned to me:**
```jql
assignee = "{ACCOUNT_ID}" AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, duedate ASC
```

**Previously assigned (reassigned to someone else, last 30 days):**
```jql
project = BPT2 AND assignee WAS "{ACCOUNT_ID}" AND assignee != "{ACCOUNT_ID}" AND assignee is not EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

**Previously assigned (now unassigned, last 30 days):**
```jql
project = BPT2 AND assignee WAS "{ACCOUNT_ID}" AND assignee is EMPTY AND updated >= -30d AND status not in (Done, Closed, Cancelled, Resolved, Released, Success, Remediated) ORDER BY status ASC, updated DESC
```

---

## Link Registration

After creating or picking up a story, register it in `~/.claude/browser-links.json` using the links plugin pattern:

1. Read `~/.claude/browser-links.json`
2. Add to `links` section: `"story:BPT2-XXXX": { "url": "https://younglivingeo.atlassian.net/browse/BPT2-XXXX", "description": "<story summary>" }`
3. Create workspace `BPT2-XXXX` if it doesn't exist: `{ "type": "story", "description": "<story summary>", "links": ["story:BPT2-XXXX"] }`
4. Write back to `~/.claude/browser-links.json`

Also add any related `git:repo-name` to the story workspace if the repo is known.

---

## Creation Pattern

```
Step 1: createJiraIssue
  - summary: "Story title"
  - additional_fields:
      customfield_10902: { id: "10948" }       # Opex
      customfield_13609: [{ id: "15097" }]     # Maintenance (or appropriate type)

Step 2: editJiraIssue
  - description: "### Heading\n- Bullet 1\n- Bullet 2"
  - assignee: { accountId: "{ACCOUNT_ID}" }  # read from ~/.claude/plugins/user-config.json

Step 3 (optional): transitionJiraIssue
  - transition: { id: "421" }    # Move to In Progress

Step 4 (optional): addCommentToJiraIssue
  - commentBody: "Additional details with **markdown** and ```code blocks```"
```

---

## Reference Files

- `references/jira-workflow.md` — Jira transition rules: when to clear assignee, status conventions
- `references/story-chats.md` — How to find a story's Teams chat by story number

---

## Post-Deployment Checks

Story session files support an optional `Post-deployment checks:` field — a markdown checkbox list of things to verify after the story ships in production. These are surfaced and acknowledged at CAB close (via `/release:deploy`) but **do not block the CAB from closing**.

**Format in session file:**
```
- **Post-deployment checks:**
  - [ ] Monitor 2+ hours — confirm no AWS alert emails on 2-hour cycle
  - [x] Check CloudWatch alarm state returns to OK within first cycle
```

- `- [ ]` — not yet acknowledged (will appear at CAB close)
- `- [x]` — acknowledged (someone noted whether the expected outcome was met)

**What "acknowledged" means:** The person deploying has noted the expected outcome and committed to following up. The check may have passed, failed, or not yet been verifiable. If the expected outcome was **not met**, the correct response is to write a follow-up story — not to hold up the CAB.

**When to add checks:**
- At `/session:finish` for the story — prompted automatically if none exist
- Any time during development when a specific post-deploy outcome must be verified

---

## Teams Messaging

**Story chat members:** When creating a new Teams chat for a story, add all members found
in `~/.claude/plugins/team.json` with role `story-chat` using their `teamsUserId`. If a
member's `teamsUserId` is blank, skip them silently — they can be added manually later.

Whenever any step in this plugin posts a Teams message, apply these rules without exception:

1. **Always end with the Claude signature** — no exceptions:
   `<p><em>Posted by Claude Code on behalf of {USER_NAME}</em></p>` (use `user.name` from `~/.claude/plugins/user-config.json`)
2. **Always preview before sending.** Show the full message content and wait for explicit approval before calling `send_chat_message`.
3. **Always use HTML formatting.** `send_chat_message` body supports and renders HTML.
4. **Always open with an intro paragraph** (`<p>`) before the first section.
5. **Follow the HTML guide.** Read `~/.claude/plugins/marketplaces/ajudd-claude-plugins/comms/skills/comms/references/teams-html-guide.md` before drafting any message.

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
<p>&nbsp;</p>
<p><em>Posted by Claude Code on behalf of {USER_NAME}</em></p>
```
