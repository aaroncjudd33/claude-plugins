# @handle Tagging, Provenance & Attribution Format

Mechanics for handle tagging, the inbox/backlog entry header format, provenance rendering, the `updated-by`/`created-by` session-file fields, the listing renderer, the "mine" filter, and per-item attribution. Loaded on demand (the SKILL keeps a one-line pointer at § @handle Tagging).

Every entry written to shared files (history, inbox, backlog) must carry the current user's handle.

**Handle lookup order:**
1. `~/.claude/config/<slug>.json` → `handle` field (repo-based projects)
2. `~/.claude/plugins/user-config.json` → `user.handle`
3. Fallback: prefix of `user.email` (e.g., `ajudd@youngliving.com` → `ajudd`)

**History entry format** (new and going forward):
```
[YYYY-MM-DD @<handle>] <session-name> — <accomplished sentence>
```

**Inbox/backlog entry header format** (new and going forward):
```
## [YYYY-MM-DD @<handle>] from <slug> / <session-name> (<type>) — <description>
```
`<slug>` / `<session-name>` are the **source** repo slug and session (where the item came from — NOT the target inbox's slug). `<type>` is the source session type (`story` / `cab` / `plugin` / `personal` / `general`). Keep both repo AND session — never collapse to one. When writing, derive all three from the *source* session context (active session file frontmatter for type; `pwd` slug for the repo).

**Provenance rendering (layout B)** — how inbox items are *displayed* for pickup (session:start routing block, session:switch), with a single-line variant for the finish/checkpoint sweeps. Full spec + parsing/back-compat rules in `references/inbox-convention.md`. In short: **description leads**, provenance dimmed on a second line `↳ <slug> / <session> (<type>) · MM-DD`; **drop `<slug>` when it equals the current repo slug** (only cross-repo origins show it); tolerate legacy headers — spaced or unspaced `/`, and a missing `(<type>)` or missing slug render gracefully.

**`updated-by` field in session files** — written on every checkpoint/finish/commit/switch:
```
- **updated-by:** @<handle>
```
Position: in the session file body after `Name:`, before `Teams chat:`.

**`created-by` field in session files** — written once at session creation (start.md Step 8); preserved as-is on all subsequent writes (checkpoint/finish/commit/switch):
```
- **created-by:** @<handle>
```
Position: immediately after `updated-by:`. On migrate: seeded from the migrating user's handle (best available approximation — original authorship cannot be determined from local files). The combination of `created-by` + `updated-by` enables attribution display in listings. The default listing shows only `@updater` (the "last edit" column — the recency signal); the `created` column (`@creator` + created-date) is hidden by default and appears when the user types `full`.

## Listing Renderer

The session listing (session:start Step 2, session:switch) is rendered by `scripts/session-list.py`, not generated token-by-token by the model. The script reads `_index.md`, the per-session `_inbox_<name>.md` files, the `_active` marker, and the session `.md` filenames, then prints the finished, aligned, grouped table (default columns; `out`/`created` shown only on `full`; completed + `refinement-*` hidden by default; active marked `←`). Commands run it and **echo stdout verbatim**. Filter args: `--full`, `--show all|refinement`, `--status <value>`, `--mine`. It forces UTF-8 stdout (the `←` marker breaks Windows cp1252) and exits non-zero with empty stdout on any error so the command falls back to model rendering. **Do not re-inline listing formatting into the commands** — the script is the single source of truth; the in-command fallback is only for machines without python3.

## "Mine" Filter

Any listing command (start, switch, status, search) supports filtering sessions to those where `updated-by` matches `@<handle>`.

- Argument `mine` → filter immediately (e.g., `/session:start mine`)
- Without argument → show all sessions; if multiple developers' sessions are visible, add hint: "(type `mine` to filter to yours)"
- In filtered mode, show label: `(filtered to @<handle>)`

## Per-Item Attribution on Open Items and Next Steps

`Open items` and `Next steps` are arrays. Every item must carry `[YYYY-MM-DD @handle]`:

```markdown
- **Open items:**
  - [2026-06-11 @ajudd] Fix null check in processOrders
  - [2026-06-10 @hiranatam] Verify DynamoDB throughput before load test

- **Next steps:**
  - [2026-06-11 @ajudd] Deploy to env6 and run smoke tests
```

**`Next steps` replaces the old scalar `Next step` field.** On reading an old `- **Next step:** <text>` line, treat it as owned by the current handle and re-write as a `Next steps:` array item on the next write (checkpoint/finish/commit).

**Untagged items** (written before v1.36.0) are treated as owned by the current session's handle — backward compatible, re-tagged on next write.

**Resume block display:** Split into mine vs. teammate at display time:
```
Open items (mine, N):
  - [date @ajudd] ...

Teammate notes (N — read-only):
  - [date @hiranatam] ...
```

After displaying teammate notes, offer: `Adopt any teammate items as your own? (numbers, 'all', or 'skip')`.
Adopted items re-tagged: `[YYYY-MM-DD @<handle>] <text> (via @<original-handle>)`.
