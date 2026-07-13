---
name: store
description: Dump volatile in-session reasoning to a context file before running /clear, so /session:restore can fully restore working context without re-explanation.
---

# Session Store

Captures everything held in conversation that isn't in persistent files — reasoning chains, confirmed facts, decisions and why, rejected options, open questions, key code/values — into a named `_context_<session-name>.md` file. That file **is** the handoff: `store` tells you its name and exactly how to pick it up on return, so restoring is an explicit named-file load — no hidden markers, no guessing which session was active.

Run this **before** `/clear`. After `/clear` (or from a fresh terminal), run `/session:restore <session-name>` to restore.

## Instructions

### 1. Identify Current Session

Read current session from conversation context (most recent `session:start` output — "Resuming `<name>`"). If not found in context, read `~/.claude/memory/sessions/<slug>/_active` as a fallback.

Resolve the repo slug as `basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"` and use that output verbatim. **Do NOT use the dashed project-directory name from your environment context** (e.g. `C--Users-ajudd--...`) — that is Claude Code's mangled memory-path key, not the slug. Resolve `session_root` using Path Resolution (`references/path-resolution.md`).

**Session guard (command-level enforcement — acp-ajudd#1).** `store` dumps the active session's working context, so a session must exist. If neither the conversation context nor `~/.claude/memory/sessions/<slug>/_active` yields a session name, **stop cleanly**:

```
No session established for <slug>. Run /session:start first.
```

Editing files is never blocked; the session commands are what require a session. (`start` / `refine` and read-only views are exempt.)

### 2. Dump Context File

Write the context file **always to the local path** `~/.claude/memory/sessions/<slug>/_context_<session-name>.md` — regardless of whether the session is repo-based or local. A restore point is a **personal, ephemeral, local stash** ("git stash for session context"), treated exactly like `_active`: never checked into a repo, never migrated, never shared. (This is why it is safe to hold raw pre-clear reasoning — it never travels.)

```markdown
# Pre-Clear Context — <session-name>
Generated: <YYYY-MM-DD HH:MM>

## Problem Being Solved Now
<One paragraph — what are we trying to accomplish in this exact moment>

## Confirmed Facts
- <fact confirmed this session — source or evidence>
- ...

## Decisions Made This Session
- <decision> — **Why:** <reasoning>
- ...

## Rejected Options
- <option> — **Why rejected:** <reason>
- ...

## Open Questions
- <question not yet resolved>
- ...

## Key Code / Values / Names
- <file path, function name, value, or identifier that matters>
- ...

## Exact Next Action
<The most granular possible next step — more specific than the session file's Next step field>
```

Focus on the volatile reasoning layer — things that are true NOW in this conversation that aren't captured in the session file, inbox, or memory. Do not repeat information already in those files.

**Never write secrets or PII into the context file.** The file is always local and never committed or migrated, so it does not travel — but keep it clean anyway: local session dumps are still the highest-density collection of raw working state on the machine, and pointers restore context just as well. In the "Key Code / Values / Names" section especially: do **not** paste credentials, passwords, DB connection strings, API keys, tokens, private keys, or real-person PII (a person's name paired with a member/custid, `fedTaxNum`, SSN, addresses). Instead, write a **pointer** to where the value lives — e.g. "Oracle Clone/env6 creds: see global `reference_oracle_environments.md`" or "test member: custid in global accounts store". A pointer restores context just as well on resume, without writing the secret to a file that travels.

### 2a. Secrets & PII Guard (before write — BLOCKING)

Before writing the context file, scan the composed content for the same secrets/PII patterns the commit guard uses (`SECRET_PATTERNS` in `session-commit-guard.py`): DB connection strings with passwords (`user/PASS@host:port`), `password=`/`token=`/`api_key=` assignments, `AKIA…` keys, JWTs, `-----BEGIN … PRIVATE KEY-----`, and `fedTaxNum`/`ssn`/`taxId` PII fields, plus any real name↔custid pairing.

If anything matches, **redact it before writing** — replace with a placeholder + pointer:
- secrets → `<REDACTED — see <source>>` (or just `<REDACTED>`)
- PII → `<test-member>` / `<custid>`

Then report what was scrubbed:
```
Scrubbed before writing context (kept out of _context_<name>.md):
  - db-connection-credentials ×2 → replaced with pointer to reference_oracle_environments.md
  - name↔custid "Edie Wadsworth / 1443424" → <test-member>
```
This stops secrets at the source — they never reach disk in the context file. The context file is local-only (never committed or migrated), so this write-time scan is its **only** line of defense — the commit guard and migrate scan never see it. That is exactly why the scan here is BLOCKING.

### 3. Update Session Status

In `<session_root>/<session-name>.md`, update the `Status` field to `prepare-clear`. If the field does not exist, add it after the `Branch` line.

### 4. Confirm to User

The context file name is the handoff — name it explicitly and tell the user exactly how to pick it up on return. No marker is written; restore is always by explicit name.

Print:

```
Saved context to _context_<name>.md — <N> sections captured

When you're back (after /clear, or from a fresh terminal), run:
  /session:restore <name>

Run /clear now.
```

The `/session:restore <name>` invocation is the pick-up instruction — it works identically after a `/clear` in this terminal or from a brand-new session later, because it loads the named `_context_<name>.md` + session file directly rather than relying on any transient marker or on `_active` still pointing at this session.
