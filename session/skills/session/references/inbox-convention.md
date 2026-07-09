# Project Inbox Convention

How to leave cross-session or cross-project work items for a plugin or session you're not currently working in.

## Location

**Canonical (current model): one consolidated inbox per slug.**

`~/.claude/memory/sessions/<repo-slug>/_inbox.md`

This single file is THE inbox for the slug. `/session:start` reads it and the plugin/personal flow `code`s records from it (the old `pick` — acp-ajudd#56) — at graduation, the item body is folded into the new feature session and the item is archived-on-consume (a `[CONSUMED …]` copy is appended to `_inbox_archive.md`, then the item is removed from the live inbox — acp-ajudd#40). For the plugin marketplace, slug = `ajudd-claude-plugins`; for a personal project, slug = that project's directory name. Plugin and personal behave identically.

Routing a handoff to a **plugin or personal** slug always targets this consolidated `_inbox.md` (not a per-target file) — see `/session:inbox`. **story / cab** sessions still use a per-session file `_inbox_<key>.md` (e.g. `_inbox_BPT2-6479.md`), since each story/CAB is its own external unit of work.

**Legacy (historical, back-compat only — do not write new items here):**

Before the item-driven-sessions overhaul, multi-plugin repos used one inbox file *per plugin* — `_inbox_session.md`, `_inbox_release.md`, `_inbox_comms.md`, `_inbox_docs.md`, `_inbox_e2e.md`, `_inbox_links.md`, `_inbox_setup.md`, `_inbox_story.md`. These files (and their `_archive`/`_backlog` siblings) are left in place as history. The listing renderer still reads them for legacy sessions, but the new flow never writes to them. New items always go to the consolidated `_inbox.md` above.

## Entry Format

```markdown
## <id> · [YYYY-MM-DD @<handle>] from <source-slug> / <session-name> (<source-type>) — <short title>
> [status: capture]

<Context: what the item is, why it matters, what needs to happen.>
```

- `<id>` — the item's **stable, permanent handle** (e.g. `acp-ajudd#14`). Issued once at creation and never changes, even as positions shift. Form: `<acronym>-<handle>#<n>` (see Stable IDs below). Reference items by this ID in conversation and recaps — never by their shifting list position.
- `<source-slug>` — the originating **repo** slug (where the request came from, e.g. `virtual-office`, `gen-leadership-bonus`, a personal project), **NOT** the target inbox's slug. This matters because plugin suggestions often route in from cross-repo work.
- `<session-name>` — the originating session (e.g. `BPT2-6377`, a feature name).
- `<source-type>` — the **provenance** axis: the source session's type (`story` / `cab` / `plugin` / `personal` / `general`). This is the value that sits positionally inside `from … (<…>)`. It answers *where the item came from*. (It was once called just "type"; it is named `source-type` to keep it distinct from the item's lifecycle `status` — the old recipient-facing `type` axis was removed in acp-ajudd#21.)
- **Keep both repo AND session — never collapse to one.** Derive all three from the *source* session context when routing.
- The `> [status: …]` line directly under the header carries the item's **lifecycle status** (`capture` → `refining` → `ready`) plus an **optional `intent:` hint** (see Item Model below). It is optional for back-compat; when absent, defaults apply.

Keep it self-contained — the receiving session may pick this up weeks later with no memory of the source conversation.

## Item Model — captures on one lifecycle (acp-ajudd#21)

> **This supersedes the v1.57.0 "three orthogonal axes" model.** The old `type` axis (`story` / `note` / `data`) is **gone**. There is no message-type field anymore — an inbox holds **captures**, and every capture moves along **one lifecycle**. Back-compat for the old syntax is spelled out at the end of this section.

**An inbox holds captures.** A **capture** is raw inbound — *provenance known, intent deferred*. It's whatever arrived: a plugin idea fired in from another repo, a heads-up from a sibling session, a payload of values, a half-formed task. You don't classify it at write time; you **disposition it on read**. (Metaphor: an inbox item is to a plugin/personal repo what a Jira story is to a work repo — once promoted, the same object is both the **work-in-progress store** *and* the **final deliverable**: you write into it, iterate, mark it ready, and an implementation session picks it up. A session file is only ever created for *work being done*, never for scoping the item itself.)

**One lifecycle:**

```
capture  ──(promote)──▶  refining  ──▶  ready  ──▶  [picked up → coding session]
   │
   └──(disposition on read)──▶  discard  ·  absorb into current session  ·  feed a refinement   → archived
```

- **`capture`** — the single entry state. *Everything* starts here (this is what note/data + unclassified ideas all become). Provenance is recorded; intent is deferred to the reader.
- **promote** — a refine/planning read decides "this is real work" and moves the capture into the story track (`status: refining`), right in the inbox. Promotion is a status flip, not a move to a different file.
- **`refining`** — a promoted capture being scoped/polished (the WIP-store phase). **`ready`** — scoped enough for an implementation session to pick up. This mirrors a Jira story moving *Gathering Requirements → Ready For Work*.
- **"story" is not a type — it's a promoted capture.** A capture that has been promoted into `refining`/`ready` is *tracked work* (the Jira-story analog). "Story" names that stage, not a separate kind of item. A **spawn** is a promoted (`ready`) capture tagged `[spawn]`.
- **A capture that is *not* promoted is dispositioned on read** — one of: **discard** (drop it), **absorb into the current session** (fold its content into the work you're doing now), or **feed a refinement** (hand it to a refine pass to shape into work). All three end **archived** — a capture whose fate is read-and-archive. *This is what the old `note`/`data` items become.*

**Provenance is a required attribute; intent is an optional hint.**
- **Provenance** (where/who it came from) is always recorded — the header's `from <slug> / <session> (<source-type>)` plus the author `@handle` and date. `source-type` (`story` / `cab` / `plugin` / `personal` / `general`) is display-only and never gates behavior; in-repo vs cross-repo is *derived* from `source-slug` vs the current slug.
- **Intent** is an **optional, non-binding hint** the sender may attach — `· intent: <hint>` on the status line. It tells the reader what the sender *thinks* the capture is, without deciding for them:
  - `intent: story` — "this looks like real work" (the old `story` signal)
  - `intent: fyi` — "awareness only, no build expected" (the old `note` signal)
  - `intent: data` — "a payload to consume as input" (the old `data` signal)
  When absent, the reader infers from the content. Intent **never binds** — the reader always dispositions.

**The status line:** `> [status: <capture|refining|ready>]`, with an optional intent hint: `> [status: capture · intent: fyi]`. Parse `status` and `intent` independently; both are optional.

**Creator defaults** (the model — the command wiring lands in acp-ajudd#22/#23):
- `/session:inbox` handoff / any cross-repo capture → `status: capture` (+ optional `intent:` hint from the sender). This one path replaces the old note/data *and* story/ready handoff defaults — everything arrives as a capture.
- `refine` → creates/promotes at `status: refining` (written early, matured over sessions, flipped to `ready` at graduation). Refine is also where an existing `capture` gets **promoted**.
- spawn → `status: ready`, plus the `[spawn]` tag (a spawn stages a follow-on coding session, so it's inherently promoted work).

(The old start-screen `new <description>` — create-at-`ready`-and-code-immediately — is **retired** under acp-ajudd#56's two-verb model: new work is `refine`d into a record first, then `code`d when ready. Directly-`ready` records now come only from a refine graduation or a spawn, not a one-shot create-and-code gesture.)

**`code`-ing a not-yet-`ready` capture is guarded, not blocked.** Because a promoted capture doubles as its own WIP store, a half-scoped item must be distinguishable from a ready one — that is what `capture`/`refining` vs `ready` encodes. `code` on a `capture` or `refining` record **warns and confirms** ("not fully scoped — you'll scope *and* build; refine first if it's big") before folding it into a coding session. It **never blocks** — a capable coding session decides based on size. A `ready` item codes clean.

**Back-compat (verified against the existing inbox — no lockout).** The `> [status: …]` line is **optional**, and legacy `> [type: … · status: …]` lines still parse:
- **No line at all** (pre-model items) → reads as **`ready`** — pickable exactly as before.
- **Legacy `type: story`** → a **promoted capture** at its existing `status` (`refining`/`ready`); the `type` word is ignored.
- **Legacy `type: note`** → a **capture** with `intent: fyi`. **Legacy `type: data`** → a **capture** with `intent: data`.
- **Legacy statuses:** `new`/`unread` → `capture`; `refining`/`ready` → unchanged; `consumed` → already dispositioned (archived).
- Parse `status` and `intent` independently; never break on an absent, partial, or legacy line. **No migration of existing files** — old items read correctly in place.

## Captures inbound — reading and dispositioning (acp-ajudd#10)

The inbox does two jobs, and both are now the *same object* at different lifecycle stages. The **to-do list** job is promoted captures (`refining`/`ready`) you pick up and build (above). The **captures-inbound** job is un-promoted `capture` items — raw inbound one session drops for another (a heads-up, a payload of values, a stray idea). This section is that inbound read flow. *(It was previously called the "mailbox" for `note`/`data` items; the behavior is identical — only the framing changed: there is no note/data type, just captures awaiting disposition.)*

**The model: the human is the notifier.** Claude does **not** monitor, poll, or auto-announce inbound captures. There is no hook watching the inbox and no mid-session "you have mail" surfacing. Captures move only when a human coordinates it. Three phases:

**1. Write (silent to the recipient, visible to the sender).** A session drops a capture into another slug's inbox via `/session:inbox` — a **free-rein write** (no propose→approve, per acp-ajudd#5) that surfaces a visible confirmation line *in the sending session* (`Sent inbox item <id> to <target> inbox`). The receiving side is not interrupted — nothing pings the target session.

**2. Coordinate (human).** The developer tells the target session where to look — "there's a capture for you from `<repo>/<session>`, go read it," or just "check my captures." Claude looks only when told. (The one automatic touch: a single **"N captures waiting"** count at `session:start` — see below — which is one read at a natural moment, not monitoring.)

**3. Read → disposition → archive (on request).** When asked, the target session:
   - reads every un-promoted `capture` (`status: capture`) in its slug inbox (`_inbox.md` for plugin/personal; `_inbox.md` — the global slug inbox — for story/cab, *not* a per-session `_inbox_<name>.md`, since captures are addressed to the slug);
   - **dispositions** each — **promote** (it's real work → flip to `refining`, hand to refine or scope inline), or one of the read-and-archive fates: **discard**, **absorb into the current session** (fold its content — e.g. a data payload or an FYI — into the work at hand), or **feed a refinement**;
   - **archives** each non-promoted capture with the **bucket-3 planning-disposition stamp** `[DISPOSITIONED YYYY-MM-DD — <fate>]` (`<fate>` is one of `discarded` / `absorbed` / `refined` — see § Disposition & completion): append it to `_inbox_archive.md` and remove it from the live inbox. This is a **non-completion** stamp — dispositioning a capture on read is *not* completing implemented work (only a coding `/session:finish` writes `[DONE]`), and it is *not* a pickup-consume (that is `[CONSUMED → session]`). Same file and same auto-purge (>30d) as the `[DONE]` flow. Captures are **archived, never deleted** (a promoted capture stays live in the inbox at `refining`/`ready`). *(Legacy captures archived with a bare `[CONSUMED YYYY-MM-DD]` still read correctly as historical dispositions — see § Disposition & completion back-compat.)*
   - surface a one-line summary, e.g. `Read 2 captures — 1 promoted to refining, 1 absorbed → dispositioned.`

**Addressing = to-slug (v1).** A capture is addressed to a repo's inbox — whoever next works that slug — not to a specific named session. (`/session:inbox` already writes to the slug inbox for plugin/personal.)

**Payloads — inline by default, optional `ref:`.** A small payload goes inline in the capture body. For a large payload, put it in a file and reference it:
```markdown
## <id> · [YYYY-MM-DD @ajudd] from virtual-office / BPT2-6258 (story) — enrollment test IDs
> [status: capture · intent: data]
ref: ~/.claude/memory/sessions/ajudd-claude-plugins/_data_enrollment-ids.md
(inline summary: 12 member IDs for the reactivation smoke test — see ref for the full list)
```
When a capture has a `ref:`, the reading session reads the referenced file to get the payload. Inline is the default; `ref:` is only for payloads too big to sit in the inbox comfortably.

**Two lists at `session:start`, one object.** Un-promoted captures **never appear in the pickup list** — they are not yet work to grab; they surface only as a glance count. The `session:start` pickup list shows only promoted captures (`refining`/`ready`). The captures-inbound count is separate: a single line

```
Captures waiting: N — say "check captures" to read them
```

shown once at `session:start` when any `status: capture` item exists. Omit the line entirely when there are none. This is the only place inbound captures surface on their own — one glance, no monitoring.

**`question` deferred.** Not built in v1. A capture can carry a question; a reply is just another capture. No reply-expected lifecycle yet.

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

## State-exclusivity — a live item OR a consumed session, never both (acp-ajudd#13)

Free rein (above) governs *how* records get written — no approval ceremony. This section governs the relationship between a **live inbox item** and the **coding session** that builds it. It **replaces the old "planning edits in place, coding must not touch the record" role rule** — that rule tried to keep a coding session from mutating requirements by *forbidding* it; state-exclusivity makes the concern structurally impossible instead. It is a **documented convention, instruction-only — there is no guard or hook** (a record-layer hook would reintroduce exactly the file-edit policing acp-ajudd#1 removed, and would gate the `~/.claude/memory/` tier we deliberately keep free; it would also be trivially bypassed by a plain session). The invariant holds by construction, not by policing.

The record layer = inbox items (their body / requirements / acceptance criteria) and their work-repo analog, Jira stories.

**The invariant: a given piece of work is EITHER a live inbox item OR a consumed coding session — never both at once.**

- **A coding session *may* edit a live inbox item.** While an item is still in the inbox, editing its body is just **planning-in-the-moment** — free-rein, exactly like `refine`. There is no "coding sessions can't touch requirements" prohibition; a coding session acting as planning is fine.
- **Picking up an item consumes it — fold-then-archive (acp-ajudd#40).** The pickup folds the item body into the session file and **removes** the item from the *live* inbox — appending a `[CONSUMED <date> → session <name>]` copy to `_inbox_archive.md` first, as a recovery net (preserving its stable `<id>` in the session's provenance block). After that there is **no live item left to edit** — the requirement now lives, and evolves, in the session. So the work can never exist as *both* a divergent live item and an in-flight session: consuming is what makes it session-only. This is **self-enforcing** — nothing needs to forbid double-editing because there is only ever one live copy. The archived copy is **history, not a second live record**, and the `<id>` is **retired, never reused**, so archiving does not reintroduce a competing copy.
- **Jira stories keep the "locked once *In Progress*" rule.** A Jira story is **not consumable** — you can't fold-then-archive it — so the exclusivity invariant can't be enforced structurally for stories. Instead, `/story:update` **locks the description once the story moves to *In Progress***, which achieves the same "requirements don't drift mid-build" outcome by a lock rather than by deletion. The exclusivity-by-consumption invariant is therefore **inbox-native only**; stories get the lock as their equivalent.

What a coding session **still does freely**: write/update its **own session file**; **post NEW inbox items** — cross-session handoffs (`/session:inbox`), spawns, and inbound captures. Posting new captures is unrelated to the invariant (it creates fresh items, it doesn't fork an in-flight one).

(A `refining`→`ready` **status flip** and the fold-then-archive on pickup are not "forking the work" — they're the normal lifecycle. The thing state-exclusivity rules out is a live item and a session both claiming the *same* work and drifting apart.)

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
if command -v python3 >/dev/null 2>&1; then python3 "$IDT" next --slug "<home-slug>" --handle "<handle>"; else python "$IDT" next --slug "<home-slug>" --handle "<handle>"; fi   # prints the ID and increments
```
The `python3 -> python` fallback matters on Windows Git Bash, where only `python` may be on PATH — without it every mint silently degrades to the `#?` placeholder. Use `--peek` to preview the next ID without consuming it. If **neither** `python3` nor `python` (nor the script) is available, fall back to `<acronym>-<handle>#?` and note that the counter could not be advanced (rare; degrade gracefully rather than block the write).

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
- **Stable ID before the description**, in `[ ]`. The leading `N` is the **ephemeral in-view position** (for `code <n>` convenience); the `[<id>]` is the **permanent handle** — use it in conversation and recaps so references don't shift. `code` accepts either (`code 1` or `code acp-ajudd#14`). Omit the `[<id>]` segment entirely for legacy items that have none.
- **Same-repo dimming:** when `<slug>` equals the current repo slug, **drop it** — show `↳ <session> (<type>) · MM-DD`. Only genuinely cross-repo origins show the slug, so they stand out.
- **Missing type:** omit the `(<type>)` segment; still show `↳ <slug> / <session> · MM-DD`.
- **Stale source session:** render as-is — historical provenance stays valid, and the description-first line keeps it from looking orphaned.

**Single-line form (finish/checkpoint sweeps — action prompts stay one line):** lead with the stable ID, then the quoted description and dim provenance, before the option list:
```
  [acp-ajudd#14] Inbox pending: "<description>"  ·  ↳ <session> (<type>)   nothing / done / picked-up
```
Drop the slug when same-repo (as above); include it (`↳ <slug> / <session> (<type>)`) for cross-repo items. Omit the `[<id>]` for legacy items with none.

## Disposition & completion — three stamps, three owners (acp-ajudd#42)

When an item leaves the live inbox it gets an archive stamp. There are **three distinct stamps and they must never be blurred** — each answers a different question and only some actors may write each. The rule that matters most: **"complete" means *implemented*, and only a coding session's `/session:finish` may say it.** A planning / refine / sessionless read may create, refine, delete, backlog, or set-aside an item freely — it may do everything *except* mark it complete.

| Stamp | Bucket | Means | Written by |
|---|---|---|---|
| `[DONE YYYY-MM-DD]` | **1 — COMPLETION** | the work is *implemented and closed* | **ONLY a coding session's `/session:finish`** (or a coding `checkpoint` closing its own picked-up work). Never a planning/refine/sessionless read. |
| `[CONSUMED YYYY-MM-DD → session <name>]` | **2 — CONSUMED-ON-PICKUP** | the item was *folded into a coding session* — **taken, not done** | **ONLY a coding session, at pickup** (acp-ajudd#40). The `→ session <name>` suffix is what marks it as a pickup-consume, not a completion. |
| `[DISPOSITIONED YYYY-MM-DD — <fate>]` | **3 — PLANNING DISPOSITION** | a *non-completion* fate applied on read: `<fate>` is one of `discarded` / `absorbed` / `refined` / `superseded` | a read that decides not to build the item as-is — typically a **planning / refine / sessionless** read, but a coding session reading a capture it won't build also dispositions it. **Never means implemented.** |

**Why the split (the live incident).** A planning context once archived an audit-index capture with a `[CONSUMED … shipped]` stamp while that item still had open children — using a completion word for something it had no authority to complete. Bucket 3 exists so a planning read has a stamp that says "handled, not built": it reads as non-completion at a glance and can never be mistaken for `[DONE]`.

**Backlog is a move, not a stamp.** "Move to backlog" relocates the item to `_backlog*.md` (bucket-3 non-completion, nothing archived); it is deferral, not completion. Deleting a backlog item is a permanent drop — still never a completion.

**Back-compat (existing archives stay readable).** Legacy `[DONE]` and legacy bare `[CONSUMED YYYY-MM-DD]` (no `→ session`, written by the old captures-inbound disposition flow) both still parse — treat a bare `[CONSUMED]` with no `→ session` suffix as a historical bucket-3 disposition, not a pickup-consume or a completion. No migration; old stamps read in place.

**Parent / index items close bottom-up.** A capture that spawned children — an **audit index** that maps findings to child items (e.g. `A1 → #36`, `D10 → #40`) is the canonical case — is **not complete until its implemented children are complete**. Each child is closed by *its own* coding session's `/session:finish` (bucket 1); only once every implemented child is `[DONE]` may the parent index be marked `[DONE]`. A planning/refine read **must never self-complete a parent** while children remain open — doing so is exactly the completion-without-authority the whole rule forbids. Until then the index stays live (at `refining`/`ready`), ideally carrying an explicit "stays live until children close" note and a child→status map so the open work is legible. (This is the rule the live incident violated: an index was archived `[CONSUMED … shipped]` by planning while its children were still in flight.)

## Item Lifecycle (pickup states)

Pickup state is **orthogonal to the maturity `status` above**: `status` = "is this capture promoted and scoped enough to grab" (`capture` → `refining` → `ready`); pickup state = "has a session grabbed it yet." A `refining` or `ready` item is "pending" here; `code`-ing either makes it in-progress (`capture`/`refining` just means `code` warns first).

**Two pickup mechanisms, by inbox kind:**
- **Item-driven consolidated inbox (plugin / personal — `_inbox.md`):** pickup **consumes** the item — **fold-then-archive** (state-exclusivity, above): the body folds into the session file, a `[CONSUMED <date> → session <name>]` copy is appended to `_inbox_archive.md` as a recovery net, and the item is removed from the *live* inbox. It never sits at "in-progress" in the inbox; it's gone from the live inbox the moment it's picked up, and the session (with the archived copy as a backstop) is the paper trail.
- **Per-session inbox (story / cab — `_inbox_<name>.md`):** pickup inserts an **in-progress marker** and the item **stays** in the inbox until done, then archives. This is the pending → in-progress → done flow below.

**Pending** — item has arrived, not yet picked up:
```markdown
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 (story) — Add /comms:pto command
> [status: ready]

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

**Done** — work **implemented and complete** (bucket 1 — see § Disposition & completion). This stamp asserts the work was *built*, so it is written **only by a coding session's `/session:finish`** (or a coding `checkpoint` closing its own picked-up work) — never by a planning/refine/sessionless read. The item is removed from inbox and appended to the archive file (`_inbox_<name>_archive.md` or `_inbox_archive.md`) with a `[DONE]` stamp:
```markdown
[DONE 2026-06-05]
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 (story) — Add /comms:pto command
[Work file: _work_session_2026-06-05-comms-pto.md]   ← preserved if one was created
```
(The pickup archive above uses the distinct bucket-2 stamp `[CONSUMED <date> → session <name>]` — *taken, not done*. A planning read that decides not to build an item uses the bucket-3 `[DISPOSITIONED …]` stamp or moves it to backlog — never `[DONE]`.)

## Triage Options (at session:start / checkpoint / finish)

Each verb maps to a disposition bucket (§ Disposition & completion). Only **Mark done** carries a completion semantic, and it is gated to a coding session.

- **Work on it** — inserts `[in-progress — <session>, <date>]` in the inbox entry, adds `[inbox] <item>` to session Open items. Does NOT archive yet.
- **Mark done** (bucket 1 — COMPLETION) — archives with `[DONE]` stamp, removes from inbox. **Only valid from a coding session closing work it actually built** (this is why the prompt appears at `checkpoint`/`finish`, which require a coding session). **A planning / refine / sessionless read must not use this** to clear an item it merely judged obsolete — that is a planning disposition: use **Move to backlog** (defer) or a bucket-3 `[DISPOSITIONED … — superseded]` archive (drop), never `[DONE]`.
- **Move to backlog** (bucket 3 — planning disposition, non-completion) — moves to `_backlog_<name>.md` (plugin) or `_backlog.md` (others). No archive — stays until explicitly deleted. Available to any read, planning included.
- **Keep** — leaves as-is in inbox. Does not add to Open items.

## Auto-Purge

At session:start, archive entries with `[DONE YYYY-MM-DD]` older than 30 days are dropped automatically. `[in-progress]` markers and backlog entries are never auto-purged.
