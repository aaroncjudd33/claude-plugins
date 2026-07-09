---
name: inbox
description: Route a work item to another session's inbox. The single hub for all cross-session handoffs — scope guards in checkpoint, finish, and commit invoke this same logic.
argument-hint: "[target-session]"
---

# Session: Inbox

Route a work item to a target session's inbox and record it in the source session's outbox. All cross-session routing flows through here.

**Free rein, never silent (acp-ajudd#5).** An inbox item is captured intent, not code — so routing one is like writing a session file: you do it **without a propose→approve ceremony.** There is no pre-write approval gate anywhere in this flow. The one rule that survives is *visibility*: every write **surfaces a confirmation line in the conversation as it happens** (Step 5), so the user can read the record and validate it after the fact. "Just do it, but say you did it."

## Instructions

### 0. Resolve Context

Run `pwd`, extract slug, resolve `session_root` and `handle` using Path Resolution (see Session Skill).

Determine the current session name from conversation context (most recent "Resuming `<name>`" or "Switching to `<name>`" line). If no session is active, source attribution uses `from <slug>` only — warn: "No active session — routing from repo level. Run `/session:start` first for proper attribution."

Also determine the **source session type** (`story` / `cab` / `plugin` / `personal` / `general`) for provenance — read the active session file's `type:` frontmatter (or the `- **Type:**` body bullet); fall back to the current repo's type from Path Resolution. This is the SOURCE type — recorded on the item so the receiving inbox shows where it came from. If no session is active, omit the `(<type>)` segment.

### 1. Determine Content

If item content is already clear from context (e.g., the scope guard just detected a specific file or described a task), use it directly — do not ask.

Otherwise:
```
What's the item to route? (one-line description)
```

Compose a self-contained body block — enough context that the receiving session can act on it weeks later with no memory of this conversation.

### 2. Determine Target

If an argument was passed (e.g., `/session:inbox release`), use it as the target session name and skip the prompt.

If the target is clear from context (an argument was passed, or the scope guard already identified the file path and owning plugin/session), use it **directly — write the item, then report it.** Do not gate the write behind a "route to X? yes/no" prompt; the Step 5 confirmation line names the target so a wrong inference is immediately visible and the user can redirect. Free rein means routing is like writing a session file — done, then surfaced, not asked-first.

Only when the target genuinely cannot be derived (no argument, no context signal), list sessions and ask — this is a routing necessity (there is no destination yet), not an approval gate:
```
Where should this go?
  [1] <session-name> — <type> · inbox N · last <date>
  [2] <session-name> — <type> · inbox N · last <date>
  ...
  [G] Global inbox — no named target yet (surfaces at next session:start)
  [X] Cross-repo — different project
```

- **Target type decides the file:**
  - **plugin / personal target** → the slug's consolidated inbox `<target_session_root>/_inbox.md`. These types are item-driven: there is ONE inbox per slug, and `/session:start` `code`s records from it. Do NOT write a per-session `_inbox_<name>.md` for these — the new flow never reads it.
  - **story / cab / general target** → per-session `<target_session_root>/_inbox_<target-name>.md` (route a handoff to a specific story/CAB, as today).
- **Global** → `<target_session_root>/_inbox.md` (cross-cutting items with no specific target; for plugin/personal slugs this is the same file as a named target).
- **Cross-repo** → ask for the target repo slug, then show that repo's sessions using the same prompt

### 3. Write Inbox Entry

Determine target file:
- plugin / personal target, or Global → `<target_session_root>/_inbox.md` (create with header `# Inbox — <slug>` if needed)
- story / cab / general named session → `<target_session_root>/_inbox_<target-name>.md` (create with header `# Inbox — <target-name>` if needed)

**Issue a stable ID first.** The ID's home is the **target** slug (where the item will live and get its number), and it is namespaced by the **author's** handle. Determine `<target-slug>` — the slug that owns `<target_session_root>` (the current slug for same-repo, or the chosen repo slug for cross-repo):
```bash
IDT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}/scripts/inbox-id.py"
if command -v python3 >/dev/null 2>&1; then python3 "$IDT" next --slug "<target-slug>" --handle "<handle>"; else python "$IDT" next --slug "<target-slug>" --handle "<handle>"; fi   # prints e.g. acp-ajudd#7, increments the counter
```
If `python3`/script is unavailable, fall back to `<acronym>-<handle>#?` and note the counter wasn't advanced — never block the write. See `references/inbox-convention.md` § Stable IDs.

Append (record the ID, then the **source** slug/session/type — not the target — followed by the `status` line):
```markdown
## <id> · [YYYY-MM-DD @<handle>] from <source-slug> / <source-session> (<source-type>) — <description>
> [status: capture]
<body>
```
Omit the `(<source-type>)` segment only when no source session is active (repo-level routing). The `<id>` is permanent — it never changes as the item moves through its lifecycle.

**Everything routed through `/session:inbox` is a capture (acp-ajudd#21).** There is no `type` axis anymore — an inbox holds **captures** on one lifecycle (`capture` → `refining` → `ready`), and a routed handoff always arrives at the entry state `capture`. Provenance is recorded (the header above); *intent* is deferred to the reader, who dispositions the capture when they read it. Full model in `references/inbox-convention.md` § Item Model.

`/session:inbox` only ever **creates** a capture at `status: capture` — it never marks any item complete, done, or shipped, and it never archives (the outbox is append-only, below). Completion is a coding-session `/session:finish` act alone (acp-ajudd#42, § Disposition & completion) — nothing on this write path can stamp it.

**The `> [status: …]` line** carries the capture's lifecycle status plus an **optional, non-binding intent hint**:
- **`status`** — always **`capture`** for a fresh handoff (the single entry state). Do not write `refining`/`ready` here — those are reached by `refine` promoting the capture, not by the sender. (`refine` writes `refining` directly; a spawn writes `ready` — those are separate write sites.)
- **`intent`** (optional) — a hint the sender may attach so the reader knows what the sender *thinks* it is, without deciding for them: `> [status: capture · intent: story]` ("looks like real work"), `intent: fyi` ("awareness only, no build expected"), or `intent: data` ("a payload to consume as input"). Omit it entirely when unsure — the reader infers from the content. Intent **never binds**; the reader always dispositions (promote / discard / absorb / feed a refinement — see § Captures inbound).
  - **`intent: data` payload:** inline in the body by default. For a large payload, write it to a file and add a `ref: <path>` line in the body instead (see § Captures inbound for the shape).

See Provenance Rendering in `references/inbox-convention.md` for how this header + line is later displayed.

### 4. Write Outbox Entry

If a source session is active, append to `<session_root>/_outbox_<source-name>.md` (create with header `# Outbox — <source-name>` if needed):

```markdown
## [YYYY-MM-DD @<handle>] → <target-slug> / <target-session> — <description>
<body>
```

Outbox is append-only — never modified or archived.

### 5. Confirm — surface the write (the one guardrail)

The write already happened in Step 3. Surface it as a plain feedback line so the record is visible and validatable — lead with the stable `<id>`:

```
Sent inbox item <id> to <target-name> inbox — surfaces when that session starts.
```

This line is **feedback, not a gate.** It names the target so a wrong inference is obvious; if it went to the wrong place the user just says so and you re-route. Never skip it — a write the user never sees is the exact silent-auto-file failure this flow exists to prevent.
