# Prompt Patterns

Canonical AskUserQuestion widget patterns for all interactive prompts in the session plugin. Every prompt that asks the user to make a choice must use AskUserQuestion — no verb tables, no numbered lists requiring typed answers.

Reference by name in each command file (e.g. "use **ConfirmPrompt**"). Always include the YAML inline so the command is self-contained. The "Other" free-text option is always available to the user — never add it as an explicit option.

---

## ConfirmPrompt

Binary yes/skip for optional actions. Use for: Teams update, Confluence page, story doc, browser stop, epic update, etc.

```yaml
question: "<action, ending with ?>  e.g. Post a closing update to [teams_chat]?"
header: "<short label, max 12 chars>"
options:
  - label: "Yes"
    description: "<what happens if yes>"
  - label: "Skip"
    description: "Continue without doing this"
```

---

## CommitConfirmPrompt

Confirm, edit, or cancel a git commit. Used in session:commit Step 2.

```yaml
question: "Commit and push with this message?"
header: "Commit"
options:
  - label: "Commit and push"
    description: "Stage, commit, and push with the drafted message"
  - label: "Edit message"
    description: "Use a different message — you'll provide it next"
  - label: "Cancel"
    description: "Stop — do not commit"
```

After **Edit message** → ask: "What message would you like to use?"

---

## MarkDonePrompt

Mark items from a numbered list as complete. Display the list above the widget.

```yaml
question: "Mark any complete?"
header: "Open items"
options:
  - label: "Done (all)"
    description: "Mark all items complete and remove from list"
  - label: "Done (select)"
    description: "Mark specific items done — you'll pick the numbers next"
  - label: "Skip"
    description: "None done yet — keep all open"
```

After **Done (select)** → ask: "Which items? (number or comma list, e.g. 1, 3)"

---

## InProgressInboxPrompt

Mark in-progress inbox items done at checkpoint, finish, or switch. Display the numbered list above the widget.

```yaml
question: "Mark any in-progress items done?"
header: "In-progress"
options:
  - label: "Done (all)"
    description: "Mark all complete, archive, and remove from Open items"
  - label: "Done (select)"
    description: "Mark specific items done — you'll pick the numbers next"
  - label: "Keep"
    description: "Keep all in-progress — carry to next session"
```

After **Done (select)** → ask: "Which items? (number or comma list, e.g. 1, 3)"

This is the same pattern used in session:start Step 5.

---

## InboxItemPrompt

Decide what to do with pending inbox items. Display the numbered list above the widget.

```yaml
question: "What would you like to do with these items?"
header: "Inbox"
options:
  - label: "work"
    description: "Pick up — mark in-progress and add to Open items"
  - label: "done"
    description: "Mark complete — archive without picking up"
  - label: "backlog"
    description: "Defer to backlog for later"
  - label: "keep"
    description: "Leave as-is — no action"
```

After any selection → ask: "Which item(s)? (number, comma list, or 'all')"

This is the same pattern used in session:start Step 5.

---

## PendingSweepPrompt

Handle pending inbox items at checkpoint/finish that were addressed outside in-progress tracking. Display the numbered list above the widget.

```yaml
question: "Any inbox items addressed this session outside in-progress tracking?"
header: "Inbox sweep"
options:
  - label: "Done (select)"
    description: "Archive as complete — you'll pick the numbers next"
  - label: "Picked up (select)"
    description: "Mark in-progress — you'll pick the numbers next"
  - label: "Nothing"
    description: "Nothing addressed — skip"
```

After **Done (select)** or **Picked up (select)** → ask: "Which items? (number or comma list)"

---

## ScopeActionPrompt

Handle out-of-scope work at checkpoint or commit (warn-but-continue). Display out-of-scope items above the widget.

```yaml
question: "What would you like to do with the out-of-scope work?"
header: "Scope"
options:
  - label: "Route"
    description: "Send to target inbox — work is formally handed off"
  - label: "Note"
    description: "Acknowledge only — excluded from this record, no handoff"
  - label: "Skip"
    description: "Continue without noting"
```

---

## ScopeActionCancelPrompt

Handle out-of-scope work at finish (hard block — cannot close without resolving). Display out-of-scope items above the widget.

```yaml
question: "What would you like to do with the out-of-scope work?"
header: "Scope"
options:
  - label: "Route"
    description: "Send to target inbox — work is formally handed off"
  - label: "Note"
    description: "Acknowledge as out-of-scope, exclude — no handoff"
  - label: "Cancel finish"
    description: "Stop — I'll handle the out-of-scope work manually before closing"
```

---

## YlCdkCheckPrompt

Verify yl-cdk pattern check before Jira update. Story/CAB sessions only.

```yaml
question: "Were the yl-cdk-migration and yl-cdk-monitoring skills used to verify DynamoDB/CDK design patterns?"
header: "yl-cdk check"
options:
  - label: "Yes"
    description: "Skills were run — proceed"
  - label: "Not applicable"
    description: "No CDK or DynamoDB changes this session"
  - label: "Remind me"
    description: "Surface a reminder but continue without blocking"
```

---

## NextStepRoutePrompt

Where to route a new next-step item at session:finish. Shown after the derived next-step.

```yaml
question: "Add a new next-step item?"
header: "Next step"
options:
  - label: "Inbox (ready)"
    description: "Route to session inbox now — will surface at next start"
  - label: "Backlog (defer)"
    description: "Write to backlog — review when you choose to"
  - label: "Skip"
    description: "Keep the derived next-step as-is"
```

---

## ApproveSessionPrompt

Approve a repo session file for the first time (no prior approved-hash). Used in session:start and session:switch Step 4.

```yaml
question: "First-time load from repo — approve and load this session file?"
header: "Approval"
options:
  - label: "Approve and load"
    description: "Trust this session file — write the approval hash"
  - label: "Skip teammate fields"
    description: "Load with items from other handles quarantined for review"
  - label: "Cancel"
    description: "Abort — do not load this session"
```

---

## ReapproveSessionPrompt

Approve a repo session file that changed since last approval. Used in session:start and session:switch Step 4.

```yaml
question: "Session file changed since you last approved it — approve these changes?"
header: "Approval"
options:
  - label: "Approve changes"
    description: "Trust the updated file — overwrite approval hash"
  - label: "Load quarantined"
    description: "Load with changed fields shown as pending review — hash stays unapproved"
  - label: "Cancel"
    description: "Abort — do not load this session"
```

---

## AdoptTeammatePrompt

Adopt teammate next-step suggestions into your own active list. Shown after teammate next steps display in session:start.

```yaml
question: "Adopt any teammate next steps as your own?"
header: "Teammate"
options:
  - label: "Adopt all"
    description: "Take ownership of all teammate suggestions"
  - label: "Adopt (select)"
    description: "Pick which ones to adopt — you'll give the numbers next"
  - label: "Skip"
    description: "Keep as reference only — not added to your active list"
```

After **Adopt (select)** → ask: "Which items? (number or comma list)"

---

## TeamsChatCreatePrompt

Teams chat not found — create it, skip, or use a different one. Used in session:start Step 7.

```yaml
question: "No Teams chat found for '<teams_chat>' — what would you like to do?"
header: "Teams chat"
options:
  - label: "Create it"
    description: "Create a new Teams chat with default members"
  - label: "Use different"
    description: "Point to an existing chat — you'll name it next"
  - label: "Skip"
    description: "Set teams_chat to none — Teams steps will be skipped"
```

After **Use different** → ask: "Which existing chat should this session use?"

---

## PluginReviewedPrompt

Prompt to mark the plugin as reviewed. Used in session:start Step 9, session:checkpoint Step 6, and session:finish Step 11.

```yaml
question: "Plugin reviewed this session?"
header: "Review"
options:
  - label: "Yes — reviewed"
    description: "I ran the code-reviewer — mark as reviewed for this version"
  - label: "No"
    description: "Skip — reminder will fire at next session start"
```

---

## SessionPickerPrompt

Pick from a list of ≤ 4 sessions. For > 4: show the numbered table then ask plain text "Which number?".

For ≤ 4 sessions:
```yaml
question: "<action> which session?  e.g. Resume which session?"
header: "Session"
options:
  - label: "<session-name-1>"
    description: "<type> · <status> · last <friendly-date>"
  - label: "<session-name-2>"
    description: "..."
  - label: "None"
    description: "Don't switch / cancel"
```

For > 4 sessions: display the numbered table, then ask as plain text:
"Which session? (number or name, or 'none')"

---

## SpawnTypePrompt

Pick a session type for a new spawn. Used in session:spawn Step 2.

```yaml
question: "What type of work is this spawn?"
header: "Type"
options:
  - label: "story"
    description: "Jira story — BPT2-XXXX work in a work repo"
  - label: "plugin"
    description: "Plugin development in ajudd-claude-plugins"
  - label: "personal"
    description: "Personal project under ~/claude/"
  - label: "general"
    description: "General / research / other"
```

"Other" → free-text; also handles `cab` (two or more stories deploying together).

---

## ContextSourcePrompt

Decide how to populate the spawn's context. Used in session:spawn Step 3.

```yaml
question: "What context should the new session inherit?"
header: "Context"
options:
  - label: "Auto-derive"
    description: "Summarize key findings and decisions from this conversation"
  - label: "I'll describe it"
    description: "Provide the context manually — you'll enter it next"
```

After **I'll describe it** → ask: "Describe the context the spawned session should inherit:"

---

## SwitchOfferPrompt

Offer to switch to a matched session after a search. Used in session:search Step 6.

For one match:
```yaml
question: "Switch to '<name>'?"
header: "Switch"
options:
  - label: "Switch"
    description: "Run /session:switch <name> now"
  - label: "No"
    description: "Stay in current session — results shown above"
```

For 2–4 matches: use SessionPickerPrompt with the matched names as options.
For > 4 matches: display numbered list and ask "Switch to one? (number or 'n')"

---

## InboxTargetConfirmPrompt

Confirm the routing target before writing to an inbox. Used in session:inbox Step 2.

```yaml
question: "Route to <target-name> inbox?"
header: "Route"
options:
  - label: "Yes, route there"
    description: "Write to <target-name>'s inbox — will surface at their next session start"
  - label: "Pick different"
    description: "Choose a different target — you'll pick from the list next"
```
