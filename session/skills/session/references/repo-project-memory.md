# Repo Project Memory

How project memories are stored/shared/loaded across the three tiers. Loaded on demand (the SKILL keeps a one-line pointer at § Repo Project Memory).

Project memories can be stored in the repo under `.claude/memory/` for team sharing.

**Three tiers:**
- Global (`~/.claude/memory/`) — cross-project, always loaded
- Local (`~/.claude/projects/<encoded>/memory/`) — machine-specific, auto-loaded by Claude Code
- Repo (`.claude/memory/`) — git-tracked, shared; activated by running `/session:migrate`

**Activation:** Run `/session:migrate` — creates `.claude/memory/`, writes attribution frontmatter and feature labels on each migrated file, regenerates `MEMORY.md`. It does **not** write `.claude/CLAUDE.md` — there is no auto-load import (see below).

**No auto-load — on demand only.** Project memory is **never** loaded automatically. There is no `.claude/CLAUDE.md @import`. A developer who opens a migrated repo without invoking a command inherits zero context overhead — the `.claude/memory/` files are inert until a command reads them. This is deliberate: the **memory plugin** governs all loading, and it only reads when the user asks.

- Even `MEMORY.md` is read on demand (by the memory plugin or a session command) — it is not forced into context at repo open.
- Load individual memory files only via `/memory:load`, `/memory:scan`, `/memory:groom`, or when a session command surfaces the session's recorded `Loaded memories:` and the user opts to reload.
- Never proactively read memory files at session start. Surfacing relevant memory happens through the memory plugin's scan offer (a prompt the user accepts or rejects) — never as a silent auto-read.

**Global vs. project memory:** The on-demand rule applies to project memory (repo `.claude/memory/` and local `~/.claude/projects/<encoded>/memory/`). Global memory (`~/.claude/memory/`) contains behavioral guidelines — feedback, preferences, cross-project rules — and may load freely as needed.

**Writes:** New project memories are written to `.claude/memory/` by the memory plugin's `/memory:save` (it resolves the path itself — no `CLAUDE.md` redirect needed). The memory plugin owns the read and write paths; the session plugin only records which memories were loaded (`Loaded memories:` field).

**Merge semantics:** Re-running `/session:migrate` is safe — adds files not yet in repo, skips files already present. Multiple developers can migrate independently; files merge together with no overwrites.

**Rollback:** Delete `.claude/` folder. Claude falls back to local memory automatically. Same format both places — no manual steps required.

**Sentinel:** `~/.claude/projects/<encoded>/memory/.migrated-to-repo` — local-only marker with migration date and repo path.

**Before concluding project memory is absent, check the actual file listing — not just whether `MEMORY.md` looks like a stub (acp-ajudd#139).** Observed live: a session read `.claude/memory/MEMORY.md`, saw what looked like an empty/stub index, and concluded "not migrated" — while the real content (59 individual memory files) was sitting untouched in the same directory the whole time; only the index file was misleading. `MEMORY.md` is a derived index, not the source of truth — a stub or stale-looking index does not mean the underlying `.claude/memory/*.md` files are missing. List the directory before concluding memory is unavailable. Separately: memory can also be genuinely present on a **different branch** than the one currently checked out (e.g. a migration that landed on a feature branch and was never merged) — `git show <branch>:.claude/memory/<file>` reads it without merging or switching branches, and reading it that way is not itself a reason to propose migrating/merging anything unless asked.

**A "migrated" local stub is only true on the branch the migration commit actually reached — verify before trusting it (acp-ajudd#144).** The local tier's `MEMORY.md` gets stubbed to `"Migrated — do not use, all reads/writes now go to the repo path"` plus a `.migrated-to-repo` sentinel once `/session:migrate` runs — but that stub is written once, on whichever branch was checked out at migration time, and is itself unversioned (it lives outside git entirely, at `~/.claude/projects/<encoded>/memory/`, so it never gets reverted or branch-scoped). If the migration commit is later merged to master, the stub is accurate everywhere. If it **isn't** — a real, observed case: the migration landed on a feature branch that was never merged — the stub still confidently says "don't use me" on every other branch, including master, even though the repo-tracked `.claude/memory/` it points to doesn't exist there. Reading the stub and stopping is exactly the failure this causes: a session goes hunting through git history for content that was sitting untouched in the local folder the entire time (the local tier is never deleted by migration, only stubbed). **Before treating a "migrated" local stub as authoritative, check that the repo-tracked `.claude/memory/MEMORY.md` actually exists on the *current* checked-out branch** (a plain file-existence check). If it doesn't, the migration hasn't reached this branch — read the local tier's real files directly instead of the stub's index; do not propose re-running `/session:migrate` as the fix (that only adds a third stranded copy on yet another branch) — the actual fix is merging the original migration commit to master, which is a repo-owner decision, not something to do unprompted.
