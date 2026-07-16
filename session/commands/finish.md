---
name: finish
description: End-of-day close — full checklist; Jira, Teams, Confluence, and browser steps run conditionally by session type.
---

# Session Finish

Full end-of-day close. Runs the complete checklist to ensure nothing is left behind.

## Finish is the explicit close — all-or-nothing, backed by a deterministic helper (acp-ajudd#103), run by self-finalize by default (acp-ajudd#109)

**`/session:finish` is the ONE thing that declares a coding session done.** It is un-bundled from the deploy (Session Skill § The dispatch↔code loop — deploy stays code's authority; the *close* is this command). Two hard rules govern it:

1. **All-or-nothing tie-out — performed by `finish-close.py`, not by prose (acp-ajudd#103).** The record close touches five surfaces — **frontmatter `status:` + body `Status:` + `_index.md` row flip together**, the `[DONE]` archive stamp is written, `_active` is cleared, and history + worklog are appended. #94 shipped this as a *prose* rule and it still did not land: three sessions in a row (#85, #96, #95) needed a manual dispatch tie-out because the model did the loud half (deploy + return block) and dropped the quiet half (the record close) — prose cannot make a multi-step write atomic. So the whole close now runs through **one deterministic call** (`session/scripts/finish-close.py`, Step 12a): the model composes the *content*, the script performs *all five writes* in one all-or-nothing act, or exits non-zero having changed nothing. It also **self-verifies before exiting 0** (acp-ajudd#107 FIX 0) — this is exactly what makes #109's self-finalize safe (a self-finalize cannot silently partial-fail). **Never approximate the close with a manual commit + a prose edit, and never hand-write the surfaces piecemeal** — that approximation IS the bug this fixes. The **safe-to-close cue is gated on the script's success** (Step 12a) — a session cannot signal "done" unless the close actually ran. A coding session either completes `finish-close.py` or it is still open.

2. **Who fires the close — self-finalize by default; the validated signal in the toggle-off path (acp-ajudd#109).** How this command gets triggered depends on the work order's `Self-finalize` field (Session Skill § The dispatch↔code loop):
   - **Default (`Self-finalize: yes`, or a solo / bare `code` session):** the coding session, having **self-validated** its build against the Done-whens, runs `/session:finish` **itself** — build → self-validate → finish → done. This is self-triggered but still an **explicit invocation** (Claude runs the command after validating), never an implicit side-effect of a build.
   - **Toggle-off (`Self-finalize: no`):** the happy path is *build → deploy → report `State: implemented-deployed`* and **stops, session still active** (Session Skill § The dispatch↔code loop). This command then runs on **either** (a) the **human** running `/session:finish` on seeing `safe-to-close`, or (b) a dispatch/planning handoff note carrying **`Action: finish`** ("validated — run `/session:finish`", renamed from `close`) pasted into this terminal. On this path the close returns a **`State: finished`** confirmation (Step 12b).
   - **Human-typed finish ALWAYS closes — with a heads-up when unvalidated (acp-ajudd#104, decision B+heads-up).** A human running `/session:finish` in the terminal always closes, even if the handoff said `Self-finalize: no` (the human is the ultimate authority; editing is never policed — acp-ajudd#1). But when this session was flagged `Self-finalize: no` **or** has no dispatch validation on record, print **one heads-up line first** and then proceed — see Step 0b. **Inform, never block.**

Everything below is the mechanics of that close.

## Instructions

### 0. Read Session Context

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (`references/path-resolution.md`).

Determine the session name from conversation context:
1. Look back at the current conversation for the most recent "Resuming `<name>`" line (from session:start) OR "Switching to `<name>`" line (from session:switch). Use whichever is most recent.
2. If neither is found in this conversation, fall back to reading `~/.claude/memory/sessions/<slug>/_active` as a hint.

**Session guard (command-level enforcement — acp-ajudd#1).** `finish` closes the active session, so a session must exist. If neither the conversation context nor `~/.claude/memory/sessions/<slug>/_active` yields a session name, **stop cleanly** — do not ask, do not treat as a general session, do not proceed:

```
No session established for <slug>. Run /session:start first.
```

Editing files is never blocked; the session commands are what require a session. (`start` / `refine` and read-only views are exempt.)

Read `<session_root>/<name>.md` and extract:
- `type` (plugin / story / cab / personal / general)
- `name`
- `title` (story/cab only — may be absent in older session files; treat as empty string if missing)
- `teams_chat`
- `branch`

If the session name is determined but `<session_root>/<name>.md` does not exist, warn the user: "Session file for `<name>` not found — run `/session:start` to re-establish." and stop.

### 0b. Human-Finish Heads-Up — inform, never block (acp-ajudd#104)

A **human** running `/session:finish` **always** closes — the human is the ultimate authority (editing is never policed — acp-ajudd#1) — regardless of the work order's `Self-finalize` field. But when this session is closing **without validation on record**, surface it in **one line** first, then proceed with the close. Emit the heads-up when **either** holds:
- the session was picked up under **`Self-finalize: no`** (check the `## Picked up from inbox` provenance / the pickup work order for the toggle), **or**
- there is **no dispatch validation on record** (no `safe-to-close` signal and no `Action: finish` note was received in this terminal — i.e. the human is finishing a shipped-but-unvalidated `Self-finalize: no` session on their own).

```
Heads-up: this session was self-finalize:no and dispatch hasn't validated — closing anyway per your explicit finish.
```

Do **not** block, do **not** ask for confirmation — print the line and continue to the close. (Issues arising *during* the close are caught by `finish-close.py`'s self-verify — acp-ajudd#107 FIX 0 — not by this heads-up.) In the **default self-finalize path** (`Self-finalize: yes`), the coding session self-validated before invoking finish, so no heads-up is needed. Skip this step entirely for story / cab / general (no dispatch layer) and for a bare solo `code` session with no toggle on record.

### 0a. Retention Prune (acp-ajudd#50)

Run the age-based retention prune **before anything else** — it must complete before the git scan (Step 2, which may commit) and well before the deploy (Step 11), so it never races a commit or leaves a half-archived state to be committed. It is idempotent, fail-safe, and never touches in-progress/paused sessions — so it cannot archive the session you are currently finishing (it becomes `completed` only in Step 9, and even then it is fresh, not >6 months old).

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
if command -v python3 >/dev/null 2>&1 && [ -f "$ROOT/scripts/session-archive.py" ]; then
  python3 "$ROOT/scripts/session-archive.py" --session-root "<session_root>" --slug "<slug>"
fi
```

If it prints a `Retention: archived …` line, relay it — archival is never silent. For repo-based sessions the moved files and the trimmed `_index.md` are picked up by this finish's own commit/push (they were archived before staging); for local sessions the archive is local. Either way the prune is done before any commit runs.

### 1. Header

Output:
```
Session Finish — <name> (<type>)
<DayOfWeek>, <Month> <Day>, <Year>
================================================================
```

### 2. Git Scan

| Type | Scope |
|------|-------|
| plugin | `~/.claude/plugins/marketplaces/<pluginMarketplaceName>` (read from user-config) |
| story | current working directory (work repo) |
| cab | current working directory — check release branch specifically |
| personal | current working directory |
| general | skip |

**Run all git checks in parallel:**
- Uncommitted/unstaged changes (`git status`)
- Stashed changes (`git stash list`)
- Unpushed commits (`git log --oneline @{u}..HEAD 2>/dev/null`)
- Current branch name

Report anything that could be lost.

**Non-plugin types — always commit and push, no question asked (acp-ajudd#140, confirmed with Aaron 2026-07-16).** If uncommitted changes exist, commit them now as part of the close, using a message summarizing the work, **and push** (nothing else pushes for a non-plugin close if `/session:commit` was never run mid-session — story/cab/personal push during `commit`, per the polymorphic-lifecycle table, so this close is the only remaining chance). Report it informationally, e.g. "Committed and pushed `<sha>` — `<subject>`." **Never ask "Want to commit before closing?"** — `finish` means done, and there is no case where you'd want to walk away from a finished session with something left uncommitted. This mirrors the "finish = done, ship it" judgment call already applied to plugin type below and to Step 7's batch. The existing `session-commit-guard.py` pre-commit hook (secrets/PII scan) remains the real backstop for anything that shouldn't be committed — that was never what this question was protecting against. (Observed live twice, 2026-07-16, `virtual-office` BPT2-6532: "why are you asking me about committing files... that should mean everything ended in a completed and committed state." — being asked implied the commit might not have happened, which is the opposite of what `finish` is supposed to guarantee.)

**Plugin type:** do NOT prompt for a separate commit here. Uncommitted changes and unpushed local commits (from `session:commit`) at plugin finish are the work being shipped, and the **deploy step (Step 11) commits, bumps, pushes, and reinstalls them IF NOT ALREADY SHIPPED** (the atomic close, Step 12a, is the terminal write after it — it flips status, stamps `[DONE]`, appends history + worklog, and clears `_active`). Report them as informational only, e.g. "Uncommitted changes + N local commits — will ship in the deploy step," never as at-risk. Note (acp-ajudd#94): on the orchestrated happy path the ship already ran at build-end, so at close the tree is usually **clean** and Step 11 is a no-op — a clean tree here is normal, not a problem; finish is then the close, not the deploy.

If clean: "Git: clean" (for plugin, this means there is nothing to deploy — note that Step 11 will be a no-op).

### 3. Memory

Review the conversation for anything worth saving:
- Feedback, corrections, or rules established
- Workflow or convention changes
- Project or session state updates
- Anything non-obvious that future sessions should know

Save what's missing. Report: "Saved: [list]" or "Memory: nothing new to save."

### 4. Jira Update *(story/cab only)*

**plugin / personal / general:** Skip this step entirely — do not read the reference.

**story / cab:** Read `references/finish-story-cab.md` (Step 4 section) and perform the Jira actions silently before the batch block. (The reference is loaded once here and also supplies the Step 6 prep additions, the Step 7 story/cab slot bodies, and the Step 9 post-deployment checks — keep it in context for the rest of this finish.)

### 5. Scope Scan

Read the `Scope:` field from the session file. If the field is missing or the session type is `general`, skip this step.

The `Scope:` field may hold **one path or a comma-separated set** (a multi-plugin feature declares every plugin dir it touches — acp-ajudd#54). Split on `,`, trim each entry, and resolve each: if an entry is relative, resolve it as `local_cfg.projectRoot + "/" + entry` (read `local_cfg` from `~/.claude/config/<slug>.json`); for legacy sessions with absolute scope, use as-is.

Review file paths that were accessed or modified during this conversation (Read, Edit, Write, Bash file operations). A path is in-scope if it begins with **any** of the resolved scope paths; only paths under **none** of them are out-of-scope. A multi-plugin feature's own declared surface is in-scope by design — only edits outside the item's declared plugin set are the leakage this scan is for (acp-ajudd#54).

**If out-of-scope items found — hard block.** Show prominently before the batch block and wait (Pattern 5 — finish is a hard block, not a warn):

```
Cross-scope work detected — cannot close this session cleanly.

  Out-of-scope changes:
    · <file path>  (belongs in: <target slug> / <target session>)

Resolve before closing:
  (1) Route to <target> inbox?    yes / note / cancel
```

- **yes (route):** invoke `/session:inbox` flow with the out-of-scope item pre-populated. Choosing `route` IS the go-ahead — `/session:inbox` writes it directly and surfaces the `Sent inbox item <id> to <target> inbox` line (free rein + visible, never silent — acp-ajudd#5; no separate pre-write approval). Once routed, continue to batch block.
- **note:** record excluded work in Open items, no inbox write. Continue.
- **cancel:** stop. Do not write session summary or deactivate.

Only proceed to the batch block once all flagged items are resolved.

### 6. Pre-Batch Preparation (Silent)

Before assembling the batch, gather contextual data needed to build the batch items. **Run all applicable reads in parallel — issue them as a single batch before processing any result.**

Universal reads (all types):

1. **Inbox file — fresh read at close (acp-ajudd#6).** The recap must reflect the *live* inbox, not a snapshot taken at session start — a concurrent `refine` pass or another terminal may have added items while this session ran.
   - **plugin / personal (item-driven):** **render the consolidated inbox fresh, now** via `inbox-render.py` (auto-migrates on access; parse stdout, relay any stderr notice — `references/inbox-convention.md` § Per-item storage mechanics) — do NOT reuse a session-start snapshot, and do NOT look for a per-session `_inbox_<name>.md` (item-driven sessions are fold-then-archive; that file does not exist for them). **Exclude** any item this session folded at pickup or marked completed; **include** everything else currently in the dir (so concurrently-added items appear).
   - **story / cab / general:** read the per-session `<session_root>/_inbox_<name>.md` (these are not item-driven — a per-session handoff file is correct). Same fresh-read discipline.
   - **Parser (both):** count and list **by the `## <id> · [date…]` header lines**. **Skip the `> [type: … · status: …]` metadata line** under each header (legacy `> [status: …]` and older `> [type: story/note/data · status: …]` all tolerated — see `references/inbox-convention.md` § Inbox Model back-compat) — it is entry metadata, not a separate entry and not body content; never miscount it. Tolerate legacy entries with no `<id>` prefix and no metadata line. **Exclude `capture`-type entries** from the pickup sweep (acp-ajudd#10) — they are not work to close out; they're read/archived only on request (§ Captures inbound). Categorize each `work` entry (`status: new` / `refining` / `ready`) as in-progress (has an `[in-progress — …]` marker) or pending.
2. **Plugin version:** if type is plugin, read current version from `plugin.json`.
3. **Loaded memories:** read the session file's `- **Loaded memories:**` field. If it has entries, note them for the validate-shape of batch item (A2). If absent or empty, (A2) takes its capture-only shape — it is always presented.

**story / cab only:** also issue the type-specific prep reads (epic file, story doc path, browser, Teams guide pre-fetch) from `references/finish-story-cab.md` (Step 6 section) in this same parallel batch.

**CDK detection (story/cab only — run once before building the batch):**
```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
CDK_PRESENT=""
[ -n "$REPO_ROOT" ] && { [ -f "$REPO_ROOT/cdk.json" ] || [ -d "$REPO_ROOT/cdk" ]; } && CDK_PRESENT=true
```
If `REPO_ROOT` can't be resolved, leave `CDK_PRESENT` unset and default to showing Slot A (no silent loss of the gate for real infra work).

### 7. Finish Batch

Gather all pending questions and present as **one batched block**. Output and wait (Pattern 2). **Do not use AskUserQuestion.**

**Plugin type — smart defaults (finish = done, ship it).** For a plugin session Aaron is planner + coder + tester + QA in one seat, so finish should NOT interrogate him slot-by-slot. Claude owns the routine judgment calls and only surfaces genuine exceptions; a bare `go` performs the full sensible close. This is the opposite of story/cab, whose batch stays prompt-heavy **by design** (external Jira/CAB/QA gates that Claude cannot decide). Concretely, for plugin type:

- **Memory capture (A2):** do not ask `skip / new`. Claude reviews the session itself, decides whether there is project/session knowledge worth saving, and captures it — reporting the outcome (`Captured: <name>` or `Memory: nothing new`). Override honored ("capture X, this way"), but the default is "you assess and do it."
- **Plugin reviewed (F):** when this finish is deploying (Step 11 will run), the review is **mandatory, not optional** — run it automatically rather than presenting `skip / yes`. A deploy without a review is not acceptable.
- **Open items completed this session (G/H/I):** items that were *this session's* picked-up `[inbox]` work and got completed are **auto-marked done** (show the reasoning, e.g. "marking done — completed this session"), not left open and re-asked.
- **Net:** a bare `go` runs capture-if-relevant (Claude's call) → review → mark completed items done → then the deploy (Step 11) → the atomic close (Step 12a — status flips + `[DONE]` + history + worklog + `_active`, one all-or-nothing call) → return handoff if this session was fed a note (to dispatch if orchestrated, a courtesy note to planning if planning-fed solo) → the ✅ close cue (Step 12c, gated on the close). Aaron overrides only exceptions.
- **Empty batch → no stop.** After applying these defaults, if no slots remain that genuinely need a decision, do NOT present an empty batch and wait — report the auto-resolutions (captured memory, auto-done items, review result) as informational output and proceed straight through Steps 8–12. Only stop at the batch when at least one ambiguous slot survives.

The slot bodies and apply-logic below note where this default changes behavior for plugin type. **Story / cab / personal / general are unchanged** — they keep their explicit prompts.

**Batch skeleton — canonical slot order.** Assemble the numbered list by walking these slots in order, omitting any whose condition isn't met, and assigning each surviving slot the next running number `(N)`. Universal slots (and the plugin-only F) are defined inline below; story/cab slot bodies live in `references/finish-story-cab.md` (already loaded in Step 4 for story/cab sessions). For plugin / personal / general sessions the story/cab slots are simply absent — never read the reference for them.

| Slot | Item | Applies to | Body |
|------|------|-----------|------|
| A  | CDK/DynamoDB check            | story/cab + CDK_PRESENT | `references/finish-story-cab.md` |
| A2 | Memory validation + capture   | **all**   | inline below |
| B  | Epic update (+B+1 Confluence) | story/cab | `references/finish-story-cab.md` |
| B2 | Epic validation for CAB       | cab       | `references/finish-story-cab.md` |
| C  | Confluence story page         | story/cab | `references/finish-story-cab.md` |
| D  | Story doc                     | story     | `references/finish-story-cab.md` |
| E  | Browser                       | story     | `references/finish-story-cab.md` |
| F  | Plugin reviewed               | plugin    | inline below |
| G  | Open items                    | all       | inline below |
| H  | In-progress inbox items       | all       | inline below |
| I  | Legacy [inbox] Open items     | all       | inline below |
| J  | Pending inbox sweep           | all       | inline below |
| K  | Teams update                  | story/cab | `references/finish-story-cab.md` |

**Inline slot bodies (universal + plugin):**

**(A2) Memory validation + capture** — **always include this item** (for any session type). This closes the context-rot loop and provides the finish-time opportunity to record project knowledge. Two shapes:

- **If the session has loaded memories** (from Step 6 item 3): every memory that influenced this session's work gets an accuracy check, plus the option to capture a new one.
  ```
  (N) Loaded memories (M) — validate for accuracy, and capture anything new?    skip / review / new / both
  ```
- **If no memories were loaded:** offer capture only — especially valuable when work touched an area with no memory yet.
  ```
  (N) Capture anything from this session as a project memory?    skip / new
  ```

**Plugin type — A2 is not a batch question.** Do not present the `skip / review / new / both` (or `skip / new`) prompt in the batch. Instead, Claude assesses the session itself: validate any loaded memories for accuracy automatically (drop/update stale ones, per the apply-logic), and capture new project/session memory if warranted. Report the outcome outside the batch (`Captured: <name> [<label>]` / `Memory: nothing new`). If genuinely uncertain whether a specific capture is worth making, that single item may be surfaced — but the default is decide-and-do, not ask.

**(F) Plugin reviewed** — plugin type only.

- **If this finish is deploying** (there is work to ship, so Step 11 will run): the review is **mandatory — auto-run it, do not present a skip/yes prompt.** Run the plugin review automatically before the deploy and report the result. A deploy without a review is not acceptable.
- **If this finish is NOT deploying** (clean tree, Step 11 is a no-op) and `plugin_reviewed` is missing, a legacy value, or MAJOR.MINOR differs, it may still be offered:
  ```
  (N) Plugin reviewed? (last: v<stored>, current: v<current>)    skip / yes
  ```

**(G) Open items** — if there are non-`[inbox]` Open items:
```
  (N) Open items done?
        1  [item one text]
        2  [item two text]
     skip / all / <number(s)>
```

**(H) In-progress inbox items** — one per item found in Step 6:
```
  (N) [<id>] Inbox [in-progress]: "<description>"    keep / done
```

**(I) Legacy [inbox] Open items** — any `[inbox]` tag with no corresponding in-progress inbox entry:
```
  (N) Open item [inbox legacy]: "<text>"    keep / done
```

**Plugin type — auto-resolve this-session's completed work (G/H/I).** For plugin sessions, any G/H/I item that was **this session's picked-up work AND got completed** is marked done automatically — not presented as a question. Detection heuristic: `[inbox]`-tagged Open items (or in-progress inbox items) matching the work this session picked up, when the session actually produced the corresponding changes. Show the resolution with reasoning outside the question set, e.g.:
```
  Auto-resolved (completed this session):
    ✓ [inbox] Make session:finish the plugin deploy — marking done
    ✓ [inbox] session:commit = local checkpoint — marking done
```
Only items that are genuinely ambiguous (started but not clearly finished, or unrelated to the picked-up work) remain as batch questions. If uncertain, default to **done** for plugin type (finish = done) with an easy override — the user can reply `<n> keep` to reopen any auto-resolved item. Story/cab/personal/general keep the explicit `skip / all / keep / done` prompts unchanged.

**(J) Pending inbox sweep** — one per pending inbox item (single-line provenance form — see `references/inbox-convention.md`):
```
  (N) [<id>] Inbox pending: "<description>"  ·  ↳ <session> (<type>) — addressed this session?    nothing / done / picked-up
```
Lead with the item's stable `[<id>]` (omit for legacy items that have none). Include `<slug>` in the `↳` when the item's source repo differs from the current slug; drop it when same-repo; omit `(<type>)` for legacy items.

**Assembled block example (story type):**
```
  (1) CDK/DynamoDB patterns verified?    not-applicable / yes / remind
  (2) Loaded memories (2) — validate for accuracy, and capture anything new?    skip / review / new / both
  (3) Epic update (BPT2-6300) — mark story done and record final notes?    skip / yes
  (4) Push epic update to Confluence architecture page?    skip / yes
  (5) Update Confluence page for this story?    skip / yes
  (6) Story doc — update existing?    skip / yes
  (7) Open items done?
        1  Fix scope guard edge case
     skip / all / 1
  (8) [vo-ajudd#4] Inbox [in-progress]: "Update session tests"    keep / done
  (9) [vo-ajudd#12] Inbox pending: "Review DynamoDB schema"  ·  ↳ BPT2-6258 (story) — addressed?    nothing / done / picked-up
  (10) Post closing update to BPT2-6258 — Shopify Member Agreement?    skip / yes

Reply with overrides or "go".
```

**Parsing:** `go` accepts all defaults. Parse freely: `3 yes 6 yes 10 yes`, `all skip`, `8 done 10 yes`, etc.

**Applying answers:**

For **story/cab slots (A, B, B2, C, D, E, K)** the apply-logic lives in `references/finish-story-cab.md` (Step 7 sections) — already in context. The universal/plugin slots are applied here:

*(A2) Memory validation + capture:* (run after the batch is processed — these are justified follow-ups since per-memory dispositions and new-memory content can't be known in advance)
- **review:** run the staleness check (scoped mode) from the memory plugin's `references/staleness-check.md` against the session's loaded memories. Present only the **flagged** files (unresolved code references) as a batch — clean loaded memories are kept automatically and skipped. Apply per `/memory:groom` Steps 2–3 (scoped). If all loaded memories are clean: skip the review, surface only the capture offer. Any memory deleted is dropped from the session's `Loaded memories:` field in Step 9. If the memory plugin is not installed, fall back to inline review: read each file, show it, and ask `keep / update / delete`.
- **new:** run the memory plugin's `/memory:save` flow — infer the feature area from this session's work, propose a `feature:X/Y` label + name + body, and on confirm write the file, update `MEMORY.md`, and add it to the session's `Loaded memories:` field. Offer to capture more than one if the session spanned distinct areas. If the memory plugin is not installed, fall back to writing the file inline using the `feature:X/Y` convention.
- **both:** run review first, then capture.
- **skip:** leave memories untouched. (Skipping review means nothing needed revision; skipping capture means nothing new to record.)

*(F) Plugin reviewed:*
- **yes:** update `Plugin reviewed: <current-version>` in the session file.
- **skip:** leave as-is.

*(G) Open items:*
- **all:** remove all non-`[inbox]` items from the list.
- **<number(s)>:** remove those items.
- **skip:** keep all open.

*(H) In-progress inbox items:*
- **done:** strip `[in-progress — ...]`, archive with `[DONE YYYY-MM-DD]`, remove from inbox, remove `[inbox] <item>` from Open items. **Archive file is type-aware:** the single `_inbox_archive.md` for plugin / personal (item-driven — "remove from inbox" = **delete the item's `_inbox/<id>.md` file**, acp-ajudd#102), `_inbox_<name>_archive.md` for story / cab / general.
- **keep:** no change. Will carry as in-progress to next session.

*(I) Legacy [inbox] items:*
- **done:** remove `[inbox] <item>` from Open items.
- **keep:** no change.

*(J) Pending inbox sweep:*
- **done:** archive with `[DONE YYYY-MM-DD]`, remove from inbox (plugin / personal → **delete the item's `_inbox/<id>.md` file**, acp-ajudd#102).
- **picked-up:** insert `[in-progress — <session-name>, YYYY-MM-DD]` after `## [date]...` header (plugin / personal → edit that item's `_inbox/<id>.md` file); add `[inbox] <item>` to Open items.
- **nothing:** skip.

**Auto-purge archive:** After handling inbox items, if the archive file exists, drop entries whose `[DONE YYYY-MM-DD]` date is more than 30 days before today. Rewrite with only retained entries (preserving the header line).

### 8. History Entry — compose only (the close script appends it)

Compose a 1-sentence description of the work accomplished this session. Write it as a complete thought that stands alone without conversation context. Format the full line as:

```
[YYYY-MM-DD @<handle>] <session-name> — <accomplished sentence>
```

**Do NOT append it to `_history.md` here.** The atomic close (Step 12a) appends it — `_history.md` is one of the five surfaces `finish-close.py` writes as a single all-or-nothing act (acp-ajudd#103), so a separate prose append here would double-write and re-open the drift #103 closes. Hold the composed line in context; it is also the value for `Last worked on` in the session file (Step 9). **Do not re-read `_history.md`.**

### 9. Session Summary

**Before writing — close-readiness gate (acp-ajudd#94). This runs FIRST, before any `completed` write.** The close must not silently declare done what isn't done:

- **A gated OUTWARD leg still pending is an unresolved Open item — never swallow it.** If any outward deliverable this session was meant to produce is still unshipped — a **Confluence publish** awaiting review, a **Teams send** not yet sent, a **PR** not opened, a **deploy** that didn't run — it is by definition unresolved. Do **NOT** mark the session `completed` around it. Surface it plainly and **block**, e.g.:
  ```
  Cannot close — a gated deliverable is still pending:
    · Confluence page <id> — drafted, NOT published (awaiting review)
  Resolve first: publish it now, or explicitly carry it forward as an Open item / route to inbox.
  ```
  This is the acp-ajudd#94 live case: `session-confluence-rewrite` was flipped `completed` while the Confluence publish (a gated outward leg) had not happened — the session reported done while the deliverable didn't exist. Treat a pending outward leg exactly like an out-of-scope item in Step 5: resolve, carry-forward, or route — never close silently over it.
- **No unresolved Open item is closed over silently.** Any Open item still open at this point is either (a) resolved now, (b) explicitly carried forward (written into the completed session's `Open items:` / `Next steps:` as a deliberate hand-off), or (c) acknowledged by the human. Carrying an item forward is a legitimate acknowledgement; *dropping* one without a trace is not.

**Coding-finish writes the `[DONE]` completion stamp — compose the note; the close script stamps it (acp-ajudd#94/#103, #42 completion-authority).** Completion authority is coding-finish's alone (Session Skill § State-Exclusivity). This session's picked-up `work` entry was folded-and-archived at pickup as a `[CONSUMED <date> → session <name>]` line in `_inbox_archive.md`; at this close it must **also carry `[DONE YYYY-MM-DD — <note>]`** so the archive ledger and the session file's `status: completed` stay consistent. **Do NOT hand-edit `_inbox_archive.md` here** — the atomic close (Step 12a) locates the entry by its `## <id> ·` header (never by the nearest `[CONSUMED]` line — that mis-resolved #102's close; acp-ajudd#107 Defect 3) and inserts the `[DONE]` stamp within that header-bounded block as part of its one all-or-nothing write (this is exactly the stamp that had to be written by hand in the #94/#96/#95 live cases — #103 makes it deterministic, #107 makes it self-verified). Your job now is only to **compose the `done_note`** — a short completion note, e.g. `shipped v1.82.0 via session <name>`. Record the item `<id>` from the session file's `## Picked up from inbox` provenance; it is passed to the script as `--item-id`. If this session picked up no inbox entry (a bare `code <name>` with no provenance), `--item-id` is empty and the stamp is skipped.

**Reconcile-consume if the pickup was skipped (acp-ajudd#115).** Normally the item was consumed at `/session:start code #X` and is already a `[CONSUMED …]` line in the archive; this close just adds `[DONE]`. But if the mandatory pickup was skipped and the item is **still live** in `_inbox/<id>.md`, `finish-close.py` **reconciles** — it consumes the item (fold-then-archive with `[CONSUMED]` + `[DONE]`) as part of this same atomic close and prints a one-line `RECONCILED` note. This structurally prevents a session ending with its work both live-as-`ready` AND shipped (#13), even when the pickup was missed. You do nothing extra here — just pass the correct `--item-id` (from provenance, or from the pasted work order's `pick up #X` if this session was coded straight from paste with no provenance block); the script detects the live item and reconciles. (For **story / cab / general** the per-session `_inbox_<name>_archive.md` is still covered by the Step 7 `[DONE]` handling; the close script's stamp is the plugin/personal item-driven path.)

**Before writing — tag any untagged items:** For each Open item that does not already start with `[YYYY-MM-DD @`, prepend `[today @<handle>] `. Preserve existing tags as-is.

**Story type only — post-deployment checks:** Run the post-deployment-checks prompt from `references/finish-story-cab.md` (Step 9 section, already in context). Skip entirely for non-story types.

**Derive `Next steps` — do not ask.** Use only mine-tagged items. Check in order:
1. Remaining items in the fresh inbox read from Step 6 (pending or in-progress) — **plugin / personal → the consolidated `_inbox/` (rendered via `inbox-render.py`)**; **story / cab / general → `_inbox_<name>.md`** → `[today @<handle>] See inbox — N items pending` (N counted by `## <id>` header lines in the rendered stream, not the metadata line)
2. Non-`[inbox]`-tagged Open items → use the first mine-tagged item's text as the next step
3. Story/CAB type → check Jira status and branch state for a concrete action. **Never suggest "create PR to master", "merge to master", or any variant.** If the story is otherwise complete: "Hand off to /release:create when ready to deploy."
4. If none of the above apply → ask: "What's the first thing to pick up next time? (or 'skip')"

After deriving, offer routing for a **new** item as a brief inline prompt:
```
Route next step → inbox (ready) / backlog (defer) / skip (keep as-is)
```
- **inbox:** invoke `/session:inbox` targeting this same session. Add `[today @<handle>] See inbox` to Next steps.
- **backlog:** write to `<session_root>/_backlog_<name>.md` (plugin) or `<session_root>/_backlog.md`. Set Next steps to `none`.
- **skip:** keep the derived Next steps as-is.

Write `<session_root>/<name>.md` with the final state:

**Frontmatter:** for `plugin` and `personal` types, write `type:` and `status:` keys alongside `updated:`. At finish, `status: completed` — this is what excludes the session from the default `/session:start` resumable listing (the file is never deleted). For `story` / `cab` / `general`, write only `updated:` (preserve any existing extra keys as-is). **No `mode` key — a session is always a coding session (acp-ajudd#16); drop `mode:` from any older file rather than preserving it.**

```
---
updated: [today's date]
type: [type]            ← plugin/personal only
status: completed       ← plugin/personal only; marks the session done (file kept, hidden from default listing)
---

# Session State — <name>

- **Type:** [type]
- **Name:** [name]
- **updated-by:** @<handle>
- **created-by:** @<original-handle>   ← read from existing file; preserve as-is — never overwrite
- **Title:** [Jira summary]   ← story/cab only; omit for other types
- **Category:** [category]   ← general only, omit for other types
- **Teams chat:** [teams_chat or "none"]
- **Scope:** [scope path]   ← preserve from existing file; write relative if new; omit for general
- **Status:** completed
- **Branch:** [branch or "n/a"]
- **Last worked on:** [the entry composed and written in Step 8 — use that value directly; do not re-read _history.md]
- **Open items:**
  - [YYYY-MM-DD @<handle>] <item text>   ← all items tagged; "none" if empty
- **Next steps:**
  - [YYYY-MM-DD @<handle>] <next step>   ← array format; "none" if no next step
- **Loaded memories:**   ← preserve surviving entries (drop any deleted during Step 7 memory validation); omit the field if none
  - <name>  [<label>]
- **Commits:**   ← preserve existing entries exactly as-is; omit the field if not present. Written by session:commit
  - [YYYY-MM-DD] <short-sha> — <commit subject>
- **Plugin reviewed:** <version>   ← plugin type only; omit for other types
- **Related CAB:** [CAB-XXX or "none"]   ← story type only, omit for other types
- **Post-deployment checks:**   ← story type only; omit if field not present
  - [ ] <check description>
  - [x] <acknowledged check description>
- **Related stories:** [BPT2-XXXX, BPT2-YYYY or "none"]   ← cab type only, omit for other types
- **linked_sessions:** [<session-name>, ...]   ← preserve as-is; omit if not present
```

**Backward compat:** If the existing session file has a `Project:` field, preserve it. If `- **Next step:** <text>` (scalar), re-write as `- **Next steps:**` array tagged `[today @<handle>]`. `Commits:` is preserve-only at this step (written by session:commit) — for plugin type, the deploy (Step 11) appends its deploy commit afterward. `Loaded memories:` carries forward minus anything deleted during the Step 7 memory-validation item.

Write the session file **body** with all its semantic fields (Open items, Next steps, Loaded memories, Commits, etc.). Write `status: completed` / `- **Status:** completed` per the template — but the **authoritative** flip across all three status surfaces (frontmatter + body + `_index.md` row) is performed by the atomic close in Step 12a, not by hand here.

**Do NOT hand-write `_index.md` and do NOT hand-flip the status lines as separate steps (acp-ajudd#103).** The `_index.md` row update, the frontmatter/body status flips, the `[DONE]` archive stamp, and the `_history.md` + worklog appends are **all performed together by `finish-close.py`** in Step 12a — as one all-or-nothing call, or nothing. This replaces the old ~5 separate prose write-steps whose piecemeal nature was exactly what let the close drift (frontmatter flipped while `_index` lagged; the `[DONE]` stamp dropped; `_active` left set — the #94/#96/#95 live cases). The model composes the *content* (history line, worklog block, `done_note`, and this session-file body); the script performs the *writes*.

**After the atomic close runs (Step 12a) — update approved-hash (repo sessions only):** because the hash must cover the final, status-flipped file, recompute it **after** Step 12a, not here:
```bash
git hash-object "<session_root>/<name>.md" > ~/.claude/memory/sessions/<slug>/<name>.approved-hash
```

**General sessions only:** Also check `~/.claude/memory/sessions/<slug>/<name>/` — if notes, decisions, or outputs were produced today, ensure they are written there before closing.

Print the summary to screen. **For plugin type, this is not the final output** — the deploy (Step 11) runs while the session is still active, then the atomic close (Step 12a) ties out the record and clears `_active`, and the ✅ close cue (Step 12c) is the true last line. For all other types, the atomic close (Step 12a) followed by the ✅ cue is the final output.

### 10. Work Log — compose only (the close script appends it)

**Compose** the worklog entry now; **do NOT append it here.** The atomic close (Step 12a) writes it to `~/.claude/memory/worklog/<YYYY-MM-DD>.md` — the worklog is the fifth surface `finish-close.py` writes, so a separate append here would double-write. Use today's date for the target filename and the current local time (HH:MM) for the entry header. Hold the composed block in context for the close call.

Entry format varies by type:

- **story/cab with title:** `## <HH:MM> — <name> — <title> (<type>)`
- **story/cab without title** (older session files): `## <HH:MM> — <name> (<type>)`
- **plugin:** `## <HH:MM> — <name>` (no type label — the name is self-identifying)
- **personal/general:** `## <HH:MM> — <name> (<type>)`

```markdown
## <HH:MM> — <formatted header per above>

**Accomplished:** <most recent entry from _history.md>

**Open items:** <open items from session state, or "none">
```

Multiple entries per day are expected — always append, never overwrite.

### 11. Deploy — plugin type only, IF NOT ALREADY SHIPPED (runs before the atomic close)

**Deploy is un-bundled from close (acp-ajudd#94), and this step deploys-if-not-already (acp-ajudd#109).** In the **default self-finalize path** the coding session ran no separate ship — it went build → self-validate → finish — so **this step performs the deploy** (bump + push + reinstall): finish is the ship *and* the close in one. In the **`Self-finalize: no` toggle-off path** the coding session **already deployed at build-end** (the ship — code's own authority — Session Skill § The dispatch↔code loop) and reported `State: implemented-deployed` **before** this close was triggered, so this step is normally a **no-op** — the work is already live; the close just ties out the record. Same for a solo session that shipped separately. Either way, this step **deploys only if there is undeployed work** (the no-op guard below detects it from the git scan), then the atomic close (Step 12a) is the terminal action.

It runs after the history line is composed (8), the session-file body is written (9), and the worklog is composed (10) — but **before the atomic close (Step 12a), deliberately.** The version bump + push + reinstall land while the session is still active; then Step 12a performs the record close (status flips + `[DONE]` + history + worklog + `_active` removal) as the true terminal write, so `_active` is cleared only once the deploy has fully completed.

**For story / cab / personal / general: skip this step entirely.** Those types push during `commit` and have no version/reinstall concept — Step 11 is skipped and their finish ends at the atomic close (Step 12a) + the ✅ cue.

**No-op guard (now doubles as the already-shipped guard):** if the Step 2 git scan found nothing to ship — a clean tree AND no unpushed local commits — the work is already live (the happy-path ship handled it) or there was nothing to deploy. Report `Already shipped — nothing to deploy; close complete.` and skip to the close's final cue. Do not bump or push.

Otherwise (there is undeployed work — the solo ship+close case), present the deploy as a visually distinct step, followed by the Step 12a atomic close (which clears `_active`) and then the Step 12b/12c return block and ✅ close cue:

```
────────────────────────────────────────────────
DEPLOY  (bump → commit → push → reinstall → live)
────────────────────────────────────────────────
```

**Deploy discipline for storage-format bumps (acp-ajudd#110).** A storage-format MAJOR bump (a change to the on-disk session/inbox/history file layout — e.g. #102's per-item inbox) migrates the shared data instantly, but every *other* open terminal (planning / dispatch / capture) keeps running the prior plugin code against the new data until it is manually restarted — a migrated-data / old-code split observed live on #102's deploy. The clean way to avoid it: **before running this deploy, close the other role terminals for this slug; deploy; then reopen them.** Do the structural change in one pass rather than leaving other terminals to straggle across the boundary. The 11e notice below is the backstop for when a terminal is missed anyway — it is not a substitute for this discipline.

**11a. Derive the target plugin(s) from changed paths** — not from the session name. Using the Step 2 git scan (uncommitted changes + unpushed local commits), map each changed file under the marketplace root to its top-level plugin directory (e.g. `session/commands/finish.md` → `session`). Collect the distinct set. A deploy may span multiple plugins; each affected plugin gets its own bump.

**11b. Version bump — prompted, never silent.** For each affected plugin, read the current version from `<plugin>/.claude-plugin/plugin.json` and suggest a level + next version (one bump per plugin per feature):
- **PATCH** — bug fixes only
- **MINOR** — new command / feature / meaningful behavior addition
- **MAJOR** — redesign or breaking change

Show and wait (this is the one real decision in the deploy):
```
Deploy bump:
  session   v1.53.0 → v1.54.0   (MINOR — solo ship+close; deploy runs here as no prior ship)
go / <plugin> <level> / cancel
```
Apply the confirmed version to each affected `plugin.json`. On **cancel**, stop — nothing is committed, pushed, or reinstalled (the session is already closed; the deploy can be re-run later by re-opening).

**Storage-format flag (acp-ajudd#110) — only when the confirmed level is MAJOR.** Ask one follow-up: `Storage-format change — does this bump alter the on-disk session/inbox/history file layout (not just command behavior)? (yes/no, default no)`. A `yes` sets a flag carried into 11e (the one-time restart notice); a `no` (or any non-MAJOR bump) skips it silently — this is the only place the flag is asked, and it costs nothing on the read hot path.

**11c. Commit + push to master.** Stage the plugin changes (edited files + bumped `plugin.json`), draft a commit message summarizing the shipped work in the repo's style (`git log --oneline -5`), commit, and **push to master**. Any unpushed local commits made via `session:commit` during the session ride along in the push. End the commit message with the Co-Authored-By trailer per the repo convention (see CLAUDE.md). Direct pushes to `master` on this repo are authorized — no PR.

**11d. Reinstall — make it live, with the Windows fallback.** For each deployed plugin:
```bash
claude plugin update <plugin>@ajudd-claude-plugins
```
**Verify it took** — `claude plugin update` / marketplace update can fail silently on Windows. If the installed version does not match the new `plugin.json` version, fall back to the manual sequence:
```bash
cd ~/.claude/plugins/marketplaces/ajudd-claude-plugins && git pull
claude plugin uninstall <plugin>
claude plugin install <plugin>@ajudd-claude-plugins
```
A Claude Code restart may be required to load the new version — note this if so.

**11e. Record + report.** Append the deploy commit to the session file's `Commits:` field (one-line append — SHA + subject; the file was written in Step 9). Then print the deploy result (Step 12's return/close cue follows it):
```
Deployed: session v1.53.0 → v1.54.0 — pushed to master, reinstalled (live)
```

**Coordinated-restart notice (acp-ajudd#110) — only if 11b's storage-format flag was set `yes`.** Print immediately after the deploy line, one time:
```
⚠ Storage-format change — restart all other open terminals (planning / dispatch / capture) for this slug now; they are still running the prior on-disk format until restarted.
```

### 12. The Atomic Close, Return Handoff & Close Cue (acp-ajudd#94/#103)

**12a. Run the atomic close — the single terminal record-write (acp-ajudd#103).** Everything the close must persist — the frontmatter/body/`_index` status flips, the `[DONE]` archive stamp, the `_history.md` append, the worklog append, and the `_active` removal — is performed by ONE call to `finish-close.py`, or nothing is. It is the mechanical counterpart to `inbox-id.py` / `session-list.py` / `session-archive.py`; it exists because "all-or-nothing" cannot be enforced by prose — three sessions in a row still needed a manual dispatch tie-out (#85/#96/#95). Having composed the free text in Steps 8 / 9 / 10 (and written the session-file body in Step 9), call it now:

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/<pluginMarketplaceName>/session}"
PYBIN=python3; command -v python3 >/dev/null 2>&1 || PYBIN=python
"$PYBIN" "$ROOT/scripts/finish-close.py" \
  --session-root "<session_root>" --slug "<slug>" --name "<name>" \
  --type "<type>" --date "<YYYY-MM-DD>" --handle "<handle>" \
  --item-id "<id-or-empty>" --title "<title-or-empty>" << 'JSON'
{"history_line": "<the Step 8 line>", "worklog_entry": "<the Step 10 block, internal newlines escaped as \n>", "done_note": "<the Step 9 note, e.g. shipped v1.82.0 via session <name>>"}
JSON
```

- `history_line` / `worklog_entry` / `done_note` are the content composed in Steps 8 / 10 / 9. `worklog_entry` is a JSON string value, so its internal newlines must be escaped as `\n`.
- `--item-id` is the picked-up item's `<id>` (from the session file's `## Picked up from inbox` provenance); leave it **empty** for a bare `code <name>` session — the `[DONE]` stamp is then skipped. `--title` is the story/cab Jira summary; empty for plugin/personal preserves the existing `_index` title.
- The script is **idempotent**: if a prior partial run wrote some surfaces, re-running converges without duplicating. On **malformed JSON or any hard precondition failure it writes nothing and exits non-zero** (fail-closed) — fix and re-run; do **NOT** fall back to hand-editing the surfaces (piecemeal hand-writes are exactly the drift #103 removes).
- **The close self-verifies before it exits 0 (acp-ajudd#107 FIX 0).** After writing, the script re-reads every surface and confirms the expected end state (status flips, `_index` row, `_active` gone, history + worklog lines, and the `[DONE]` stamp in the target id's archive block). If any surface fails the read-back it exits **non-zero with a precise "surface X not confirmed" message** — so a partial can no longer masquerade as success. On that failure, **re-run** (idempotent); the reworded free text of a re-run still dedups (stable-key), and the payload is UTF-8-safe regardless of the Git-Bash locale.
- Relay the script's summary lines (they name each surface it wrote, plus any soft anomaly such as a missing `[CONSUMED]` line). **If the script prints a `! RECONCILED` line** (acp-ajudd#115 — the item was still live because the mandatory pickup was skipped), relay it prominently: it signals the `/session:start code #X` consume did not run and the close had to consume the item itself. For repo sessions, recompute the approved-hash (Step 9) now — after this call, so it covers the status-flipped file.

**GATE — nothing below prints until `finish-close.py` exits 0 (acp-ajudd#103).** The safe-to-close cue and any return block are gated on the script's success: a session must not be able to signal "done" (the ✅ cue, the deactivation) unless the record close actually ran. If the script exits non-zero, **STOP** — report the error, do **not** emit the ✅ cue, do **not** treat the session as finished. It is still open until the close succeeds.

**12b. Return handoff.** What this step emits depends on the `Self-finalize` mode and WHO fed the session; orchestration is detected, not declared (Session Skill § The three roles, Pillar 4) — read the `## Picked up from inbox` provenance for the `<from-role>` and the pickup work order's `Self-finalize` field. Escape-hatch stop-reasons (`blocked-question` / `found-issue` / `requirements-change`) are emitted mid-build via `/session:handoff` — **never here** (a stop is not a finish).

- **Orchestrated, default (`Self-finalize: yes`) — the coding session self-finalized AND notifies dispatch, one-way (acp-ajudd#109/#118).** The session self-validated and ran this close **itself** — there was no ship-report to confirm back, and this is **not** a round-trip: emit a **fire-and-forget** `coding ──▶ dispatch` return block with **`State: finished`** as terminal output (command-invoked via `/session:handoff`, two-ended title per acp-ajudd#69), then go straight to the ✅ / 🏆 close cue below — do **not** wait for a reply. The note is the *trigger* that tells dispatch to check this entry and pull the next; dispatch still confirms the `[DONE]` stamp (and, if relevant, the tree) before doing so — validate-don't-rubber-stamp (Session Skill § The dispatch↔code loop). This restores the coding→dispatch signal that #109's silence over-removed: #84's "happy path, no report" rule governs the **dispatch→planning** edge only — the coding→dispatch edge is different and stays legal (#74).
- **Orchestrated, `Self-finalize: no` — return the finished confirmation (acp-ajudd#100, scoped by #109).** This close ran because an `Action: finish` note (or the human on `safe-to-close`) triggered it after the build-end `implemented-deployed` ship report. Emit a `coding ──▶ dispatch` return block with **`State: finished`** — the finish-confirmation that closes the #98 wait-for-finish gate — command-invoked via `/session:handoff`, two-ended title per acp-ajudd#69. (Edge case: if this finish is itself acting as ship+close for a `Self-finalize: no` session that never separately shipped, the `finished` block still stands as the single return.)
- **Solo, planning-fed — a `planning ──▶ coding` handoff fed this session, dispatch bypassed (acp-ajudd#75).** The session self-finalizes on its own authority (solo default). Because a human planner is waiting, emit a **courtesy** `coding ──▶ planning` return block (`State: finished`) — a solo report explicitly outside the strict hub, not a `coding ──▶ dispatch` relay (Session Skill § The dispatch↔code loop, solo carve-out). Bypass cost: no independent validator ran — safe only for the doc-only, crisp-Done-when work such a direct handoff is meant for.
- **Solo, truly unpaired — no handoff note ever received.** No return block. Just the ✅ / 🏆 close cue.

**12c. End with the ✅ close cue — the last thing on screen (acp-ajudd#103/#109).** Only after `finish-close.py` exited 0 (Step 12a gate), print exactly one bold courier line from the fixed vocabulary (Session Skill § Cross-Session Paste Handoff → The courier line — UTF-8 chat markdown, not hook stdout, so the cp1252 ASCII rule does not apply):
```
**✅ <ids> — validated & closed. Safe to close this terminal.**
```
This is the `✅` **close** cue. In the **default self-finalize path**, a **truly-solo** session has it as the *single* terminal cue (no earlier `📤` ship cue fired); a **dispatch-fed** session prints it as the *second* of two cues — the fire-and-forget `finished` block's `▶ paste to dispatch` line comes first (acp-ajudd#118), this `✅` line last. In the `Self-finalize: no` path it is distinct from the `📤` **ship** cue printed earlier at build-end and from dispatch's `safe-to-close` signal. It fires only now, after the atomic close ran (Claude can't restart itself; the cue hands the terminal back to the human to close). When a return block is also emitted (`Self-finalize: no`, planning-fed solo, or the dispatch-fed default's fire-and-forget `finished` note), print it above the ✅ close cue.

For **personal** (also an inbox zone, can be orchestrated) the same applies without a version deploy. **story / cab / general are never dispatch-orchestrated** (Jira flow / no dispatch layer) — they get the standard close and no return block; their finish ends at the atomic close (Step 12a) + the ✅ cue.

### 13. Deactivation — folded into the atomic close (acp-ajudd#103)

**`_active` removal is no longer a separate step** — it is one of the surfaces the Step 12a atomic close (`finish-close.py`) removes, so deactivation happens as part of the single all-or-nothing write, gated by the same success check. Deploy (Step 11) still runs before Step 12a, so the version bump and any plugin-file edits during the deploy are still authorized by an active coding session; `_active` is cleared only once, by the close script, as the terminal write.

No manual `rm` is needed. If you ever need to verify (or a legacy path skipped the script), a bare `_active` removal is always safe — it is local and edits no plugin files:

```bash
rm -f ~/.claude/memory/sessions/<slug>/_active
```
On PowerShell: `Remove-Item -ErrorAction SilentlyContinue ~/.claude/memory/sessions/<slug>/_active`

Deactivation is silent — it produces no user-facing output. The last thing on screen is therefore the **Step 12c `✅` close cue** (`✅ <ids> — validated & closed. Safe to close this terminal.`) — printed after any return block this close emitted: planning-fed solo → a courtesy `coding ──▶ planning` block; **orchestrated default (dispatch-fed) → a fire-and-forget `coding ──▶ dispatch` `finished` block (acp-ajudd#118)**; `Self-finalize: no` → the finish-confirmation block. Only a **truly-solo** close (no handoff ever received) emits no return block, so the ✅ close cue stands alone as the final line.
