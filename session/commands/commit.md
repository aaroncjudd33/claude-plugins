---
name: commit
description: Commit current work, update memory, and save session state. Mid-session save with a real git commit — no Jira, no Teams, no session deactivation. Pushes for story/cab/personal; plugin sessions commit locally only (the push is the finish deploy).
---

# Session Commit

Commit in-progress work, update memory, and save session state. Use this mid-session when you want your changes committed and context saved without closing out the session.

**Commit is the "iterate" stage of the lifecycle** (start = pick up · commit = iterate · finish = done). What it does with the commit depends on the environment:

| Type | Commit behavior |
|------|-----------------|
| story / cab / personal / general | Commit **and push** — the working branch is not the deployed artifact, so pushing WIP is safe and gives an off-machine backup. |
| **plugin** | Commit **locally only — never push.** For plugins, `master` **is** the deployed branch (reinstall pulls straight from it), so pushing unversioned WIP would let the marketplace pull half-finished work. The push happens exactly once, at `finish` (the deploy). Commit here is a private safety checkpoint. |

This is the polymorphic split: same command, environment-appropriate behavior. `commit` never bumps the version or reinstalls for any type — that is `finish`'s job for plugins.

## Instructions

### 0. Read Session Context

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (see Session Skill).

Determine the session name from conversation context:
1. Look for the most recent "Resuming `<name>`" line (from session:start) OR "Switching to `<name>`" line (from session:switch). Use whichever is most recent.
2. Fall back to reading `~/.claude/memory/sessions/<slug>/_active` if not in context.

**Session guard (command-level enforcement — acp-ajudd#1).** `commit` operates on the active session, so a session must exist. If neither the conversation context nor `~/.claude/memory/sessions/<slug>/_active` yields a session name, **stop cleanly** — do not ask, do not guess, do not proceed:

```
No session established for <slug>. Run /session:start first.
```

This is the whole enforcement model: editing files is never blocked, but the session commands refuse to run without a session. (`start` / `refine` and read-only views are exempt.)

Read `<session_root>/<name>.md` and extract all fields. Minimally:
- `type` (plugin / story / cab / personal / general)
- `name`
- `branch`
- `title` (story/cab only — may be absent in older session files; treat as empty)
- `category` (general only — may be absent)
- `teams_chat`
- `related_cab` (story only — may be absent)
- `post_deployment_checks` (story only — preserve entire block verbatim)
- `related_stories` (cab only — may be absent)
- `linked_sessions` (may be absent)
- `plugin_reviewed` (plugin only — may be absent)
- `loaded_memories` (may be absent — preserve as-is; written by the memory plugin)
- `commits` (may be absent — preserve existing entries; this command appends to it)

When writing the session file in Step 6, preserve all fields present in the existing file — do not drop any field that was read here.

### 1. Git Scan

| Type | Scope |
|------|-------|
| plugin | `~/.claude/plugins/marketplaces/<pluginMarketplaceName>` (read from user-config) |
| story | current working directory (work repo) |
| cab | current working directory |
| personal | current working directory |
| general | current working directory |

Run from the appropriate directory:

**Run all git checks in parallel:**

```bash
git status
git diff --staged
git diff
```

If there is nothing to commit (clean working tree, no staged changes): report "Git: nothing to commit" and skip to step 3.

If there are changes, continue to step 2.

### 2. Draft and Confirm Commit Message

Scan the staged and unstaged changes (`git diff HEAD`) to understand what changed. Draft a concise commit message following the repo's style (seen in recent `git log --oneline -5`).

**Determine push behavior from session type** (per the table above):
- **plugin** → commit **locally only, no push**. Prompt reads `Commit locally?`.
- **all other types** → commit **and push**. Prompt reads `Commit and push?`.

Show the drafted message using Pattern 4 (Generated Content Approval) — output and wait:

```
Commit message draft:
---
<drafted message>
---
Commit locally? (go / edit: <your message> / cancel)      ← plugin
Commit and push? (go / edit: <your message> / cancel)     ← story/cab/personal/general
```

- **go:** stage all changed files that belong to this session's scope (not `git add -A` blindly), then commit. **Push only for non-plugin types** — for plugin sessions, stop after the local commit (do NOT push).
- **edit: <message>:** use the user-provided message, then commit (and push per type, as above).
- **cancel:** stop here. Do not proceed to memory or session state steps.

Commit format:
```bash
git commit -m "$(cat <<'EOF'
<message>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

For non-plugin types, push after the commit (`git push`). For plugin types, do not run `git push` — the working commit stays local until the finish deploy.

**Committed-sessions discipline (acp-ajudd#48/#49 — see Session Skill § The committed-sessions model).** When staging for a **repo-based** session (`.claude/sessions/` is git-tracked):
- **Fold session state into the meaningful commit — no standalone `chore: session log` commits.** The derived caches (`_history.md`, `_index.md`) are gitignored and won't stage; the `<name>.md` state file rides along with the code change it describes, never as its own noise commit.
- **Never write another team's security findings, credentials, tokens, or PII into the session file or any committed record — reference by ticket/PR number.** The `session-commit-guard.py` pre-commit hook backstops this (it blocks staged session/memory files containing secret/PII patterns); if it blocks the commit, scrub the flagged content, don't bypass it.

**After committing — capture the commit reference** for the session record:
```bash
git rev-parse --short HEAD
git config --get remote.origin.url
```
Record the short SHA + the first line of the commit message. **For non-plugin types**, if a GitHub remote exists, derive a commit link `https://github.com/<org>/<repo>/commit/<sha>` from the remote URL (strip `.git`, convert `git@github.com:` form to `https://github.com/`). **For plugin types, record the SHA + subject without a link** — the commit is local and unpushed, so a commit URL would 404 until the finish deploy pushes it. This is written to the session file's `Commits:` field in Step 6.

### 2a. Jira Commit Comment *(story/cab only)*

Post a 1-line Jira comment summarizing what was just committed.

- **story:** story key = session name
- **cab:** post to each story in `Related stories`

Translate the commit message to business-readable language — status + milestone, no file paths, class names, or token names. Example: *"Committed touchToken fix for all 3 filter input types — testing in progress."*

Before posting, check if the most recent Jira comment already covers this commit — if so, skip.

**plugin / personal / general:** Skip.

### 3. History Entry

Compose a 1-sentence description of what was accomplished in this commit. Write it as a complete thought that stands alone without conversation context.

Append to `<session_root>/_history.md` (create the file if it does not exist, with header `# History — <slug>`):

```
[YYYY-MM-DD @<handle>] <session-name> — <accomplished sentence>
```

This entry becomes the value for `Last worked on` in the session file.

### 4. Memory

Review the conversation since the last checkpoint/commit for anything worth saving:
- Feedback, corrections, or rules established
- Workflow or convention changes
- Anything non-obvious that future sessions should know

Save what's missing. Report: "Saved: [list]" or "Memory: nothing new to save."

**Status → the session file, not other living docs (Session Skill § Record ownership).** Live/ephemeral status — dated events, test counts, blockers, next action — is recorded in the session file here. Do **not** mirror it into a contract/requirements record (spec, ADR, design doc, ticket body) on your own initiative; those are developer-owned and edited only on explicit direction. Link to the record; don't duplicate its content or push status into it.

### 5. Scope Check

Read the `Scope:` field from the session file. If the field is missing or the session type is `general`, skip this step.

If the scope value is relative, resolve it as: `local_cfg.projectRoot + "/" + scope_value` (read `local_cfg` from `~/.claude/config/<slug>.json`). For legacy sessions with absolute scope, use as-is.

Review file paths accessed or modified during this conversation. Any path not beginning with the resolved absolute scope is out-of-scope.

If out-of-scope work is found, warn but do not block. Display the out-of-scope items and output a routing line:

```
Out-of-scope work detected — will be excluded from this session record.

  Out-of-scope:
    · <file path>  (belongs in: <target slug> / <target session>)

  route  ·  note  ·  skip
```

- **route:** invoke `/session:inbox` flow with the out-of-scope item pre-populated. Choosing `route` IS the go-ahead — `/session:inbox` writes directly and surfaces the `Sent inbox item <id> to <target> inbox` line (free rein + visible, never silent — acp-ajudd#5; no separate pre-write approval).
- **note:** note in session Open items but do not write to any inbox.
- **skip:** continue without noting.

### 6. Session State

**Before writing — tag any untagged items:** For each Open item that does not already start with `[YYYY-MM-DD @`, prepend `[today @<handle>] `. Preserve existing tags as-is.

Write `<session_root>/<name>.md` with current state:

```
---
updated: [today's date]
---

# Session State — <name>

- **Type:** [type]
- **Name:** [name]
- **updated-by:** @<handle>
- **created-by:** @<original-handle>   ← read from existing file; preserve as-is — never overwrite
- **Title:** [Jira summary]   ← story/cab only; omit for other types
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Scope:** [scope path]   ← preserve from existing file; write relative if new; omit for general
- **Status:** in-progress
- **Branch:** [branch or "n/a"]
- **Last worked on:** [most recent entry from _history.md — do not synthesize, read from file]
- **Open items:**
  - [YYYY-MM-DD @<handle>] <item text>   ← all items tagged; "none" if empty
- **Next steps:**
  - [YYYY-MM-DD @<handle>] <next step>   ← array format; "none" if no next step
- **Loaded memories:**   ← preserve existing entries; omit the field if none. Written by the memory plugin (/memory:load|scan|save)
  - <name>  [<label>]
- **Commits:**   ← append the commit captured in Step 2; preserve prior entries; omit the field if none
  - [YYYY-MM-DD] <short-sha> — <commit subject>   ← append "  <link>" if a GitHub remote was derived
- **Plugin reviewed:** <version>   ← plugin type only; write current plugin.json version when marking reviewed; omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Post-deployment checks:**   ← story type only; preserve existing value exactly as-is; omit if field not present
  - [ ] <check description>
  - [x] <acknowledged check description>
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
- **linked_sessions:** [<session-name>, ...]   ← preserve as-is; omit if not present
```

**Backward compat:** If the existing session file has a `Project:` field, preserve it on write. If the existing file has `- **Next step:** <text>` (scalar), re-write as `- **Next steps:**` array with the item tagged `[today @<handle>]`.

**`Commits:` field:** Append the commit captured in Step 2 as a new line under `- **Commits:**` (create the field if absent, positioned after `Next steps:`). Keep prior commit lines — this is an append-only running list for the session. Cap display at the most recent 10; if older entries exist, keep them in the file. If nothing was committed this run (clean tree), leave the field unchanged.

**After writing — update approved-hash (repo sessions only):** If `session_root` is inside a repo, recompute and overwrite `~/.claude/memory/sessions/<slug>/<name>.approved-hash`:
```bash
python3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "<session_root>/<name>.md" > ~/.claude/memory/sessions/<slug>/<name>.approved-hash
```

**Update `_index.md`:** Read `<session_root>/_index.md` — create with header if not exists. Find the line for `<name>`: extract `@created-by` (col 2) and `created-date` (col 3) to preserve; if no existing line, use `@<handle>` and `<today>`. Replace or append: `<name> | @<created-by> | <created-date> | @<handle> | <today> | in-progress | <title-or-dash>`.

Print the summary to screen.

### 7. Work Log

Append to `~/.claude/memory/worklog/<YYYY-MM-DD>.md` (create the file and `~/.claude/memory/worklog/` directory if they don't exist).

Use today's date for the filename. Use the current local time (HH:MM) for the entry header.

Entry format varies by type:

- **story/cab with title:** `## <HH:MM> — <name> — <title> (<type>)`
- **story/cab without title** (older session files): `## <HH:MM> — <name> (<type>)`
- **plugin:** `## <HH:MM> — <name>` (no type label — the name is self-identifying)
- **personal/general:** `## <HH:MM> — <name> (<type>)`

```markdown
## <HH:MM> — <formatted header per above>

**Accomplished:** <most recent entry from _history.md>

**Open items:** <open items from session state, or "none">
```

Multiple entries per day are expected — always append, never overwrite.
