# Project Inbox Convention

How to leave cross-session or cross-project work items for a plugin or session you're not currently working in.

## Location

**Canonical (current model): one consolidated inbox per slug.**

`~/.claude/memory/sessions/<repo-slug>/_inbox.md`

This single file is THE inbox for the slug. `/session:start` reads it and the plugin/personal flow `pick`s items from it — at pickup, the item body is folded into the new feature session and the item is deleted (no archive). For the plugin marketplace, slug = `ajudd-claude-plugins`; for a personal project, slug = that project's directory name. Plugin and personal behave identically.

Routing a handoff to a **plugin or personal** slug always targets this consolidated `_inbox.md` (not a per-target file) — see `/session:inbox`. **story / cab** sessions still use a per-session file `_inbox_<key>.md` (e.g. `_inbox_BPT2-6479.md`), since each story/CAB is its own external unit of work.

**Legacy (historical, back-compat only — do not write new items here):**

Before the item-driven-sessions overhaul, multi-plugin repos used one inbox file *per plugin* — `_inbox_session.md`, `_inbox_release.md`, `_inbox_comms.md`, `_inbox_docs.md`, `_inbox_e2e.md`, `_inbox_links.md`, `_inbox_setup.md`, `_inbox_story.md`. These files (and their `_archive`/`_backlog` siblings) are left in place as history. The listing renderer still reads them for legacy sessions, but the new flow never writes to them. New items always go to the consolidated `_inbox.md` above.

## Entry Format

```markdown
## [YYYY-MM-DD @<handle>] from <source-slug> / <session-name> (<type>) — <short title>

<Context: what the item is, why it matters, what needs to happen.>
```

- `<source-slug>` — the originating **repo** slug (where the request came from, e.g. `virtual-office`, `gen-leadership-bonus`, a personal project), **NOT** the target inbox's slug. This matters because plugin suggestions often route in from cross-repo work.
- `<session-name>` — the originating session (e.g. `BPT2-6377`, a feature name).
- `<type>` — the source session type: `story` / `cab` / `plugin` / `personal` / `general`.
- **Keep both repo AND session — never collapse to one.** Derive all three from the *source* session context when routing.

Keep it self-contained — the receiving session may pick this up weeks later with no memory of the source conversation.

## Provenance Rendering (layout B)

How inbox items are **displayed** for pickup. Applies to the session:start routing block and session:switch listing (two-line form), and to the finish/checkpoint inbox sweeps (single-line form). Parse the header before rendering.

**Parsing the source (`from <slug> / <session> (<type>)`):**
- Tolerate both spaced `slug / session` and unspaced `slug/session`.
- `(<type>)` is **optional** — legacy items omit it. If absent, render without the `(<type>)` segment.
- If only a bare `<source>` is present (oldest items, no `/`), treat it as the session with no slug.
- Never break on a malformed header — degrade to showing whatever is present.

**Two-line form (pick lists — the default):**
```
Inbox — pick up or describe new work (N):
  1  <description>
     ↳ <slug> / <session> (<type>) · MM-DD
  2  ★ [spawn] <label>
     ↳ <slug> / <session> (<type>) · MM-DD
```
- **Description leads** — it's the decision driver when picking.
- **Same-repo dimming:** when `<slug>` equals the current repo slug, **drop it** — show `↳ <session> (<type>) · MM-DD`. Only genuinely cross-repo origins show the slug, so they stand out.
- **Missing type:** omit the `(<type>)` segment; still show `↳ <slug> / <session> · MM-DD`.
- **Stale source session:** render as-is — historical provenance stays valid, and the description-first line keeps it from looking orphaned.

**Single-line form (finish/checkpoint sweeps — action prompts stay one line):** append the dim provenance after the quoted description, before the option list:
```
  (N) Inbox pending: "<description>"  ·  ↳ <session> (<type>)   nothing / done / picked-up
```
Drop the slug when same-repo (as above); include it (`↳ <slug> / <session> (<type>)`) for cross-repo items.

## Item Lifecycle

Items move through three states, all tracked inline in the inbox file:

**Pending** — item has arrived, not yet picked up:
```markdown
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 (story) — Add /comms:pto command

Add a `/comms:pto` command...
```

**In-progress** — session picked it up, work is underway. A marker is inserted after the `## [date]` header:
```markdown
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 (story) — Add /comms:pto command
[in-progress — session, 2026-06-04]
[Work file: _work_session_2026-06-04-comms-pto.md]   ← optional, for deep items

Add a `/comms:pto` command...
```

The item stays in the inbox file until work is complete. A matching `[inbox] Add /comms:pto command` line is added to the session's Open items.

**Done** — work complete. Item is removed from inbox and appended to the archive file (`_inbox_<name>_archive.md` or `_inbox_archive.md`) with a `[DONE]` stamp:
```markdown
[DONE 2026-06-05]
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 (story) — Add /comms:pto command
[Work file: _work_session_2026-06-05-comms-pto.md]   ← preserved if one was created
```

## Triage Options (at session:start / checkpoint / finish)

- **Work on it** — inserts `[in-progress — <session>, <date>]` in the inbox entry, adds `[inbox] <item>` to session Open items. Does NOT archive yet.
- **Mark done** — archives with `[DONE]` stamp, removes from inbox.
- **Move to backlog** — moves to `_backlog_<name>.md` (plugin) or `_backlog.md` (others). No archive — stays until explicitly deleted.
- **Keep** — leaves as-is in inbox. Does not add to Open items.

## Auto-Purge

At session:start, archive entries with `[DONE YYYY-MM-DD]` older than 30 days are dropped automatically. `[in-progress]` markers and backlog entries are never auto-purged.
