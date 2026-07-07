---
name: handoff
description: Emit a paste-ready handoff block for the current session — a self-contained block you copy into another live Claude session (another terminal/machine). Text only — writes no files, sends nothing, touches neither _active nor the session file. The human-carried counterpart to spawn/inbox.
---

# Session Handoff

Assemble the current session's context into the **standard handoff block** and print it — nothing more. The human copies the block (one click on the fenced block's copy button) and pastes it into a *different live Claude session* elsewhere, which then has everything it needs to continue the work.

This is the **human-carried** handoff path. Distinguish it from the file-based paths:

| Path | Mechanism | Crosses machines? |
|------|-----------|-------------------|
| `/session:inbox` | writes an item into a target slug's `_inbox.md` | no — same machine |
| `/session:spawn` | writes a `[spawn]` inbox item staging a linked session | no — same machine |
| **`/session:handoff`** | **prints a block you paste into a live session elsewhere** | **yes — you carry it** |

`inbox`/`spawn` travel through the filesystem; `handoff` travels through your clipboard. Because the receiving session has none of this conversation, the block must be **self-contained**. See the Session Skill § **Cross-Session Paste Handoff** for the format — that section is the single source of truth; this command does not restate the format.

## Instructions

### 1. Identify Current Session

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).

Determine the session name from conversation context (same pattern as `commit`/`checkpoint`):
1. Look for the most recent "Resuming `<name>`" (from `session:start`) or "Switching to `<name>`" (from `session:switch`) line. Use whichever is most recent.
2. Fall back to reading `~/.claude/memory/sessions/<slug>/_active` if not in context.

**Session guard (command-level enforcement — acp-ajudd#1).** `handoff` describes the active session, so a session must exist. If neither the conversation context nor `~/.claude/memory/sessions/<slug>/_active` yields a session name, **stop cleanly** — do not ask, do not guess, do not proceed:

```
No session established for <slug>. Run /session:start first.
```

(The `_active` check is existence-only, for the guard — conversation context wins for *which* session is current when one is present.) Editing files is never blocked; the session commands are what require a session. (`start` / `refine` and read-only views are exempt.)

### 2. Gather Handoff Context

Read `<session_root>/<name>.md` for the durable state (branch, open items, next steps, scope, related keys, loaded memories, recent commits). Combine it with what the current conversation surfaced to assemble what a *fresh* receiving session needs:

- **What we're doing** — the task in one or two sentences, stated from scratch.
- **Key decisions** — choices already made and options already rejected (so the receiver doesn't relitigate them).
- **Exact next action** — the single concrete thing to do next, not a vague direction.
- **Guardrails / do-NOTs** — constraints, out-of-scope areas, conventions to follow.
- **Relevant paths / inbox IDs** — files to open, `<acronym>-<handle>#<n>` item IDs, story/CAB keys, branch name.

Restate everything self-contained — never write "as we discussed above" or reference anything visible only in this conversation. Cap the body at what's genuinely needed; a receiver reads this cold.

**Target label:** if the user passed an argument (`/session:handoff <target>`), use it verbatim for the `To:` line. Otherwise infer a short target from context (a slug, session name, or topic), or write `To:    <topic>` with your best one-line description.

### 3. Emit the Handoff Block

Print the block in the **standard handoff format** (Session Skill § Cross-Session Paste Handoff). Fill the header from Step 1–2 and write the self-contained body:

```
═══════════════ SESSION HANDOFF ═══════════════
To:    <target label>
From:  <current session name> (<type>) — <slug>, branch <branch>
Items: <inbox IDs / story keys, or "none">

<self-contained body: what we're doing · key decisions · exact next action · guardrails · relevant paths/IDs>

═══════════════ END HANDOFF ═══════════════════
```

Format rules (from the SKILL section — apply them, do not re-explain them to the user):
- **Wrap the block in a fenced code block** so it gets the one-click copy button and exact-text fidelity.
- **If the body contains ``` fences** (bash, JSON, etc.), wrap the whole handoff in a **four-backtick** or `~~~~` outer fence so the inner fences survive.
- Keep the titled header and the `END HANDOFF` footer intact.

Precede the block with a one-line lead-in so it's obvious what to copy, e.g.:
`Copy the block below into the other session:`

### 4. Do Nothing Else

`handoff` **produces text only.** It writes no files, sends no messages, and does **not** touch `_active`, the session file, `_index.md`, `_history.md`, the inbox, or the worklog. The current session is completely unchanged. Delivery is the human's job (paste). If the user wants a *file-based* handoff on the same machine instead, point them at `/session:spawn` (stage a linked session) or `/session:inbox` (drop an item/note into a target inbox).
