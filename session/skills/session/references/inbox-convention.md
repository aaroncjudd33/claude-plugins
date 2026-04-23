# Project Inbox Convention

How to leave cross-session or cross-project change instructions for a repo you're not currently working in.

## Location

`~/.claude/memory/sessions/<repo-slug>/_inbox_<target>.md`

The `<target>` segment identifies exactly what receives the change:

- **Multi-plugin repos** (e.g. `ajudd-claude-plugins`): one file per plugin name — `_inbox_e2e.md`, `_inbox_comms.md`, `_inbox_session.md`, etc. Direct 1:1 mapping between inbox files and plugins.
- **Single-purpose repos**: use `_inbox.md` (no suffix needed).

For `ajudd-claude-plugins`, the full set of inbox files is:

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

**Never write to a combined or global inbox for a multi-plugin repo.** If a change touches two plugins (e.g. e2e + session), split it into two entries — one per plugin file — and add a cross-reference note to each.

## Format

Each inbox entry is a dated H2 section:

```markdown
## YYYY-MM-DD from <source-project> session — <short title>

**Action required — <type of change>.**  (or "No action needed — state update only.")

<context: what's broken and why>

### Proposed Fix
<specific steps, file names, line numbers if known>
```

## When to Use

- You're in Project A and notice Project B needs a code or config change
- You're doing setup/analysis and identify a plugin bug
- A session produces a side-effect change in another plugin the owner should know about

## When Working in a Repo

At session start, check only `_inbox_<plugin>.md` for the current plugin — the mapping is 1:1. Mark completed items done with the date resolved.
