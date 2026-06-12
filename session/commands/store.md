---
name: store
description: Dump volatile in-session reasoning to a context file before running /clear, so /session:restore can fully restore working context without re-explanation.
---

# Session Store

Captures everything held in conversation that isn't in persistent files — reasoning chains, confirmed facts, decisions and why, rejected options, open questions, key code/values — into `_context_<session-name>.md`. Then writes a `_resume_<session-name>` marker so `/session:restore` can find this session immediately after `/clear`.

Run this **before** `/clear`. After `/clear`, run `/session:restore` to restore.

## Instructions

### 1. Identify Current Session

Read current session from conversation context (most recent `session:start` output — "Resuming `<name>`"). If not found in context, read `~/.claude/memory/sessions/<slug>/_active` as a fallback.

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` using Path Resolution (see Session Skill).

### 2. Dump Context File

Write `<session_root>/_context_<session-name>.md` (goes to repo if repo-based — useful for teammates to see the pre-clear reasoning state):

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

**Never write secrets or PII into the context file.** This file may be committed to the repo (when repo-based) and is copied verbatim by `/session:migrate` — it is the single highest-risk leak path. In the "Key Code / Values / Names" section especially: do **not** paste credentials, passwords, DB connection strings, API keys, tokens, private keys, or real-person PII (a person's name paired with a member/custid, `fedTaxNum`, SSN, addresses). Instead, write a **pointer** to where the value lives — e.g. "Oracle Clone/env6 creds: see global `reference_oracle_environments.md`" or "test member: custid in global accounts store". A pointer restores context just as well on resume, without writing the secret to a file that travels.

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
This stops secrets at the source — they never reach disk in the context file, so there is nothing for migrate or the commit guard to catch later. Those remain the backstops; this is the front line.

### 3. Write Resume Marker

Write `~/.claude/memory/sessions/<slug>/_resume_<session-name>` (always local — never in repo; plain text, just the session name, no extension):

```
<session-name>
```

This is the durable per-user signal that survives `/clear`. `/session:restore` scans `~/.claude/memory/sessions/<slug>/` for `_resume_*` files.

### 4. Update Session Status

In `<session_root>/<session-name>.md`, update the `Status` field to `prepare-clear`. If the field does not exist, add it after the `Branch` line.

### 5. Confirm to User

Print:

```
Ready to /clear

  Session:    <name>
  Context:    _context_<name>.md — <N> sections captured
  Marker:     _resume_<name> written

Run /clear now. When you're back, run /session:restore to restore full context.
```
