# Path Resolution

Mechanics for resolving `slug`, `session_root`, and `handle`. Loaded on demand by any session command flow that needs to locate session files (the SKILL keeps a one-line pointer at § Path Resolution).

**All session commands use this logic.** Do not hardcode `~/.claude/memory/sessions/<slug>/` — check for repo-based sessions first.

```
slug = basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
       ← the current repo's folder name (e.g. `ajudd-claude-plugins`).
       Run this command and use its output VERBATIM. Do NOT use the dashed
       project-directory name from your environment context / system reminders
       (e.g. `C--Users-ajudd--claude-plugins-marketplaces-ajudd-claude-plugins`)
       — that is Claude Code's mangled memory-path key, NOT the slug. It appears
       in the memory path in every system reminder and is a strong distractor.

repo_root = $(git rev-parse --show-toplevel 2>/dev/null) or pwd if not a git repo

if <repo_root>/.claude/sessions/ exists:
    session_root = <repo_root>/.claude/sessions/
    local_cfg    = ~/.claude/config/<slug>.json
    if local_cfg missing → run First-Run prompt (see below)
    handle = local_cfg.handle
else:
    session_root = ~/.claude/memory/sessions/<slug>/
    handle = user-config.json → user.handle (fallback: prefix of user.email)

Always local / never committed (gitignored in repo-based sessions — acp-ajudd#48/#49):
    _active        → ~/.claude/memory/sessions/<slug>/_active   (per-user pointer — always the local path)
    _context_*     → <session_root>/_context_*.md               (pre-clear / planning-resume stash — store + handoff)
    _history.md    → <session_root>/_history.md                 (worklog glimpse — duplicates the global worklog; created on demand)
    _index.md      → <session_root>/_index.md                   (listing render cache — see below)
    *.approved-hash → ~/.claude/memory/sessions/<slug>/*.approved-hash

Session index (DERIVED render cache — NOT committed; acp-ajudd#49):
    _index.md      → <session_root>/_index.md
                     One line per session (7 cols): `name | @created-by | created-date | @updated-by | updated-date | status | title`
                     Fully derivable from the committed `<name>.md` files' frontmatter/body — it is a cache, not source of truth.
                     Written by: start (seed on create; rebuild when absent — absence is normal), checkpoint/finish/commit/switch (update), migrate (warm the cache).
                     `session-list.py` reads each session file directly when a row is missing, so the listing renders correctly with NO committed index.
                     created-date/updated-date are ISO dates (YYYY-MM-DD); created-date is never overwritten after first write.
```

**Scope resolution for the scope guard:** If the session file's `Scope:` value is relative (no leading `/`, `~`, or drive letter), resolve it as `local_cfg.projectRoot + "/" + scope_value`. If absolute (old format), use as-is.

**Cross-repo inbox writes** (e.g., story plugin writing to release plugin inbox): substitute the target slug and re-run path resolution to find the target session_root.

**Inbox / Outbox file naming:**
- Per-session inbox (story / cab / general): `_inbox_<session-name>.md` — e.g., `_inbox_BPT2-6479.md`, `_inbox_release.md` (a single file per session)
- Consolidated / global inbox (plugin / personal, and the global inbox for other types): the per-item dir `_inbox/` — one file per item `_inbox/<id-with-#→->.md>` (acp-ajudd#102), read via `scripts/inbox-render.py`. A legacy single `_inbox.md` auto-migrates into this dir on first access.
- Archive (append-only): the single `_inbox_archive.md`
- Outbox (append-only send record): `_outbox_<session-name>.md`

All cross-session routing goes through `/session:inbox` — scope guards invoke it rather than writing directly.

**Shell portability (macOS/zsh):** Never iterate a bare filename glob that may match nothing — `for f in <dir>/_inbox*.md` aborts the whole command under zsh (macOS default shell) with "no matches found", which silently breaks listings. Always use a no-match-safe form: `find <dir> -maxdepth 1 -name '_inbox*.md' 2>/dev/null | while read -r f; do …; done`. Applies to every command that enumerates `_inbox*`, `_context_*`, `*.approved-hash`, or `refinement-*` files.

## First-Run Auto-Config

Triggered once per developer per repo-based project when `~/.claude/config/<slug>.json` is missing. **No prompt needed** — derive everything silently:

```
projectRoot = git rev-parse --show-toplevel   ← always known
handle      = user-config.json → user.handle  ← already in user-config
```

Write `~/.claude/config/<slug>.json`:
```json
{ "projectRoot": "<derived>", "handle": "<derived>" }
```

Then show a one-time notice: `"Repo sessions active for <slug> — local config written to ~/.claude/config/<slug>.json"`

Only ask for `handle` if `user-config.json` is completely absent (plugin not set up at all — uncommon edge case).
