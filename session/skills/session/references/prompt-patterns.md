# Prompt Patterns

Interaction patterns for the session plugin. **Never use AskUserQuestion** — all prompts use plain text output followed by a single free-text reply.

---

## Core Rules

1. **No AskUserQuestion anywhere.** No widget, no select-before-type, no click-to-answer.
2. **Batch all known questions.** Show them all at once. Only add a second stop when an answer creates new content to review (Teams message draft, commit message).
3. **Show defaults inline.** The user types only overrides — not confirmations.
4. **Accept any natural phrasing.** Parse `2 yes`, `yes 2`, `skip teams`, `2 / 4 skip`, `2 yes 4 skip`, etc. If genuinely ambiguous about which question an answer applies to, ask one targeted clarifying question.
5. **"go" means accept all defaults.** Consistent shortcut across every batched block.
6. **Omit questions with obvious-only answers.** If a question can only have one reasonable answer in context (e.g., scope is always clean, inbox is empty), skip it rather than confirming.

---

## Pattern 1 — Routing Block

*Used in: session:start Step 3, session:switch Step 2, session:search Step 6*

Show the table or list, then one instructional line. Claude outputs the block and waits for one free-text reply.

```
[sessions table or list]

  <verb> <target>  ·  <verb> <target>  ·  <verb>
```

**Plugin example** (item-driven — `pick` from the inbox, never blank/plugin-named):
```
  resume <n>  ·  pick <n>  ·  new <description>
```

**Work project example:**
```
  resume <n>  ·  start story  ·  start cab
```

Accepted inputs: number (`1`), session name (`session`), verb+target (`resume 1`, `start release`), or natural language. Claude infers intent. If genuinely ambiguous, ask one clarifying question.

---

## Pattern 2 — Batched Question Block

*Used in: session:start (post-load inbox + mode + review), session:checkpoint, session:finish*

List all pending questions with defaults shown inline. Claude outputs the block and waits for one reply.

```
  (1) <question>?    <default>    [optional hint]
  (2) <question>?    <default>
  (3) <question>?    <default>

Reply with overrides or "go".
```

**Default guidelines:**
- Safe-to-skip actions → `skip`
- Expected actions (e.g., commit when git is dirty) → `yes`
- Open items / inbox items → `keep` (never auto-close without user input)

**Parsing overrides:** any of these work:
- `2 yes` / `yes 2` / `(2) yes`
- `2 yes, 4 skip` / `2 yes / 4 skip` / `2 yes 4 skip`
- `skip all` / `yes all`
- Text value: `4 "write tests first"` or just `4 write tests first`
- `go` → accept all defaults

**Omit the batch block entirely** if there is nothing to decide (all items have forced defaults and no user input is possible). Just proceed silently.

---

## Pattern 3 — Inline Options Line

*Used in: session:start when showing post-load context (inbox, mode, review)*

Add a compact options line immediately after showing the relevant data, without a separate stop. Claude folds parsing into the routing reply or resume response.

```
Last active: <name>  ·  mode: <mode>  [·  ⚠ not reviewed since v<old> (current v<new>)]
  Inbox (2):
    1  <description> — pending
    2  <description> — pending

  resume <n>  ·  pick <n>  ·  new <description>
  + planning / both → change mode  ·  reviewed → mark it
```

User types `pick 1 planning` or `resume 2 reviewed` and Claude handles all of it.

---

## Pattern 4 — Generated Content Approval

*Used for: Teams messages, commit messages — any content Claude drafts before sending*

The only justified second stop in a command. Show the draft inline and wait.

```
[Content type] draft:
---
[full content]
---
Send this? (go / edit: <your version> / skip)
```

---

## Pattern 5 — Scope Warning

*Checkpoint (warn-but-continue): fold into the batch block*
```
  (N) Out-of-scope: <path> → route to <target>?    yes / note / skip
```

*Finish (hard block): show prominently before the question block*
```
Cross-scope work detected:
  · <file path>  (belongs in: <target> / <session>)

Resolve before closing:
  (N) Route to <target> inbox?    yes / note / cancel
```

---

## Pattern 6 — Security Approval (Repo Sessions)

*Used in: session:start Step 4 for first-load or changed hash*

Show the relevant content (key fields or git diff), then a plain-text prompt. No widget.

**First-time load:**
```
First time loading this session file from the repo — reviewing before use.
[key fields shown]

Approve and load / skip-teammate-fields / cancel
```

**Changed since last approval:**
```
Session file changed since you last approved it — @<committer>, <time ago>.
[diff shown]

Approve changes / load-quarantined / cancel
```

---

## Removed Patterns

The following are **removed** — do not use:

- `AskUserQuestion` — removed entirely from this plugin
- Sequential single-question stops ("Mark as reviewed?", "Mode — keep it or change?") — use batch block
- Verb tables with follow-up "Which number?" questions — use routing block
