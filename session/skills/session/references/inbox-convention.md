# Project Inbox Convention

How to leave cross-session or cross-project work for a plugin or session you're not currently working in.

> **Terminology (see SKILL.md § Terminology — acp-ajudd#64).** A **terminal** is a Claude Code conversation; a **coding session** is the file-backed work unit (`<name>.md`). This doc uses "the receiving session" for whichever role picks an entry up — `refine`, `dispatch`, or a `code` session — and reserves the qualified "coding session" for the file-backed unit. No plugin or command is renamed.

## Location

**Canonical (current model): one consolidated inbox per slug, stored one file per item (acp-ajudd#102).**

`~/.claude/memory/sessions/<repo-slug>/_inbox/<id>.md`  — one file per item

The consolidated inbox for a slug is a **directory** — `_inbox/` — holding **one file per item** (`_inbox/<id>.md`), mirroring how session files already work. The single `_inbox.md` file is **retired** for the live inbox: it is auto-migrated into the per-item dir on first access (below) and never written again. `/session:start` reads it (via the render helper) and the plugin/personal flow `code`s `work` from it (the old `pick` — acp-ajudd#56) — at graduation, the body is folded into the new feature session and consumed-on-pickup (a `[CONSUMED …]` copy is appended to `_inbox_archive.md`, then the item **file is deleted** — acp-ajudd#40). For the plugin marketplace, slug = `ajudd-claude-plugins`; for a personal project, slug = that project's directory name. Plugin and personal behave identically.

**Why per-item (acp-ajudd#102).** The single `_inbox.md` was safe only while one role wrote it. That invariant was relaxed on purpose — `refine` authors, `dispatch` authors no-refinement splits (#95), `code` posts new items, and `capture` (#96) appends — so multiple legitimate concurrent writers now exist. A shared single file means a full-file rewrite by one writer can clobber another's just-appended item. **One file per item makes the destructive read-modify-write race structurally impossible for the common case: two sessions on DIFFERENT items touch DIFFERENT files.** (Same-item concurrency — two sessions editing the *same* item — remains possible but rare; accept last-writer-wins + re-read-before-write, add a per-file lock only if it bites.)

Routing a handoff to a **plugin or personal** slug always targets this consolidated `_inbox/` (not a per-target file) — see `/session:inbox`. **story / cab** sessions still use a per-session file `_inbox_<key>.md` (e.g. `_inbox_BPT2-6479.md`), since each story/CAB is its own external unit of work — those are **unchanged** (one writer per session, no race). The story/cab/general **global** inbox is the same per-item `_inbox/` dir (for undirected/cross-cutting items and spawn targets).

### Per-item storage mechanics (acp-ajudd#102)

**Filename.** The id with `#`→`-`, e.g. item `acp-ajudd#97` → `_inbox/acp-ajudd-97.md`. The file holds the item verbatim — the canonical `## acp-ajudd#97 · …` header, its `> [type: … · status: …]` line, any `> [depends-on: …]` line, and the freeform body — **no** `# Inbox` header and **no** trailing `---` separator (those belong to the rendered stream, not the stored item). A legacy item with no id maps to a deterministic `legacy-<hash>.md`.

**Reading — always through the render helper (`scripts/inbox-render.py`).** Never read the item files ad hoc; run the helper, which (1) auto-migrates on access (below) and (2) concatenates `_inbox/*.md` (sorted by numeric id) into the exact `_inbox.md`-shaped stream you already parse — `## <id> · …` headers, `> [type: …]` lines, bodies, `---`-separated. Parse its **stdout** exactly like the old `_inbox.md`. The migration notice, if any, is on **stderr** — relay it to the user, never fold it into the parsed content.
```bash
RENDER="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}/scripts/inbox-render.py"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
"$PY" "$RENDER" render --session-root "<session_root>" --slug "<slug>"   # stdout = the inbox stream to parse
# modes: `render` (default, prints the stream) · `ensure` (migrate only, no stream) · `count` (prints "work=N capture=M")
```
If neither `python3` nor `python` (nor the script) is available, fall back to reading `_inbox/*.md` directly (glob the dir; if it's absent, read a legacy `_inbox.md` if one is still present) — the read must always degrade, never block.

**In-flight display — consumed items still in a live session (acp-ajudd#99).** The render helper also answers "what happened to this item?" without any role narrating it (§ Role-scoped reporting). `inbox-render.py in-flight` reads `_inbox_archive.md`, finds every block stamped `[CONSUMED … → session <name>]`, and prints the ones whose session is **still in-progress** as in-flight rows — they **drop off** when the session finishes (a line-leading `[DONE]` stamp lands, or the session leaves in-progress; the session-status check is authoritative, so a legacy consumed block whose session finished long ago without a re-stamp still correctly drops off). Display-only; nothing prints when nothing is in flight. Wire it into the board (dispatch) and the in-flight/listing views so concurrent state is legible at a glance.
```bash
"$PY" "$RENDER" in-flight --session-root "<session_root>" --slug "<slug>"   # stdout = in-flight rows (empty when none)
```

**State-exclusivity anomaly scan — read-time, warn-only (acp-ajudd#99).** The one cross-role fact any role surfaces regardless of focus is a #13 violation (§ State-exclusivity). `session-list.py` runs a cheap check on its `--rebuild-index` read — an id present **both** live (`_inbox/<id>.md`) **and** in `_inbox_archive.md` stamped `[CONSUMED]`/`[DONE]` (line-leading stamps only — a body merely *quoting* `[done]` never arms it) — and emits a `⚠ state-exclusivity (#13): <id> is live … AND archived …` line. **Warn only, never auto-fix** (which copy is authoritative isn't machine-decidable). Shares the read-time health surface with #114's encoding detect-warn — both are backstops that catch what slips past the discipline, not the discipline itself.

**Writing — one item file at a time (this is what kills the race).** There is no write-through script; a command writes/edits/deletes exactly ONE `_inbox/<id>.md` file:
- **Create a new item** (`/session:inbox`, `refine`, `spawn`, `capture`) → mint the id (`inbox-id.py`), then **write** `_inbox/<id-with-#→->.md>` containing the item block (header + `> [type: …]` line + body). Create the `_inbox/` dir if needed (`mkdir -p`).
- **Edit an item in place** (refine iterate / promote / mark-ready; checkpoint/switch mark in-progress) → edit **only** that item's `_inbox/<id>.md` file.
- **Consume / complete / disposition** → append the item to `_inbox_archive.md` (or move to `_backlog*.md`) as before, then **delete** `_inbox/<id>.md`. Removing one item is deleting one file — it can never disturb another item.

**UTF-8-safe I/O — mandatory for every session/inbox/archive write (acp-ajudd#114).** These files are UTF-8 and routinely carry `·` / `—` / `→` glyphs (headers, provenance rendering, stamps). Write and edit them **only** with UTF-8-safe tooling — the Read/Edit/Write tools, Python `open(..., encoding='utf-8')`, or bash — and **never** through PowerShell 5.1 `Set-Content` / `Get-Content -Raw`. The reason is a silent corruption: PS 5.1 `Get-Content -Raw` reads a BOM-less UTF-8 file as cp1252, and `Set-Content -Encoding UTF8` then rewrites that misread string double-encoded **and** prepends a BOM — mojibaking every non-ASCII glyph in the file. Observed live 2026-07-14 corrupting `_inbox/acp-ajudd-107.md` and `-109.md` (repaired via a Python cp1252→utf8 reversal). With per-item storage (#102) and multiple terminals editing, any PS 5.1 read-modify-write silently mangles the file. If PowerShell genuinely must touch one of these files, use `[System.IO.File]::ReadAllText(path)` / `[System.IO.File]::WriteAllText(path, text, (New-Object System.Text.UTF8Encoding $false))` (the `$false` = no BOM) — not the 5.1 cmdlets. `session-list.py` carries a detect-and-warn backstop (auto-strips a lone BOM; flags mojibake markers for manual repair, never auto-reversing), but that only catches slips — the discipline above is the actual fix.

**Auto-migration — lazy, self-healing, race-safe (built into the render helper).** `inbox-render.py` runs `ensure_inbox_migrated()` at the top of **every** access (render / ensure / count), so it fires on ANY inbox read — start / refine / dispatch / capture / finish / checkpoint / switch / in-flight / search — not tied to one command (going straight to `/session:dispatch` can't skip it). It detects a legacy `_inbox.md` with item content while `_inbox/` is unpopulated, splits each item into its own file **behind the same O_EXCL advisory lock `inbox-id.py` uses** (re-checked inside the lock, idempotent — two sessions detecting at once → one migrates, the other no-ops), retires the legacy `_inbox.md`, and prints a one-line stderr notice `Migrated inbox to per-item storage (N items). Other terminals on the prior version must restart before touching this inbox.` (the coordinated-restart line — acp-ajudd#110, mirroring the deploy-time notice for the same migrated-data / old-code split). A fresh/empty repo (no `_inbox.md`, no items) is a silent no-op. `/session:migrate` (local→repo) still carries the inbox and remains an explicit fallback, but is no longer required to trigger this conversion.

**Legacy (historical, back-compat only — do not write new entries here):** before the item-driven-sessions overhaul, multi-plugin repos used one inbox file *per plugin* — `_inbox_session.md`, `_inbox_release.md`, etc. These (and their `_archive`/`_backlog` siblings) are left in place as history; the new flow never writes to them.

## Entry Format

```markdown
## <id> · [YYYY-MM-DD @<handle>] from <source-slug> / <session-name> (<source-type>) — <short title>
> [type: work · status: new]
> [depends-on: <id> — <reason>]        ← optional; see § Sequencing
<Context: what it is, why it matters, what needs to happen.>
```

- `<id>` — the entry's **stable, permanent handle** (e.g. `acp-ajudd#14`). Issued once at creation and never changes, even as positions shift. Form: `<acronym>-<handle>#<n>` (see Stable IDs below). Reference entries by this ID in conversation and recaps — never by their shifting list position.
- `<source-slug>` — the originating **repo** slug (where the request came from, e.g. `virtual-office`, a personal project), **NOT** the target inbox's slug. This matters because plugin suggestions often route in from cross-repo work.
- `<session-name>` — the originating session (e.g. `BPT2-6377`, a feature name).
- `<source-type>` — the **provenance** axis: the source session's type (`story` / `cab` / `plugin` / `personal` / `general`). It sits positionally inside `from … (<…>)` and answers *where the entry came from*. (It is named `source-type` to keep it distinct from the entry's own `type` — the `work`/`capture` label below.)
- **Keep both repo AND session — never collapse to one.** Derive all three from the *source* session context when routing.
- The `> [type: … · status: …]` line directly under the header carries the entry's **type** (`work` / `capture`) and, for `work`, its **lifecycle status** (`new` → `refining` → `ready`). See the Inbox Model below. It is optional for back-compat; when absent, defaults apply.
- The optional `> [depends-on: <id> — <reason>]` line declares a **sequencing prerequisite** — this entry must not be picked up until `<id>` is done. See § Sequencing.

Keep it self-contained — the receiving session may pick this up weeks later with no memory of the source conversation.

## Inbox Model — two types: `work` and `capture` (acp-ajudd#62)

> **This restores a lightweight, visible type** (superseding the single-lifecycle "everything is a capture" model of acp-ajudd#21, which had removed the type axis entirely). The type is now shown at a glance and answers one question — *build it, or read it?* Back-compat for the older syntax is spelled out at the end of this section.

> **Definitions live in SKILL.md § Terminology (the canonical glossary — acp-ajudd#70).** `work`, `capture`, and the `new → refining → ready` maturity lifecycle are *defined* there in one line each; this section owns their **mechanics** — the entry format, the status line, labeling, and back-compat parsing. Don't re-derive what the words mean here; point to the glossary.

**An inbox holds `work` and `captures`.** The type is a **lightweight, visible label** — nothing more. It is deliberately *not* heavy per-type command branching (that was the old complexity we don't want back).

*(One-line recap of the glossary above, then the mechanics — this section deliberately does not re-derive the definitions.)*

- **`work`** — carried through the `new → refining → ready` lifecycle and **picked up with `code`** (the buildable unit; a Jira story is its work-repo form — see glossary). The umbrella nouns "story" / "record" / "item" are **retired** for it (acp-ajudd#62).
- **`capture`** — **read / absorb / disposition** on sight, or **promote to `work`** if it turns out to be real work. It has **no build-lifecycle** — not scoped, dispositioned on read.

**No sub-labels.** Do NOT distinguish note vs message vs data, or story vs spec vs requirement. The only distinction that changes *handling* is **work (build it) vs capture (read it)** — the sub-labels are near-synonyms with identical handling, so they add zero value today. Add one back only if a real handling difference ever appears.

**The lifecycle is work-only:**

```
work:     new  ──▶  refining  ──▶  ready  ──▶  [picked up → coding session]
capture:  (no lifecycle)  ── read ──▶  promote to work · discard · absorb · feed a refinement  → archived
```

- **`new`** — work that exists but isn't being scoped yet (freshly-dropped work, or a promoted capture before refinement starts). This is the **renamed raw stage** — the word that used to be `capture` when `capture` was a lifecycle stage (acp-ajudd#62 resolves that collision: `capture` is now a *type*, so the raw *stage* is renamed `new`).
- **`refining`** — work being actively scoped by `refine`.
- **`ready`** — scoped enough for a coding session to pick up. `code` it.
- A **capture** carries no `status` — it is just a `capture` until dispositioned or promoted to `work`.

**"story" is not a type — it's work in a work repo.** A Jira story is work's work-repo form; an inbox `work` entry is work's plugin/personal form. Same concept, two homes. A **spawn** is `ready` work tagged `[spawn]`.

**Labeling — sender declares, else infer-and-confirm (acp-ajudd#62):**
- **The sender declares the type.** The sending session knows its own intent: "here's work to build" → `work`; "here's info for you" → `capture`. Told, not guessed (same principle as dispatch role determination).
- **When unspecified, infer from content and show the label to confirm** — spec/acceptance-criteria-shaped → `work`; "FYI / here's what happened / here's the data" → `capture`. **Declared intent wins**; content-inference is the low-friction default, surfaced for correction.

**The status line:** `> [type: work · status: <new|refining|ready>]` for work; `> [type: capture]` for a capture (no `status` — no lifecycle). Parse `type` and `status` independently; both tolerate absence (see back-compat).

**Creator defaults** (where each write site lands):
- `/session:inbox` handoff → the sender declares `work` or `capture` (unspecified → infer-and-confirm). A capture arrives as `> [type: capture]`; a declared work handoff arrives as `> [type: work · status: new]`.
- `refine` → creates/promotes `work` at `> [type: work · status: refining]` (matured to `ready` at graduation). Refine is also where a `capture` gets **promoted** to `work`.
- spawn → `> [type: work · status: ready]` plus the `[spawn]` tag (a spawn stages a follow-on coding session — inherently ready work).

**Back-compat (verified against the existing inbox — no lockout, no migration).** The `> [type: … · status: …]` line is **optional**, and every earlier syntax still parses:
- **No line at all** (pre-model entries) → reads as **`type: work · status: ready`** — pickable exactly as before.
- **Old `> [status: capture]`** (the retired raw/un-promoted *stage*) → **`type: capture`**.
- **Old `> [status: refining|ready]`** → **`type: work`** at that stage.
- **Old `> [type: story · status: …]`** → **`type: work`** at that status; the word `story` is dropped.
- **Old `> [type: note …]` / `> [type: data …]`** → **`type: capture`** (the info type).
- **Old `intent:` hint** (`intent: story` / `fyi` / `data`) → the **retired sub-label**; `intent: story` reads as `type: work`, `intent: fyi` / `intent: data` read as `type: capture`. No new entry writes `intent:` — the `work`/`capture` type carries the only distinction.
- **Old statuses:** `new`/`unread` → `type: capture`; `consumed` → already dispositioned (archived).
- **No `depends-on` line** → no declared prerequisite; the entry is independently dispatchable (the common case).
- Parse independently; never break on an absent, partial, or legacy line.

## Sequencing — the `depends-on` marker (acp-ajudd#67)

Some `work` must land in order — a page-refresh that publishes a model can't run until the model's vocab has shipped; a command that reads a marker can't be built until the marker is defined. Before acp-ajudd#67 that ordering lived **only in prose**, so nothing stopped an entry being pulled early: acp-ajudd#60 was dispatched and drafted before its prerequisite #62 landed, then had to be stood down mid-flight (the HALT detour — see SKILL § HALT). The fix makes the ordering **machine-visible** and gives `dispatch` a rule to honor it.

**The marker.** A `work` entry that must not be picked up before another entry is done carries an optional line directly under its `> [type: …]` line:

```markdown
> [depends-on: acp-ajudd#67 — #65 publishes the model; if #67 adds HALT/depends-on vocab, #65 must carry it. Sequence: #66 -> #67 -> #65.]
```

- **`<id>`** — the prerequisite entry's stable handle (one or more, comma-separated). Reference by the permanent `<acronym>-<handle>#<n>`, never a list position.
- **`— <reason>`** — a short human-readable why, so a person reading the inbox understands the ordering without reconstructing it. Optional but strongly encouraged.
- **Optional and back-compatible** — no line means no declared prerequisite (the common case). Parse it independently of `type`/`status`; never break on its absence.
- **`refine` writes it; `dispatch` reads it.** The `refine` role (the inbox author) adds the marker when it scopes work it knows is ordered. `dispatch` consults it when deciding what to pull (below). A coding session may add one to a *live* (pre-conversion) entry, same as any other body edit.

**Dispatch prereq-check rule — an entry with an unmet dependency is NOT dispatchable.** Before `dispatch` pulls or bundles a `ready` entry, it checks the entry's `depends-on` line: for each cited `<id>`, the prerequisite is **met** only if that entry is `[DONE]` / `[CONSUMED → session …]` in `_inbox_archive.md` (implemented or in-flight in a coding session), and **unmet** if it is still live (`new` / `refining` / `ready`) or itself blocked. An entry with any unmet dependency is **held, not dispatched** — dispatch moves to the next dispatchable entry and, if the ordering is unclear or contested, routes a note to `refine` (never a question to the human — SKILL § Dispatch operating discipline). This is the machine-readable half that makes dispatch's **autonomous-from-inbox** mode work (SKILL § The three roles; `commands/dispatch.md`). Instruction-level only — no hook (acp-ajudd#1).

## Captures inbound — reading and dispositioning (acp-ajudd#10)

The inbox does two jobs. The **to-do list** job is `work` (`new`/`refining`/`ready`) you pick up and build (above). The **captures-inbound** job is `capture`-type entries — raw inbound one session drops for another (a heads-up, a payload of values, a stray idea). This section is that inbound read flow.

**The model: the human is the notifier.** Claude does **not** monitor, poll, or auto-announce captures. There is no hook watching the inbox and no mid-session "you have mail" surfacing. Captures move only when a human coordinates it. Three phases:

**1. Write (silent to the recipient, visible to the sender).** A session drops a capture into another slug's inbox via `/session:inbox` — a **free-rein write** (no propose→approve, per acp-ajudd#5) that surfaces a visible confirmation line *in the sending session* (`Sent capture <id> to <target> inbox`). The receiving side is not interrupted.

**2. Coordinate (human).** The developer tells the target session where to look — "there's a capture for you from `<repo>/<session>`, go read it," or just "check my captures." Claude looks only when told. (The one automatic touch: a single **"N captures waiting"** count at `session:start` — see below — one read at a natural moment, not monitoring.)

**3. Read → disposition → archive (on request).** When asked, the target session:
   - renders every `capture`-type entry in its slug inbox via `inbox-render.py` (the consolidated `_inbox/` for plugin/personal; the global `_inbox/` for story/cab, *not* a per-session `_inbox_<name>.md`, since captures are addressed to the slug);
   - **dispositions** each — **promote** (it's real work → becomes `work` at `refining`: rewrite the type/status line and hand to refine or scope inline), or one of the read-and-archive fates: **discard**, **absorb into the current session** (fold its content — a data payload or an FYI — into the work at hand), or **feed a refinement**;
   - **archives** each non-promoted capture with the **bucket-3 planning-disposition stamp** `[DISPOSITIONED YYYY-MM-DD — <fate>]` (`<fate>` = `discarded` / `absorbed` / `refined` — see § Disposition & completion): append to `_inbox_archive.md` and remove from the live inbox. This is a **non-completion** stamp — dispositioning a capture is *not* completing implemented work (only a coding `/session:finish` writes `[DONE]`) and *not* a pickup-consume (`[CONSUMED → session]`). Same file and same auto-purge (>30d) as the `[DONE]` flow. Captures are **archived, never deleted** (a promoted capture stays live as `work` at `refining`/`ready`). *(Legacy captures archived with a bare `[CONSUMED YYYY-MM-DD]` still read correctly as historical dispositions.)*
   - surface a one-line summary, e.g. `Read 2 captures — 1 promoted to work (refining), 1 absorbed → dispositioned.`

**Addressing = to-slug (v1).** A capture is addressed to a repo's inbox — whoever next works that slug — not to a specific named session.

**Payloads — inline by default, optional `ref:`.** A small payload goes inline in the capture body. For a large payload, put it in a file and reference it:
```markdown
## <id> · [YYYY-MM-DD @ajudd] from virtual-office / BPT2-6258 (story) — enrollment test IDs
> [type: capture]
ref: ~/.claude/memory/sessions/ajudd-claude-plugins/_data_enrollment-ids.md
(inline summary: 12 member IDs for the reactivation smoke test — see ref for the full list)
```
When a capture has a `ref:`, the reading session reads the referenced file to get the payload. Inline is the default; `ref:` is only for payloads too big to sit in the inbox comfortably.

**Two lists at `session:start`, distinct types.** `capture`-type entries **never appear in the pickup list** — they are not work to grab; they surface only as a glance count. The `session:start` pickup list shows only `work` (`new`/`refining`/`ready`). The captures-inbound count is separate: a single line

```
Captures waiting: N — say "check captures" to read them
```

shown once at `session:start` when any `capture`-type entry exists. Omit the line entirely when there are none. This is the only place captures surface on their own — one glance, no monitoring.

**`question` deferred.** Not built in v1. A capture can carry a question; a reply is just another capture. No reply-expected lifecycle yet.

## Writing work and captures — free rein, never silent (acp-ajudd#5)

Inbox entries get written the way session files get written: **without asking.** `work` (and its work-repo analog, a Jira story) is *captured requirements and ideas — not code*; a `capture` is *inbound info*. So planning/refinement and cross-session handoffs write and update them with **free rein** — no propose→approve ceremony, no per-entry cap. Validation is the user's job **after the fact**: they read the entry (the inbox `work`/`capture` or Jira story) or trust the conversation it came from. This **reverses** an earlier "draft → show → approve → place" gate, which was rejected as friction on low-stakes captured intent.

**The one guardrail that survives — visible, not silent.** Every write must **surface a confirmation line in the conversation as it happens**, exactly like a session-file write is visible. This is *not* an approval step; it is just "say you did it," leading with the entry's `<id>`. A background write that never appears in the conversation is the one thing that is never allowed.

**Source of record — per zone (what you write to):**

| Zone (what repo am I in) | Source of record | Planning / refinement / handoff writes to |
|---|---|---|
| **Plugin marketplace** | `work` in `_inbox/` (→ file/git history) | the `work` entry |
| **Personal** (`personalProjectsDir`) | `work` in `_inbox/` (→ file/git history) | the `work` entry |
| **Work repo** (story/cab) | the **Jira story** (work's work-repo form) | the Jira story |
| **General** | none assumed | ask once, then that target |

Rule of thumb: **what repo am I in → that's my source of record → I write to it freely, because updating it IS the work.**

**Two capabilities this enables:** (1) a single planning/refine session **creates and updates as much work as it needs** — no per-write approval, no cap; (2) **frictionless cross-repo capture from anywhere** — fire a `capture` into *another* repo's inbox with minimal ceremony (flagship: a plugin idea you had while working in a work repo → send it to the plugins inbox). Nothing gates these writes: entries live under `~/.claude/memory/`, and there is no edit-blocking hook (acp-ajudd#1).

**Where this shows up:** `session:inbox` (writes directly, then a `Sent <work|capture> <id> to <target> inbox` line), `refine` (writes early + on each edit, surfacing `Wrote/Updated <id>`), `spawn` (writes the `[spawn]` work entry, confirms with `<id>`), and the `checkpoint`/`finish`/`commit` scope-routing handoffs (route through `session:inbox`). None gate the write; all surface it.

## State-exclusivity — a live `work` entry OR a consumed session, never both (acp-ajudd#13)

Free rein (above) governs *how* entries get written — no approval ceremony. This section governs the relationship between a **live `work` entry** and the **coding session** that builds it. It **replaces the old "planning edits in place, coding must not touch the record" role rule** — that rule tried to keep a coding session from mutating requirements by *forbidding* it; state-exclusivity makes the concern structurally impossible instead. It is a **documented convention, instruction-only — there is no guard or hook** (a record-layer hook would reintroduce exactly the file-edit policing acp-ajudd#1 removed, and would be trivially bypassed anyway).

The work layer = `work` inbox entries (their body / requirements / acceptance criteria) and their work-repo analog, Jira stories.

**The invariant: a given piece of work is EITHER a live `work` entry OR a consumed coding session — never both at once.**

- **A coding session *may* edit a live `work` entry.** While it is still in the inbox, editing its body is just **planning-in-the-moment** — free-rein, exactly like `refine`. There is no "coding sessions can't touch requirements" prohibition.
- **Picking up a `work` entry consumes it — fold-then-archive (acp-ajudd#40).** The pickup folds the body into the session file and **removes** the entry from the *live* inbox — appending a `[CONSUMED <date> → session <name>]` copy to `_inbox_archive.md` first, then **deleting** its `_inbox/<id>.md` file — as a recovery net (preserving its stable `<id>` in the session's provenance block). After that there is **no live entry left to edit** — the requirement now lives, and evolves, in the session. So the work can never exist as *both* a divergent live entry and an in-flight session: consuming is what makes it session-only. **Self-enforcing** — nothing forbids double-editing because there is only ever one live copy. The archived copy is **history, not a second live record**, and the `<id>` is **retired, never reused**.
- **Consumed = frozen after conversion (acp-ajudd#59).** A consumed entry takes **no writes from any role** once converted — not the refine author, not a dispatcher, not the coding session. There is nothing left to edit by construction, and by rule nobody reopens it: a change the build needs becomes a **new inbox entry / story**, never a re-edit of the retired one. This is the inbox-side statement of the per-role write-authority set (SKILL § The three roles § Inbox write-authority): consumed = frozen, `refine` authors requirements surgically (one `_inbox/<id>.md` file at a time — the per-item split makes "never a bulk rewrite of others" structural, not just disciplined), `dispatch` is read-only **except that it may author clear, no-refinement splits of in-flight work as NEW entries** (acp-ajudd#95 — never a write-back to an existing entry, which stays frozen), and `code` may edit only a *live* (pre-conversion) entry. (Do not confuse with **halted** work — stood down *before* completion — which also never reopens but re-enters as a **new entry citing the halted one**; see SKILL § HALT.)
- **Jira stories keep the "locked once *In Progress*" rule.** A Jira story is **not consumable** — you can't fold-then-archive it — so the exclusivity invariant can't be enforced structurally for stories. Instead, `/story:update` **locks the description once the story moves to *In Progress***, achieving the same "requirements don't drift mid-build" outcome by a lock rather than by deletion. Exclusivity-by-consumption is therefore **inbox-native only**; stories get the lock as their equivalent.

What a coding session **still does freely**: write/update its **own session file**; **post NEW inbox entries** — cross-session handoffs (`/session:inbox`), spawns, and captures. Posting new entries is unrelated to the invariant (it creates fresh entries, it doesn't fork an in-flight one).

(A `refining`→`ready` **status flip** and the fold-then-archive on pickup are not "forking the work" — they're the normal lifecycle. The thing state-exclusivity rules out is a live entry and a session both claiming the *same* work and drifting apart.)

## Stable IDs

Every inbox entry gets a **permanent, per-entry handle** at creation, so it can be named consistently across its whole life instead of by a list position that shifts every time an entry is added or folded. Applies to **all** project types (plugin / personal / work / general) and **both** types (`work` / `capture`) — one universal scheme, no per-type branching.

**Form:** `<acronym>-<handle>#<n>` — e.g. `acp-ajudd#14`, `glb-nivi#7`, `vo-ajudd#3`.

- `<acronym>` — deterministic short code for the **home** slug (the repo whose inbox the entry lives in — the target of a routed handoff, not the source). Derived by `scripts/inbox-id.py acronym --slug <slug>`: first letter of each token (split on `-`/`_`/camelCase), lowercased; single-token slugs use the first 3 chars. Same slug → same acronym on any machine, no config. The **session** lives on the provenance line, not in the ID — keeping the ID short and sayable.
- `<handle>` — the authoring user's handle. This **namespaces the counter per user**: `acp-ajudd#*` and `acp-nivi#*` are disjoint, so two developers can never collide on a number without any coordination.
- `<n>` — a monotonically-incrementing counter, per **(user, home-slug)**. Issued by `scripts/inbox-id.py next --slug <home-slug> --handle <handle>`, which increments and persists the counter.

**Counter storage — local, never in a repo.** `~/.claude/config/inbox-seq.json` (`{ "<slug>": <n>, ... }`) on the author's machine. Because the counter is never in the shared repo and is namespaced per user, there is nothing shared to merge-conflict on.

**Self-healing seed — `next` can never hand back a used ID (acp-ajudd#66).** The stored counter is only the fast path; on every `next` the minter also **scans the slug's inbox files** — the top-level `_inbox*.md` (the single `_inbox_archive.md`, any legacy `_inbox.md` / per-session `_inbox_<name>.md`) **and the per-item `_inbox/*.md` dir** (the live consolidated inbox after acp-ajudd#102) — for the highest `#N` already issued to *this* `<acronym>-<handle>` and seeds from `max(stored-counter, that file max) + 1`, computed and persisted atomically inside the mint lock. So a lagging counter — or a header that was written *without* calling the minter — is self-correcting: the next real mint sees the existing number and steps past it. **This retires the old operational caution** ("don't trust `inbox-id.py`; hand-pick max+1"): the script now reconciles against the files itself, so it is always safe to trust. Hand-picking is no longer needed and must stop (see the hard rule below).

**Never hand-write a header — always mint (acp-ajudd#66, half two).** The `## <acronym>-<handle>#<n>` header is issued by `inbox-id.py next` and **nothing else**. Do **not** hand-assign a number by eyeballing the inbox, even when in a hurry or coordinating across terminals — hand-written headers are exactly what desynced the counter and caused the `#63` double-grab. Every creation path routes through the minter: `refine` (new/promoted `work`), `spawn` (the `[spawn]` entry), `/session:inbox` (handoffs and captures), and `dispatch`'s no-refinement **splits** of in-flight work (acp-ajudd#95). `dispatch` authors nothing *but* those clear splits — for anything needing requirements work it routes the record-authoring to `refine` — and when it does author a split it **still mints via the script** (never a hand-written header). The self-heal above is the safety net for a slip, not a license to skip the script.

**Permanence.** An ID is assigned once and never reused or renumbered. Folding/deleting an entry **retires** its ID; the counter never goes backward (the file scan only ever raises the floor).

**Generating an ID at write time** (any inbox write site):
```bash
IDT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}/scripts/inbox-id.py"
if command -v python3 >/dev/null 2>&1; then python3 "$IDT" next --slug "<home-slug>" --handle "<handle>"; else python "$IDT" next --slug "<home-slug>" --handle "<handle>"; fi   # prints the ID and increments
```
The `python3 → python` fallback matters on Windows Git Bash, where only `python` may be on PATH. Use `--peek` to preview the next ID without consuming it. If **neither** `python3` nor `python` (nor the script) is available, fall back to `<acronym>-<handle>#?` and note the counter could not be advanced (degrade gracefully rather than block the write).

**Parser tolerance (back-compat).** The `<id> · ` prefix is **optional** in the header. Entries created before this scheme (and archived entries) have no ID — parse them exactly as before. Show the ID if present; omit the segment if absent. Never break on a missing ID.

**Deferred (refine later):** acronym collisions across two different repos, and multi-user migration. Neither affects local/single-user use.

## Provenance Rendering (layout B)

How inbox entries are **displayed** for pickup. Applies to the session:start routing block and session:switch listing (two-line form), and to the finish/checkpoint sweeps (single-line form). Parse the header before rendering.

**Parsing the source (`from <slug> / <session> (<type>)`):**
- Tolerate both spaced `slug / session` and unspaced `slug/session`.
- `(<type>)` is **optional** — legacy entries omit it. If absent, render without it.
- If only a bare `<source>` is present (oldest entries, no `/`), treat it as the session with no slug.
- Never break on a malformed header — degrade to showing whatever is present.

**Two-line form (pick lists — the default):**
```
Inbox — code work, or refine new work (N):
  1  [acp-ajudd#14]  <description>
     ↳ <slug> / <session> (<type>) · MM-DD
  2  [acp-ajudd#9]  ★ [spawn] <label>
     ↳ <slug> / <session> (<type>) · MM-DD
```
- **Description leads** — it's the decision driver when picking.
- **Stable ID before the description**, in `[ ]`. The leading `N` is the **ephemeral in-view position** (for `code <n>` convenience); the `[<id>]` is the **permanent handle** — use it in conversation and recaps. `code` accepts either. Omit the `[<id>]` segment for legacy entries that have none.
- **Same-repo dimming:** when `<slug>` equals the current repo slug, **drop it** — show `↳ <session> (<type>) · MM-DD`. Only genuinely cross-repo origins show the slug.
- **Missing type:** omit the `(<type>)` segment; still show `↳ <slug> / <session> · MM-DD`.
- **The pickup list shows only `work`** (`new`/`refining`/`ready`); `new`/`refining` work carries a `· <stage>` suffix so still-scoping work is visually distinct from pickable `ready` work. **Captures never appear here** — they surface via the "Captures waiting: N" glance only.

**Single-line form (finish/checkpoint sweeps — action prompts stay one line):**
```
  [acp-ajudd#14] Work pending: "<description>"  ·  ↳ <session> (<type>)   nothing / done / picked-up
```
Drop the slug when same-repo; include it for cross-repo. Omit the `[<id>]` for legacy entries with none.

## Disposition & completion — three stamps, three owners (acp-ajudd#42)

When an entry leaves the live inbox it gets an archive stamp. There are **three distinct stamps and they must never be blurred** — each answers a different question, and only some actors may write each. The rule that matters most: **"complete" means *implemented*, and only a coding session's `/session:finish` may say it.** A planning / refine / sessionless read may create, refine, delete, backlog, or set-aside an entry freely — it may do everything *except* mark it complete.

| Stamp | Bucket | Means | Written by |
|---|---|---|---|
| `[DONE YYYY-MM-DD]` | **1 — COMPLETION** | the work is *implemented and closed* | **ONLY a coding session's `/session:finish`** (or a coding `checkpoint` closing its own picked-up work). Never a planning/refine/sessionless read. |
| `[CONSUMED YYYY-MM-DD → session <name>]` | **2 — CONSUMED-ON-PICKUP** | the `work` was *folded into a coding session* — **taken, not done** | **ONLY a coding session, at pickup** (acp-ajudd#40). The `→ session <name>` suffix marks it as a pickup-consume, not a completion. |
| `[DISPOSITIONED YYYY-MM-DD — <fate>]` | **3 — PLANNING DISPOSITION** | a *non-completion* fate applied on read: `<fate>` = `discarded` / `absorbed` / `refined` / `superseded` | a read that decides not to build as-is — typically a **planning / refine / sessionless** read, but a coding session reading a capture it won't build also dispositions it. **Never means implemented.** |

**Why the split (the live incident).** A planning context once archived an audit-index capture with a `[CONSUMED … shipped]` stamp while that index still had open children — using a completion word for something it had no authority to complete. Bucket 3 exists so a planning read has a stamp that says "handled, not built."

**Backlog is a move, not a stamp.** "Move to backlog" relocates the entry to `_backlog*.md` (bucket-3 non-completion, nothing archived); it is deferral, not completion. Deleting a backlog entry is a permanent drop — still never a completion.

**Back-compat (existing archives stay readable).** Legacy `[DONE]` and legacy bare `[CONSUMED YYYY-MM-DD]` (no `→ session`, written by the old captures-inbound disposition flow) both still parse — treat a bare `[CONSUMED]` with no `→ session` suffix as a historical bucket-3 disposition. No migration; old stamps read in place.

**Parent / index closes bottom-up.** An entry that spawned children — an **audit index** mapping findings to child entries (e.g. `A1 → #36`, `D10 → #40`) is the canonical case — is **not complete until its implemented children are complete**. Each child is closed by *its own* coding session's `/session:finish` (bucket 1); only once every implemented child is `[DONE]` may the parent index be marked `[DONE]`. A planning/refine read **must never self-complete a parent** while children remain open. Until then the index stays live (`refining`/`ready`), ideally carrying a "stays live until children close" note and a child→status map.

## Lifecycle (pickup states)

Pickup state is **orthogonal to the maturity `status` above**: `status` = "is this work scoped enough to grab" (`new` → `refining` → `ready`); pickup state = "has a session grabbed it yet." A `new`/`refining`/`ready` work entry is "pending" here; `code`-ing it makes it in-progress (`new`/`refining` just means `code` warns first).

**Two pickup mechanisms, by inbox kind:**
- **Item-driven consolidated inbox (plugin / personal — `_inbox/`):** pickup **consumes** the entry — **fold-then-archive** (state-exclusivity, above): the body folds into the session file, a `[CONSUMED <date> → session <name>]` copy is appended to `_inbox_archive.md`, and the item's `_inbox/<id>.md` file is deleted. The session (with the archived copy as a backstop) is the paper trail.
- **Per-session inbox (story / cab — `_inbox_<name>.md`):** pickup inserts an **in-progress marker** and the entry **stays** in the inbox until done, then archives. This is the pending → in-progress → done flow below.

**Pending** — arrived, not yet picked up:
```markdown
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 (story) — Add /comms:pto command
> [type: work · status: ready]

Add a `/comms:pto` command...
```

**In-progress** — session picked it up (per-session inbox kind). A marker is inserted after the `## [date]` header:
```markdown
## [2026-05-13 @ajudd] from virtual-office / BPT2-6258 (story) — Add /comms:pto command
[in-progress — session, 2026-06-04]

Add a `/comms:pto` command...
```
A matching `[inbox] Add /comms:pto command` line is added to the session's Open items.

**Done** — work **implemented and complete** (bucket 1 — see § Disposition & completion). Written **only by a coding session's `/session:finish`** (or a coding `checkpoint` closing its own picked-up work) — never by a planning/refine/sessionless read. Removed from inbox and appended to the archive with a `[DONE]` stamp.
(The pickup archive uses the distinct bucket-2 stamp `[CONSUMED <date> → session <name>]` — *taken, not done*. A planning read that decides not to build uses bucket-3 `[DISPOSITIONED …]` or moves it to backlog — never `[DONE]`.)

## Triage Options (at session:start / checkpoint / finish)

Each verb maps to a disposition bucket (§ Disposition & completion). Only **Mark done** carries a completion semantic, and it is gated to a coding session.

- **Work on it** — inserts `[in-progress — <session>, <date>]` in the entry, adds `[inbox] <item>` to session Open items. Does NOT archive yet.
- **Mark done** (bucket 1 — COMPLETION) — archives with `[DONE]` stamp, removes from inbox. **Only valid from a coding session closing work it actually built.** A planning / refine / sessionless read must not use this — that is a planning disposition: use **Move to backlog** or a bucket-3 `[DISPOSITIONED … — superseded]` archive, never `[DONE]`.
- **Move to backlog** (bucket 3 — planning disposition, non-completion) — moves to `_backlog_<name>.md` (plugin) or `_backlog.md` (others). No archive. Available to any read.
- **Keep** — leaves as-is in inbox. Does not add to Open items.

## Auto-Purge

At session:start, archive entries with `[DONE YYYY-MM-DD]` older than 30 days are dropped automatically. `[in-progress]` markers and backlog entries are never auto-purged.
