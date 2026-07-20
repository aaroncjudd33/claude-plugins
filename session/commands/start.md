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
   - **Exists + plugin session** → go directly to the Plugin session resume path in `start-classic.md` Step 4 (no `start-impl.md` read needed).
   - **Exists + other type** → read `start-impl.md`, go directly to its Step 4 (Resume existing) with that session.
   - **Does not exist + story/cab** → new kickoff: **before anything else — before even the inbox check below — print one line acknowledging the command was received and is running** (acp-ajudd#146 follow-up: this is the acknowledgment for the dead air that existed before the first checkmark, i.e. everything before Step 9's checklist even starts): `Got it — kicking off <name>. I'll post a ✨ line after each step as it completes.` This is a plain one-line printed statement, not a prompt — do not wait for a reply. Then continue: render the consolidated inbox (`inbox-render.py`, which auto-migrates) and check for a `[spawn]` entry whose label matches the target name. If found, archive it immediately with stamp `[PICKED UP YYYY-MM-DD — <target-name>]` to `<session_root>/_inbox_archive.md` (creating the archive file if needed), then **delete its `_inbox/<id>.md` file** (acp-ajudd#102). Read `start-impl.md`, then go to Step 6.
   - **Does not exist + plugin/personal** → do NOT blank-create. These types are item-driven: fall through to Step 1 (full discovery + inbox flow) so the target can be `code`d from the inbox, or scoped fresh via `refine <topic>`.
5. Skip Steps 2, 3 entirely — no session listing, no inbox counts, no routing block. (Plugin/personal "does not exist" falls through and does NOT skip — it runs the full flow.)

**No argument or unrecognized argument:** fall through to Step 1 — run the full discovery flow as normal.

---

### 1. Detect Zone + startFlow, Then Route

This is the dispatcher's own job — the only step that decides *which flow file* runs. It carries no per-zone or per-role branching itself; that lives in whichever flow file it hands off to.

**Lean by design (acp-ajudd#127).** The wizard's first move is a two-option ask ("refine or code?") — nothing before it should require more than knowing *which zone* and *which flow* to use. Everything else this command eventually needs (`session_root`, `handle`, the flow file's own content, the captures-waiting glance) is real work only once a target is being acted on, so it is **deferred until after the user answers** instead of front-loaded before they've said a word. This step therefore does exactly one combined read, in one shell call:

```bash
SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
UC="$HOME/.claude/plugins/user-config.json"
PC="$HOME/.claude/config/$SLUG.json"
echo "slug=$SLUG"
echo "--- user-config ---"
[ -f "$UC" ] && cat "$UC" || echo "{}"
echo "--- project-config ---"
[ -f "$PC" ] && cat "$PC" || echo "{}"
```

From that single output, compute (no further tool calls — this is plain reasoning over the text just read):

- **`zone`** — Zone Detection algorithm (`references/path-resolution.md` § Zone Detection) using `pwd` + the `user-config` fields (`paths.pluginMarketplaceName`, `paths.workReposDir`, `paths.personalProjectsDir`).
- **`startFlow`** — Config Cascade (`references/config-cascade.md`), key `startFlow`, hardcoded default `classic`: `project-config.startFlow`, else `user-config.startFlow`, else `classic`. (The `project-config` read above doubles as this tier's lookup — no separate file access needed.) The `wizard` flow is **shelved/experimental** as of v2.14.1 — opt in explicitly via `startFlow: wizard`; see acp-ajudd#129 for the open threads before re-enabling it as default.

**Do not** resolve `session_root`/`handle` yet, run the wizard/classic existence check, or read the target flow file yet — see Step 1a (wizard) / Step 1b (classic) below for when each of those happens.

**`startFlow == classic`** (default — the stable, tested flow; classic's own Step 2 is a listing, not an ask, so there's no ask to move earlier): resolve `session_root`/`handle` now via full Path Resolution (`references/path-resolution.md` — core resolution; auto-create `~/.claude/config/<slug>.json` per § First-Run Auto-Config if missing), read `commands/start-classic.md`, and continue from its Step 2, carrying forward `slug`, `session_root`, `handle`, `zone`, and `filter_mine` (if Step 0 set it).

**`startFlow == wizard`** (opt-in — experimental, shelved for revisit per acp-ajudd#129) → go to **Step 1a** below: ask immediately, before doing any more file I/O.

---

### 1a. Ask (wizard only) — the ~2-round-trip path

Print the zone-aware **labeled** role menu below and wait for one free-text reply — a bare "X or Y?" line doesn't tell a user what each verb *does*, so every option gets a one-line label (acp-ajudd#128). **Do not use AskUserQuestion.**

- **story, cab, general** (no inbox; 2 options):
  ```
  refine or code?
    refine — scope/plan work (sessionless)
    code   — open or resume a coding session
  ```
- **plugin, personal** (item-driven inbox; 4 options):
  ```
  refine, code, dispatch, or capture?
    refine    — scope/plan work (sessionless)
    code      — open or resume a coding session
    dispatch  — coordinate the inbox (sessionless)
    capture   — bank a raw idea (sessionless)
  ```

This is still the entire pre-ask sequence: one bash call (Step 1 above) + this one ask = the ~2 round trips the user sees before being asked anything, down from resolving full path state, existence-checking the flow file, reading it, and rendering a captures glance first (~8 round trips pre-#127). Labeling the options adds no extra round trip — it's the same one print, just self-explanatory. No behavior downstream of the reply changes — see Step 1b.

---

### 1b. After the Reply — Resolve, Open the Flow File, Continue (unchanged behavior)

Once the free-text reply above is in hand, do the work that used to happen *before* the ask, now that it's actually needed:

1. Resolve `session_root` and `handle` via full Path Resolution (`references/path-resolution.md` — core resolution). Reuse the `project-config` JSON already read in Step 1 rather than re-reading it. If `~/.claude/config/<slug>.json` was missing (empty `{}` in Step 1's output), auto-create it now per § First-Run Auto-Config.
2. Read `commands/start-wizard.md`. If it is missing for some reason, fall back to `commands/start-classic.md` instead (re-ask its Step 2 prompt in that case, since classic's flow shape differs — this fallback is not expected to trigger since #124 shipped the wizard file, but keeps the seam alive).
3. Continue in `start-wizard.md` from its **Step 2 processing** with the reply already collected — it does the captures-waiting glance and the eager-inference matching against this reply, then proceeds to Step 3 exactly as it always has. Carry forward `slug`, `session_root`, `handle`, `zone`, `filter_mine` (if Step 0 set it), and the reply.

Nothing about how a reply is interpreted, how targets resolve, or what happens after the pick changes — only *when* the path resolution / flow-file read / captures glance happen shifts from before the ask to after it.
