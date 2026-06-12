---
name: memory
description: "Governs project and feature memory across all repos. Load whenever the user invokes a memory command (/memory:load, /memory:save, /memory:scan, /memory:review), asks to load/save/find project memories, asks what the project knows about a feature area, or when a session command needs to record or validate loaded memories. Provides the feature:X/Y label convention, project-memory path resolution, on-demand loading rules, and the session integration contract (Loaded memories field)."
---

# Memory Skill

Manages **project and feature memory** — the git-tracked facts about how a codebase works, scoped by feature area. Separate from the session plugin (which manages lifecycle) and from global behavioral memory (preferences/feedback in `~/.claude/memory/`, which is not feature-scoped).

The design goal: nothing loads automatically, everything is labeled by feature so it can be found, and every memory that influences work gets validated at session close. This is the anti-rot mechanism — touched = reviewed, untouched = inert.

---

## Label Convention

The full spec is in `references/label-convention.md` — **read it before writing or relabeling any memory file.** Summary:

- Every feature memory carries `label: feature:<area>/<subcategory>` in frontmatter.
- Stop at subcategory — never encode file or function names.
- Multiple comma-separated labels allowed for genuine cross-cutting facts.
- `written:` date drives the staleness signal.
- Files live flat in one directory; the label (not the folder path) is how they're grouped.

---

## Project Memory Path Resolution

All memory commands resolve the active project memory directory the same way:

```
repo_root = git rev-parse --show-toplevel  (or pwd if not a git repo)

if <repo_root>/.claude/memory/ exists:
    memory_root = <repo_root>/.claude/memory/      (repo tier — migrated, shared)
else:
    memory_root = ~/.claude/projects/<encoded>/memory/   (local tier)
```

`<encoded>` = the projectRoot absolute path with path separators and special characters replaced by `-` (the Claude Code local-memory convention). If multiple local matches, prefer the one whose name corresponds to `git rev-parse --show-toplevel`.

`MEMORY.md` is always the index at the root of `memory_root` — one line per memory file, `- [<name>](<file>) — <description>`.

**Never touch global memory** (`~/.claude/memory/`) from memory commands — that tier is behavioral feedback managed by the auto-memory system.

---

## On-Demand Loading Rule

**Nothing loads automatically.** In migrated repos, `MEMORY.md` is the only project memory file that auto-loads (via the `.claude/CLAUDE.md @import`); the local tier has no such import, so even the index is read on demand there. Individual feature memory files are read only when:

1. The user explicitly runs `/memory:load` or `/memory:scan`, or
2. A session command (start on a returning session) replays the session's recorded `Loaded memories:` and the user opts to reload them.

Do **not** proactively read feature memory files at session start or speculatively during work. The index is sufficient to know what exists. This is the primary defense against context rot — a stale memory that is never loaded cannot mislead.

---

## Session Integration Contract

The memory plugin and session plugin share state through two session-file fields. The session plugin owns the schema; the memory plugin reads and writes these fields when a session is active.

**`Loaded memories:`** — list of memory files loaded into context this session. Written by `/memory:load`, `/memory:scan`, and `/memory:save` (a freshly-saved memory counts as loaded). Format:
```
- **Loaded memories:**
  - checkout-payment-validation  [feature:checkout/payment-validation]
  - cart-totals                  [feature:cart/totals]
```
- If no session is active, memory commands still work — they just skip recording.
- Find the active session via the session plugin's Path Resolution (`_active` marker → session file). If absent, operate session-less.
- On a returning session, `session:start` shows these as reload candidates.

**`Commits:`** — owned and written by `session:commit`; the memory plugin does not write it. Listed here only so the two field additions are understood as one schema extension.

**Finish-time validation:** `session:finish` invokes the review flow (see `/memory:review`) against the session's `Loaded memories:` before closing. Every memory that influenced the session's work gets a still-accurate check at the point of relevance.

---

## Feature-Area Detection

`/memory:scan` and the session-start scan offer both infer the current feature area from available signals, in priority order:

1. **Current conversation** — what the user has said they're working on (most specific).
2. **Branch name** — `feature/BPT2-6155-checkout-validation` → `checkout`, `validation`.
3. **Story title** — from the active session file's `Title:` field (story/cab sessions).
4. **Recently touched files** — `git diff --name-only` and `git diff --name-only --staged`; map directory/path segments to feature areas.

Match the inferred terms against memory `label:` fields first (precise), then against `description:` lines in `MEMORY.md` (fuzzy). Present candidates ranked by match strength. Never auto-load — the user always picks.

---

## Reference Files

- `references/label-convention.md` — the authoritative label format spec; read before writing or relabeling any memory.

---

## Relationship to Other Plugins

- **session** — owns session lifecycle and the session-file schema (including `Loaded memories:` and `Commits:`). Memory commands read/write `Loaded memories:` via the session's Path Resolution. `session:migrate` runs the one-time relabeling walk-through; `session:finish` invokes memory review.
- **Global auto-memory** — behavioral feedback in `~/.claude/memory/`. Out of scope for the memory plugin; not feature-labeled.
