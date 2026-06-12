---
name: memory
description: "Governs project and feature memory across all repos. Load whenever the user invokes a memory command (/memory:load, /memory:save, /memory:scan, /memory:review, /memory:doctor), asks to load/save/find project memories, asks what the project knows about a feature area, mentions memories stranded or misplaced in global, or when a session command needs to record or validate loaded memories. Provides the feature:X/Y label convention, project-memory path resolution, on-demand loading rules, and the session integration contract (Loaded memories field)."
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

**Never touch global memory** (`~/.claude/memory/`) from memory commands — that tier is behavioral feedback managed by the auto-memory system. **The one and only exception is `/memory:doctor`**, which exists specifically to find project memories stranded in global and relocate them — and even it acts only on explicit invocation, with per-file confirmation, never silently. `save`, `load`, `scan`, and `review` must never read or write global.

**Stranded-memory failure mode:** project memories that ended up in global (legacy data from before the tier split, or a save that resolved global by mistake) are invisible to `migrate`, `load`, and `scan` — all of which resolve the project tier only. The result is silent: a developer believes they shared project context but the files never left global. The defenses are (1) `save`'s hard guard against ever writing to global (its leak prevention), and (2) `/memory:doctor` to reconcile what's already stranded. `migrate` deliberately does **not** reach into global — that would force it to guess project-vs-behavioral classification; doctor carries that judgment with a human in the loop instead.

---

## On-Demand Loading Rule

**Nothing loads automatically — including the index.** There is no `.claude/CLAUDE.md @import`; migration does not create one. `MEMORY.md` itself is read on demand (by a memory or session command), not forced into context when the repo is opened. A developer who opens a migrated repo without invoking a command inherits zero overhead — every file under `.claude/memory/` is inert until a command reads it.

Memory enters context only when:

1. The user explicitly runs `/memory:load`, `/memory:scan`, or `/memory:review`, or
2. A session command surfaces the session's recorded `Loaded memories:` and the user opts to reload them, or
3. The session-start scan offer presents candidates and the user accepts some (a prompt — never a silent read).

Do **not** proactively read memory files at session start or speculatively during work. This is the primary defense against context rot: a stale memory that is never loaded cannot mislead anyone. Rot becomes inert, not infectious — an unmaintained file simply sits unused rather than corrupting a teammate's context.

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
