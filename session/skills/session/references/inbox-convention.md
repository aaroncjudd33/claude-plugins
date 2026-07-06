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
## <id> · [YYYY-MM-DD @<handle>] from <source-slug> / <session-name> (<source-type>) — <short title>
> [type: story · status: ready]

<Context: what the item is, why it matters, what needs to happen.>
```

- `<id>` — the item's **stable, permanent handle** (e.g. `acp-ajudd#14`). Issued once at creation and never changes, even as positions shift. Form: `<acronym>-<handle>#<n>` (see Stable IDs below). Reference items by this ID in conversation and recaps — never by their shifting list position.
- `<source-slug>` — the originating **repo** slug (where the request came from, e.g. `virtual-office`, `gen-leadership-bonus`, a personal project), **NOT** the target inbox's slug. This matters because plugin suggestions often route in from cross-repo work.
- `<session-name>` — the originating session (e.g. `BPT2-6377`, a feature name).
- `<source-type>` — the **provenance** axis: the source session's type (`story` / `cab` / `plugin` / `personal` / `general`). This is the value that sits positionally inside `from … (<…>)`. It answers *where the item came from* — do **not** confuse it with the `type` field below (what the recipient does with it). It was previously called just "type"; it is relabeled `source-type` so the two never blur.
- **Keep both repo AND session — never collapse to one.** Derive all three from the *source* session context when routing.
- The `> [type: … · status: …]` line directly under the header carries the **message type** and **lifecycle status** (see Item Model below). It is optional for back-compat; when absent, defaults apply.

Keep it self-contained — the receiving session may pick this up weeks later with no memory of the source conversation.

## Item Model — three orthogonal axes

Every inbox item is described by **three independent axes**. Keep them separate — never collapse two into one field. (Metaphor: an inbox item is to a plugin/personal repo what a Jira story is to a work repo — the same object is both the **work-in-progress store** *and* the **final deliverable**. You write into it, iterate, and mark it ready; an implementation session then picks it up. A session file is only ever created for *work being done*, never for scoping the item itself.)

**1. `source-type` — provenance (where it came from).** The source session's type, tracked positionally in the header's `from <slug> / <session> (<source-type>)`. Values: `story` / `cab` / `plugin` / `personal` / `general`. Display-only; never gates behavior. (In-repo vs cross-repo is **derived** from `source-slug` vs the current slug — it is not a declared axis.)

**2. `type` — message type (what the recipient does with it).** The primary NEW field, carried on the `> [type: …]` line. Values:
- `story` *(default)* — actionable work; the Jira-story analog. Picked up and built/done. A **spawn** is a `story` tagged `[spawn]`, not its own type.
- `note` — awareness / FYI / recorded decision for another session; no build expected.
- `data` — a payload consumed as input to work (results, values, file refs, config).
- `question` *(deferred — not built in v1)* — would ask for a decision/input and expect a reply. Until it lands, a question is just a `note` and a reply is just another `note`; there is no reply-expected lifecycle.

> **`note` / `data` are live (acp-ajudd#10).** Their delivery behavior — the **mailbox** — is implemented: a session drops a `note`/`data` into another slug's inbox (free-rein write, visible confirmation), the human points the target session at it, and it reads → processes → **archives** on request. It is **human-driven**: Claude does NOT poll, monitor, or auto-announce mail; a single "N messages waiting" line at `session:start` is the only surfacing. Full flow in **§ Mailbox — note/data delivery** below.

**3. `status` — lifecycle. Which lifecycle depends on `type`:**
- **`story` → maturity lifecycle:** `refining` → `ready` → *(picked)* → done. `refining` = still being scoped/polished (the WIP-store phase); `ready` = matured enough for an implementation session to pick up. This mirrors a Jira story moving from *Gathering Requirements* → *Ready For Work*.
- **`note` / `data` → delivery lifecycle:** `new` (a.k.a. `unread`) → `consumed` → archived. Presence in the inbox IS the "sent/delivered" state; "ready" is implicit. On read, the target processes the message and **archives** it to `_inbox_archive.md` (see § Mailbox). (Mechanics: acp-ajudd#10.)

**Creator defaults:**
- `new <description>` quick-capture → `type: story · status: ready` (a captured task is immediately pickable).
- `refine` → `type: story · status: refining` (written early, matured over sessions, flipped to `ready` at graduation).
- `/session:inbox` handoff → `type: story · status: ready` unless the sender specifies `note`/`data`.
- spawn → `type: story · status: ready`, plus the `[spawn]` tag.

**Back-compat (verified against the existing inbox — no lockout):** the `> [type: … · status: …]` line is **optional**. A missing `type` defaults to `story`; a missing `status` defaults to `ready`. Items written before this model (no line at all) therefore read as `story` / `ready` — pickable exactly as before. Parse `type` and `status` independently: `> [status: refining]` alone is valid (type defaults to `story`), as is `> [type: note]` alone (status defaults per its lifecycle). Never break on an absent or partial line.

**Picking a `refining` story is guarded.** Because a `story` doubles as its own WIP store, a half-scoped item must be distinguishable from a ready one — that is exactly what `refining` vs `ready` encodes. `pick` on a `refining` item **warns and confirms** ("still being refined — pick it up anyway?") before folding it into a coding session.

## Mailbox — note/data delivery (acp-ajudd#10)

The inbox does two jobs. The **to-do list** job is `type: story` items you pick up and build (above). The **mailbox** job is `type: note` / `type: data` items — inter-session messages one session drops for another: a `note` ("heads up, I changed X") or `data` ("here are the values you need"). This section is the mailbox.

**The model: the human is the notifier.** Claude does **not** monitor, poll, or auto-announce mail. There is no hook watching the inbox and no mid-session "you have mail" surfacing. Mail moves only when a human coordinates it. Three phases:

**1. Write (silent to the recipient, visible to the sender).** A session drops a `note`/`data` into another slug's inbox via `/session:inbox` — a **free-rein write** (no propose→approve, per acp-ajudd#5) that surfaces a visible confirmation line *in the sending session* (`Sent inbox item <id> to <target> inbox`). The receiving side is not interrupted — nothing pings the target session.

**2. Coordinate (human).** The developer tells the target session where to look — "there's a note for you from `<repo>/<session>`, go read it," or just "check my inbox messages." Claude looks only when told. (The one automatic touch: a single **"N messages waiting"** count at `session:start` — see below — which is one read at a natural moment, not monitoring.)

**3. Read → process → archive (on request).** When asked, the target session:
   - reads every `type: note` / `type: data` item with `status: new` in its slug inbox (`_inbox.md` for plugin/personal; `_inbox.md` — the global slug inbox — for story/cab, *not* a per-session `_inbox_<name>.md`, since mail is addressed to the slug);
   - **processes** each: a `note` is read/acknowledged (fold any actionable follow-up into the session's own work or a new `story` item); a `data` payload is folded into the work that needs it;
   - **archives** each: append it to `_inbox_archive.md` with a `[CONSUMED YYYY-MM-DD]` stamp and remove it from the live inbox. Archiving behavior is unchanged from the existing `[DONE]` archive flow — same file, same auto-purge (>30d). Messages are **archived, never deleted.**
   - surface a one-line summary of what was consumed, e.g. `Consumed 2 messages (1 note, 1 data) → archived.`

**Addressing = to-slug (v1).** A message is addressed to a repo's inbox — whoever next works that slug — not to a specific named session. (`/session:inbox` already writes to the slug inbox for plugin/personal.)

**`data` payload — inline by default, optional `ref:`.** Small payloads go inline in the item body. For a large payload, put it in a file and reference it:
```markdown
## <id> · [YYYY-MM-DD @ajudd] from virtual-office / BPT2-6258 (story) — enrollment test IDs
> [type: data · status: new]
ref: ~/.claude/memory/sessions/ajudd-claude-plugins/_data_enrollment-ids.md
(inline summary: 12 member IDs for the reactivation smoke test — see ref for the full list)
```
When a `data` item has a `ref:`, the processing session reads the referenced file to get the payload. Inline is the default; `ref:` is only for payloads too big to sit in the inbox comfortably.

**Out of the pickup backlog.** `note`/`data` messages **never appear in the `story` pickup list** — they are not work to grab. The `session:start` pickup list shows only `type: story` items. The mailbox count is separate: a single line

```
Messages: N waiting (note/data) — say "check messages" to read them
```

shown once at `session:start` when any `type: note`/`type: data` item has `status: new`. Omit the line entirely when there are none. This is the only place mail surfaces on its own — one glance, no monitoring.

**`question` deferred.** Not built in v1. A note can carry a question; a reply is just another `note`. No reply-expected lifecycle yet.

## Writing records — free rein, never silent (acp-ajudd#5)

Records get written the way session files get written: **without asking.** An inbox item (and its work-repo analog, a Jira story) is *captured requirements and ideas — not code.* So planning/refinement and cross-session handoffs write and update them with **free rein** — no propose→approve ceremony, no one-record-per-session cap. Validation is the user's job **after the fact**: they read the record (the inbox item / Jira story) or trust the conversation it came from. This **reverses** an earlier "draft → show → approve → place" gate, which was rejected as friction on low-stakes captured intent.

**The one guardrail that survives — visible, not silent.** Every record write must **surface a confirmation line in the conversation as it happens**, exactly like a session-file write is visible. This is *not* an approval step; it is just "say you did it." The failure mode this prevents is the historical one where items were auto-filed at `finish` and never surfaced, so the user could not read them to validate. The rule is **"just do it, but say you did it"** — free rein plus a visible confirmation (leading with the item's `<id>`). A background write that never appears in the conversation is the one thing that is never allowed.

**Source of record — per zone (what you write to):**

| Zone (what repo am I in) | Source of record | Planning / refinement / handoff writes to |
|---|---|---|
| **Plugin marketplace** | inbox item (`_inbox.md` → file/git history) | the inbox item |
| **Personal** (`personalProjectsDir`) | inbox item (`_inbox.md` → file/git history) | the inbox item |
| **Work repo** (story/cab) | the **Jira story** | the Jira story |
| **General** | none assumed | ask once, then that target |

Rule of thumb: **what repo am I in → that's my source of record → I write to it freely, because updating it IS the work.**

**Two capabilities this enables:** (1) a single planning/refine session **creates and updates as many records as it needs** — no per-write approval, no cap; (2) **frictionless cross-repo capture from anywhere** — from any zone, fire an item into *another* repo's inbox with minimal ceremony (flagship: a plugin idea you had while working in a work repo → send it to the plugins inbox). Nothing gates these writes: inbox items live under `~/.claude/memory/`, and there is no edit-blocking hook (acp-ajudd#1) — you can capture into any repo's inbox without an active session of any kind.

**Where this shows up:** `session:inbox` (writes directly, then a `Sent inbox item <id> to <target> inbox` line), `refine` (writes early + on each edit, surfacing `Wrote/Updated <id>`), `new` (writes then immediately picks up — visible via the pickup), `spawn` (writes the `[spawn]` entry, confirms with `<id>`), and the `checkpoint`/`finish`/`commit` scope-routing handoffs (route through `session:inbox`, which surfaces the line). None of these gate the write; all of them surface it.

## Stable IDs

Every inbox item gets a **permanent, per-item handle** at creation, so it can be named consistently across its whole life instead of by a list position that shifts every time an item is added or folded. Applies to **all** project types (plugin / personal / work / general) — one universal scheme, no per-type branching.

**Form:** `<acronym>-<handle>#<n>` — e.g. `acp-ajudd#14`, `glb-nivi#7`, `vo-ajudd#3`.

- `<acronym>` — deterministic short code for the **home** slug (the repo whose inbox the item lives in — the target of a routed handoff, not the source). Derived by `scripts/inbox-id.py acronym --slug <slug>`: first letter of each token (split on `-`/`_`/camelCase), lowercased; single-token slugs use the first 3 chars. Same slug → same acronym on any machine, no config. So the number reflects that person's activity **in that repo**, and the ID reads as "who + what repo". The **session** lives on the provenance line, not in the ID — keeps the ID short and sayable.
- `<handle>` — the authoring user's handle. This **namespaces the counter per user**: `acp-ajudd#*` and `acp-nivi#*` are disjoint, so two developers can never collide on a number without any coordination.
- `<n>` — a monotonically-incrementing counter, per **(user, home-slug)**. Issued by `scripts/inbox-id.py next --slug <home-slug> --handle <handle>`, which increments and persists the counter.

**Counter storage — local, never in a repo.** `~/.claude/config/inbox-seq.json` (`{ "<slug>": <n>, ... }`) on the author's machine. Because the counter is never in the shared repo and is namespaced per user, there is nothing shared to merge-conflict on — the only shared artifact is the item text, whose ID is already unique by construction.

**Permanence.** An ID is assigned once and never reused or renumbered. Folding/deleting an item **retires** its ID; the counter never goes backward, so remaining items keep theirs and future items never reclaim a retired number.

**Generating an ID at write time** (any inbox write site):
```bash
IDT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}/scripts/inbox-id.py"
python3 "$IDT" next --slug "<home-slug>" --handle "<handle>"   # prints the ID and increments
```
Use `--peek` to preview the next ID without consuming it. If `python3` or the script is unavailable, fall back to `<acronym>-<handle>#?` and note that the counter could not be advanced (rare; degrade gracefully rather than block the write).

**Parser tolerance (back-compat).** The `<id> · ` prefix is **optional** in the header. Items created before this scheme (and archived items) have no ID — parse them exactly as before. When rendering, show the ID if present; omit the segment if absent. Never break on a missing ID.

**One-time migration.** Retro-assign IDs to a slug's current items in file (creation) order, then set the counter to the highest number issued:
```bash
python3 "$IDT" set --slug "<slug>" --value <highest-n>   # counter continues from here
```
Already-folded/archived items are not retro-assigned.

**Deferred (refine later):** acronym collisions across two different repos, and multi-user migration (assigning IDs to another author's existing items — their counter lives on their machine). Neither affects local/single-user use.

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
  1  [acp-ajudd#14]  <description>
     ↳ <slug> / <session> (<type>) · MM-DD
  2  [acp-ajudd#9]  ★ [spawn] <label>
     ↳ <slug> / <session> (<type>) · MM-DD
```
- **Description leads** — it's the decision driver when picking.
- **Stable ID before the description**, in `[ ]`. The leading `N` is the **ephemeral in-view position** (for `pick <n>` convenience); the `[<id>]` is the **permanent handle** — use it in conversation and recaps so references don't shift. `pick` accepts either (`pick 1` or `pick acp-ajudd#14`). Omit the `[<id>]` segment entirely for legacy items that have none.
- **Same-repo dimming:** when `<slug>` equals the current repo slug, **drop it** — show `↳ <session> (<type>) · MM-DD`. Only genuinely cross-repo origins show the slug, so they stand out.
- **Missing type:** omit the `(<type>)` segment; still show `↳ <slug> / <session> · MM-DD`.
- **Stale source session:** render as-is — historical provenance stays valid, and the description-first line keeps it from looking orphaned.

**Single-line form (finish/checkpoint sweeps — action prompts stay one line):** lead with the stable ID, then the quoted description and dim provenance, before the option list:
```
  [acp-ajudd#14] Inbox pending: "<description>"  ·  ↳ <session> (<type>)   nothing / done / picked-up
```
Drop the slug when same-repo (as above); include it (`↳ <slug> / <session> (<type>)`) for cross-repo items. Omit the `[<id>]` for legacy items with none.

## Item Lifecycle

Items move through three **pickup** states, all tracked inline in the inbox file. (These are orthogonal to the `type`/`status` axes above: pickup state = "has a session grabbed this yet"; maturity `status` = "is a `story` scoped enough to grab." A `refining` or `ready` story is both "pending" here; picking either one makes it in-progress. `refining` just means `pick` warns first.)

**Pending** — item has arrived, not yet picked up:
```markdown
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 (story) — Add /comms:pto command
> [type: story · status: ready]

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
