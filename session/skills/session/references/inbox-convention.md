# Project Inbox Convention

How to leave cross-session or cross-project work items for a plugin or session you're not currently working in.

## Location

`~/.claude/memory/sessions/<repo-slug>/_inbox_<target>.md`

The `<target>` segment identifies exactly what receives the item:

- **Multi-plugin repos** (e.g. `ajudd-claude-plugins`): one file per plugin — `_inbox_session.md`, `_inbox_release.md`, etc.
- **Single-purpose repos**: use `_inbox.md` (no suffix needed).

For `ajudd-claude-plugins`, the full set of inbox files:

```
_inbox_comms.md
_inbox_docs.md
_inbox_e2e.md
_inbox_links.md
_inbox_release.md
_inbox_session.md
_inbox_setup.md
_inbox_story.md
```

If a change touches two plugins, split it into two entries and cross-reference each.

## Entry Format

```markdown
## [YYYY-MM-DD @<handle>] from <source-slug> / <session-name> — <short title>

<Context: what the item is, why it matters, what needs to happen.>
```

Keep it self-contained — the receiving session may pick this up weeks later with no memory of the source conversation.

## Item Lifecycle

Items move through three states, all tracked inline in the inbox file:

**Pending** — item has arrived, not yet picked up:
```markdown
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 — Add /comms:pto command

Add a `/comms:pto` command...
```

**In-progress** — session picked it up, work is underway. A marker is inserted after the `## [date]` header:
```markdown
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 — Add /comms:pto command
[in-progress — session, 2026-06-04]
[Work file: _work_session_2026-06-04-comms-pto.md]   ← optional, for deep items

Add a `/comms:pto` command...
```

The item stays in the inbox file until work is complete. A matching `[inbox] Add /comms:pto command` line is added to the session's Open items.

**Done** — work complete. Item is removed from inbox and appended to the archive file (`_inbox_<name>_archive.md` or `_inbox_archive.md`) with a `[DONE]` stamp:
```markdown
[DONE 2026-06-05]
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 — Add /comms:pto command
[Work file: _work_session_2026-06-05-comms-pto.md]   ← preserved if one was created
```

## Triage Options (at session:start / checkpoint / finish)

- **Work on it** — inserts `[in-progress — <session>, <date>]` in the inbox entry, adds `[inbox] <item>` to session Open items. Does NOT archive yet.
- **Mark done** — archives with `[DONE]` stamp, removes from inbox.
- **Move to backlog** — moves to `_backlog_<name>.md` (plugin) or `_backlog.md` (others). No archive — stays until explicitly deleted.
- **Keep** — leaves as-is in inbox. Does not add to Open items.

## Auto-Purge

At session:start, archive entries with `[DONE YYYY-MM-DD]` older than 30 days are dropped automatically. `[in-progress]` markers and backlog entries are never auto-purged.
