---
name: start
description: Start a working session. Loads last session context and routes into the right workflow.
---

# Session Start

Begin a working session. Establishes session identity, Teams chat, and routes into the right workflow.

## Instructions

### 0. Fast-Path Argument Check

If arguments were passed to `/session:start`, attempt to resolve them before running the full discovery flow.

**Two verbs — `refine` (planning, sessionless) and `code` (coding session).** The mode is never something you set; it is **read from the file you're touching** — a target with no session file is **work** you're still scoping (planning/refining), a target that already has a session file is *coding*. `code` and `refine` just name which side you're on. (`new`, `resume`, and `pick` are retired — folded into these two.)

**Detect arg type** (checked in order):

| Pattern | Example | Resolves to |
|---------|---------|-------------|
| `mine` | `/session:start mine` | full discovery flow with mine filter |
| `refine [target]` | `/session:start refine shopify refund` | refinement flow (Step 4 → Refine); **sessionless — never creates a session file** |
| `dispatch` | `/session:start dispatch` | dispatch flow (`commands/dispatch.md`); **sessionless — assume the dispatch role, orient on the inbox.** Plugin/personal only |
| `capture` | `/session:start capture` | capture flow (`commands/capture.md`); **sessionless — assume the capture role, bank ideas into `capture`-type inbox entries.** Plugin/personal only |
| `code <target>` | `/session:start code BPT2-6429` | coding session on `<target>` — the file decides: a **`work` entry** graduates into a fresh session, an existing **session** resumes |
| `BPT2-XXXX` (Jira story key) | `/session:start BPT2-6429` | coding session on that story (bare key = implicit `code`) |
| `CAB-XXXX` (CAB key) | `/session:start CAB-9260` | coding session on that CAB (bare key = implicit `code`) |
| `code cab BPT2-XXXX [...]` | `/session:start code cab BPT2-6429 BPT2-6430` | new CAB coding session for those stories (bare `cab BPT2-…` also accepted) |
| Existing session name | `/session:start release` | coding session — resume it (bare name = implicit `code`; any type, incl. legacy plugin-named + feature sessions) |

**Fast-path flow:**
1. Run `pwd`, extract slug, read `~/.claude/plugins/user-config.json` (same as Step 1). Resolve `session_root` and `handle` using Path Resolution (`references/path-resolution.md`).
2. If arg is `mine`: set `filter_mine = true`, fall through to Step 1 — full discovery with mine filter.
2a. If arg is `refine` or `refine <target>`: resolve `session_root`/`handle` (step 1 above), then go directly to Step 4 → **Refine — enter refinement flow**, passing any `<target>` as the refine argument. Skip Steps 1–3.
2a′. If arg is `dispatch`: resolve `session_root`/`handle`, then read `commands/dispatch.md` and run it from Step 1 (assume the dispatch role, orient on the inbox — sessionless). Skip Steps 1–3. (Dispatch applies only in plugin/personal; `dispatch.md` itself stops cleanly in work/general.)
2a″. If arg is `capture` or `capture <idea>`: resolve `session_root`/`handle`, then read `commands/capture.md` and run it from Step 1 (assume the capture role, bank ideas as `capture`-type inbox entries — sessionless), passing any `<idea>` as the first idea to sniff. Skip Steps 1–3. (Capture applies only in plugin/personal; `capture.md` itself stops cleanly in work/general.)
2b. If arg is `code`, `code <target>`, or `code cab <keys>` (or bare `cab <keys>`): resolve `session_root`/`handle`, strip the `code` verb, and treat `<target>` exactly as a bare token in step 3 below (`code cab <keys>` / `cab <keys>` → new CAB kickoff). Skip Steps 1–3.
3. Derive session type and target name from the arg (story key → type=story, name=BPT2-XXXX; CAB key → type=cab; `cab <keys>` / `code cab <keys>` → new CAB; any other bare token → the `code` target — a session NAME to resume, or a `work` entry to graduate).
4. Check whether `<session_root>/<name>.md` exists (**this existence check IS "the file decides"** — a session file present means resume-coding; absent means graduate-work or kickoff):
   - **Exists + plugin session** → go directly to the Plugin session resume path in `start-plugin-classic.md` Step 4 (no `start-impl.md` read needed).
   - **Exists + other type** → read `start-impl.md`, go directly to its Step 4 (Resume existing) with that session.
   - **Does not exist + story/cab** → new kickoff: before Step 6, render the consolidated inbox (`inbox-render.py`, which auto-migrates) and check for a `[spawn]` entry whose label matches the target name. If found, archive it immediately with stamp `[PICKED UP YYYY-MM-DD — <target-name>]` to `<session_root>/_inbox_archive.md` (creating the archive file if needed), then **delete its `_inbox/<id>.md` file** (acp-ajudd#102). Read `start-impl.md`, then go to Step 6.
   - **Does not exist + plugin/personal** → do NOT blank-create. These types are item-driven: fall through to Step 1 (full discovery + inbox flow) so the target can be `code`d from the inbox, or scoped fresh via `refine <topic>`.
5. Skip Steps 2, 3 entirely — no session listing, no inbox counts, no routing block. (Plugin/personal "does not exist" falls through and does NOT skip — it runs the full flow.)

**No argument or unrecognized argument:** fall through to Step 1 — run the full discovery flow as normal.

---

### 1. Detect Zone, Resolve Cascade, and Route to Flow File

This is the dispatcher's own job — the only step that decides *which flow file* runs. It carries no per-zone or per-role branching itself; that lives in whichever flow file it hands off to.

Run `pwd` and extract the **last path component** as the repo slug (if not already done in Step 0):
- `/c/Users/ajudd/.claude/plugins/marketplaces/ajudd-claude-plugins` → `ajudd-claude-plugins`
- `/c/dev/gen-leadership-bonus` → `gen-leadership-bonus`

Resolve `session_root`, `handle`, and `zone` using Path Resolution (`references/path-resolution.md` — core resolution + § Zone Detection). If repo-based and `~/.claude/config/<slug>.json` is missing, auto-create it silently (see First-Run Auto-Config in `references/path-resolution.md`).

**Resolve `startFlow`** — plugin/personal zones only (story/cab/general have no wizard alternative planned, so treat them as `classic` without resolving the cascade): read Config Cascade (`references/config-cascade.md`), key `startFlow`, hardcoded default `classic`.

**Pick the target flow file**, checked in this order with a fallback:

| zone | preferred file | fallback |
|---|---|---|
| story, cab | `commands/start-work.md` | `commands/start-plugin-classic.md` |
| plugin, personal | `commands/start-plugin-wizard.md` when `startFlow == wizard` | `commands/start-plugin-classic.md` |
| general | — | `commands/start-plugin-classic.md` |

Check whether the preferred file exists:
```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
test -f "$ROOT/commands/<candidate>.md" && echo exists || echo fallback
```
If it doesn't exist, use the fallback. **This existence-check is the seam**: `start-work.md` (acp-ajudd#121) now exists, so story/cab zones route there — with **zero edits to this file**, exactly as designed. `start-plugin-wizard.md` (question-first wizard, acp-ajudd#122) does not exist yet, so plugin/personal zones still fall back to `start-plugin-classic.md` regardless of `startFlow`; the same existence check will pick it up the moment it ships, again with zero edits here.

Read the resolved flow file and continue from its **Step 2**, carrying forward `slug`, `session_root`, `handle`, `zone`, and `filter_mine` (if Step 0 set it).
