# Inbox — ajudd-claude-plugins

---

## Item-driven sessions for plugin & personal work (no more blank/plugin-named sessions)
_Added 2026-06-30 (from session redesign discussion — full plan: `C:\Users\ajudd\.claude\plans\merry-questing-sedgewick.md`)_

### What
For **plugin** and **personal** session types only (story/cab/general untouched — they already have an external system of record):

1. No active session → investigate/explore freely, nothing written, no gate at all.
2. A plugin/personal session can ONLY be created by picking up (or writing on the spot) an inbox item — no more blank or plugin-named session creation.
3. Session file is named after the feature/item (derived from the item, confirmed once), not the plugin or project.
4. Edit/Write is hard-blocked (real PreToolUse hook enforcement, not just CLAUDE.md instruction-following) unless the active session is in `Mode: coding`/`both`.
5. At pickup, the item's full content is folded into the new session file and the item is deleted from the inbox immediately — no archive, no duplication.
6. Finish never deletes session files, only marks `Status: completed` (already true today — confirmed, no change needed there).
7. Old legacy session files (`session.md`, `release.md`, etc.) and old fragmented inbox files are left alone — no migration, no forced renaming/closing.

### Why
Plugin and personal projects have no Jira story / CAB card acting as the external unit of work — unlike story/cab sessions. Today, plugin sessions are persistent per-plugin accumulators that grow forever (`session.md`, `release.md`, ...), already drifting toward ad-hoc feature names (`perf-parallelization.md`) with no consistent rule. The "no active session" gate is **not actually enforced** today — it only works because the model follows instructions in `~/.claude/CLAUDE.md`; the real hook (`session-scope-guard.py`) is opt-in (`sessionGate.enforce`, defaults `false`) and only checks `_active` existence, never `Mode`. Inbox state is fragmented across 5+ file patterns (this very file, a sparse local `_inbox.md`, 8 per-plugin `_inbox_<plugin>.md` files, matching archives, and backlog files).

### Design (full detail in the plan file — summary here)
- **Frontmatter for `type`/`mode`/`status`** added to session files (alongside existing `updated:`) so the hook can parse reliably instead of regexing freeform markdown body bullets. Defaults to `mode: coding` if absent (back-compat).
- **Extend `session-scope-guard.py`** (no new hook file) — add a `read_session_mode()` helper; marketplace zone and personal-projects zone block on no active session or `mode: planning`; this check is **unconditional** for these two zones (decoupled from `sessionGate.enforce`, which stays as-is for the work-repos/story-cab zone). This was the one thing two independent Opus design passes caught and two Sonnet passes missed: leaving it behind the opt-in flag (default off) would make the gate a no-op by default.
- **Single consolidated inbox per slug, local tier** — promote `~/.claude/memory/sessions/<slug>/_inbox.md` to the canonical inbox (same tier session files already live in). For plugin type, slug = `ajudd-claude-plugins`. One-time manual migration of this file's 3 real entries + `_inbox_session.md`'s 1 entry into that local file; this file (`_inbox.md` at repo root) then becomes superseded — leave in place as history, stop reading it.
- **Repo isolation is pre-existing, not new — just confirm it holds.** The plugin marketplace is one repo/slug (`ajudd-claude-plugins`); each personal project is its own separate repo with its own slug under `~/.claude/memory/sessions/<slug>/` (own `_active`, own inbox, own session files). This is how path/slug resolution already works today — the redesign doesn't introduce cross-repo sharing, it just applies the identical mechanism independently inside each repo's own directory. No personal project should ever read/write another personal project's (or the plugin marketplace's) session state.
- **`start.md`/`start-impl.md` plugin+personal branches** — remove blank-creation paths; add inbox listing + `resume <n>` / `pick <n>` / `new <description>` verbs; `pick`/`new` derive a feature name (confirmed once), fold the item body into the new session's Open items, delete the item from the inbox.
- **`CLAUDE.md` "Session Enforcement" section** — state reads/explore are always free for every type; for plugin+personal note the gate is now hook-enforced, not just instruction-followed; remove the blanket "stop before any work" framing for these two types.
- **Personal-type branches are unverified** — none of the design research covered them yet (scope was plugin-only during research); re-read `start.md`/`start-impl.md` personal branches before implementing, since personal sessions may already informally follow part of this pattern.

### Acceptance criteria
- [ ] No active plugin/personal session: Read/Grep/Glob/Bash read-only succeed, no file written; Edit/Write blocked
- [ ] `pick <n>` on an inbox item creates a feature-named session in `Mode: coding`, folds the item body in, deletes the item (no archive)
- [ ] `new <description>` round-trips through write-then-immediate-fold with no stray leftover entry
- [ ] Active session in `Mode: planning` blocks Edit/Write with a clear message; switching to `coding` unblocks it
- [ ] Work-repos (story/cab) zone behavior is completely unchanged (still opt-in via `sessionGate.enforce`)
- [ ] `/session:finish` still never deletes the file, marks `Status: completed`, and the session is excluded from the default `/session:start` resumable listing
- [ ] Legacy plugin-named session files and all old fragmented inbox/archive/backlog files are untouched (byte-identical before/after)
- [ ] CLAUDE.md "Session Enforcement" section accurately describes hook-enforced (not instruction-only) behavior for plugin+personal, with reads always free
