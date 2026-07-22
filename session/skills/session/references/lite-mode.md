# Lite Coding (acp-ajudd#154/#143)

A **toggleable, explicit choice** at pickup time: build the picked-up work with the full
session-file lifecycle (**session**, the existing default and behavior), or without ever
writing a session `.md` file (**lite**) — using the work's own native record (an inbox
`work` entry for plugin/personal; the Jira story/CAB issue for work repos) as the only
place state lives.

**Naming note.** Earlier drafts called this "sessionless." Renamed to **lite** because
"sessionless" already names something else in this plugin's own glossary — the
**planning** stance (refine/dispatch/capture never had a file, ever). Reusing the word
for "still coding, just skipping the file" recreated exactly the kind of ambiguity the
terminology glossary exists to prevent. **Lite** is unambiguous: it's still a coding
pickup, just a lighter-weight one. Matches the original inbox item's own working title
("Formal 'lite' coding path," #143).

**All zones: plugin, personal, story, CAB.** General has no session file *or* record
either way, so this doesn't apply to it.

## Why this exists

Session files (and, for story/CAB, the Teams-chat/epic-link/CAB-relationship extras
layered on top) are real, useful ceremony for continuity. But that ceremony has a cost,
and not every picked-up item needs it — a quick, one-sitting fix doesn't benefit from a
resume aid it will never be resumed *from*, and a CAB's "session" is mostly link-gathering
(decisions, fixes, or actual coding on a CAB itself are rare). `code`-ing work today
always pays the full cost regardless of size. Lite lets the size of the work decide.

## The choice — asked once, at pickup, same wording in every zone

**Plugin / personal** — when graduating a `work` entry via `code <n>` / `code <id>`
(`start-impl.md` § Work Pickup), **before** deriving a feature name:

**Story** — at `code <KEY>` new kickoff (`start-impl.md` § Story — new kickoff), **before**
the Jira transition + branch creation:

**CAB** — at `cab <KEYS>` / `code cab <KEYS>` new kickoff (`start-classic.md`'s Work
project type-specific inputs), **before** routing to `/release:create-cab`:

All three ask the same shape of question (plain text, not a picker — same rule as every
other prompt in this flow):

```
Session file or lite for this work?

  session (default) — full session file: Open items / Next steps as a resume
    aid across sittings, a Teams chat link, commit/checkpoint/finish tracking.
    Costs a little overhead to maintain as you build.
  lite — no session file. <record> is the only record; updates get appended
    to it as notes. Less overhead, but if you hand this off or come back much
    later, you're working from just that note — none of the session extras
    (chat link, resume fields, connections) exist.

Reply with an override, or "go" to accept session (default).
```

Where `<record>` is:
- plugin/personal → "the inbox item"
- story → "the Jira story (via comments)"
- CAB → "the CAB Jira issue (via comments)"

**Discoverable, and skippable via a trailing `lite` token.** The quick-start panel
(`start-panel.py`) advertises this directly on the `code`/`cab` lines (`code <n|KEY>
[lite]`, `cab <KEYS> [lite]`) plus a one-line hint with a worked example — the point
isn't a hidden feature you have to already know about. And you don't have to wait for
the interactive prompt: append `lite` to the command itself — `/session:start BPT2-6532
lite`, `code BPT2-6532 lite`, `cab BPT2-6532 BPT2-6540 lite` — and the question is
pre-answered, never asked. This works from the bare `/session:start <target> lite`
fast-path (`start.md` Step 0) or from typing `code <target> lite` / `cab <keys> lite` at
the routing-block reply (`start-classic.md`) — both set the same `lite_requested` flag
that `start-impl.md`'s three prompt sites check before asking. Skipping the prompt still
announces the choice with one line (never silent) — it just doesn't stop and wait for a
reply.

**Default stays session — this is a deliberate opt-*in* to less ceremony, never a
silent opt-out of it.** "go" (or any reply that doesn't say `lite`) takes the session
path exactly as documented today; nothing about the existing flow changes.

**What's required regardless of the choice (story/CAB).** The Jira transition to *In
Progress* and feature-branch creation are not session-*file* ceremony — they're needed
to do the work at all, session file or not. Asking the question doesn't defer or skip
them; it only decides whether the *extra* layer (Teams chat resolution, epic-memory-file
load/create, session state file) gets built on top. This is *why* the question is asked
up front rather than deferred to first-checkpoint: deferring would still require that
same kickoff work immediately, and would only add a "catch up the extras later, under
time pressure" cost with no corresponding savings.

**Toggle in both directions, at any point:**
- **Lite → session:** run the normal graduation on the still-live record — plugin/
  personal: Item Pickup graduation on the inbox item (never consumed, so this just folds
  it into a fresh session file); story/CAB: derive/confirm the session name (defaults to
  the key), resolve Teams chat, load epic memory, write the session file, seeding Open
  items from the accumulated Jira-comment trail. Nothing is lost — the comments already
  captured everything a lite record would have.
- **Session → lite:** delete the session file. Whatever state lived *only* in that file
  (Open items, Next steps, Teams chat link, commit history) is lost — an accepted,
  explicit-confirm risk, not a silent one: confirm once (`Delete <name>'s session file?
  State not captured elsewhere is lost. (yes / cancel)`) before removing it. The
  underlying work item / Jira issue, if not yet closed, stays exactly where it was.

## What lite skips

**Plugin / personal:** everything in `start-impl.md` Steps 6–8 that exists *because* a
session file exists — Establish Session Identity, Teams Chat Setup, Write Session State
(no `<name>.md`, no `_index.md` row). The fold-then-archive consume at Item Pickup step 5
is also skipped — the item is **not** archived at pickup; it stays live.

**Story:** Teams chat resolution/creation, the epic-memory-file check/create prompt
(`~/.claude/memory/epics/<key>.md`), and the session-file write + `_index.md` row. The
Epic Link itself still lives on the Jira issue regardless — only the local convenience
copy goes away.

**CAB:** the session-file write + `_index.md` row, and any session-level Teams chat
resolution. The CAB card itself (created via `/release:create-cab`) is unaffected — CAB
kickoff mechanics belong to the `release` plugin, not this one; lite only changes whether
`session` also keeps a parallel state file on top of it.

## What lite does instead

1. **Plugin / personal — status flip, in place.** Change the item's metadata line to
   `> [type: work · status: in-progress]` — a lifecycle stage reachable only via a lite
   pickup (a session-graduated pickup never lingers in the inbox, so this status never
   appears on a session-consumed item). `inbox-render.py` renders it distinctly: `· in-
   progress (lite)` in the pickup list, `— in progress (lite)` in the resume-inbox block
   (see `inbox-convention.md` § Lifecycle for how this sits alongside the existing
   per-session in-progress marker — same slot, different inbox kind).
2. **`_active` marker, every zone.** Write `~/.claude/memory/sessions/<slug>/_active` as
   `lite:<id>` — plugin/personal: the inbox item id (e.g. `lite:acp-ajudd#154`);
   story/CAB: the Jira key (e.g. `lite:BPT2-6429`, `lite:CAB-456` — the key IS the stable
   id, no separate mint needed) — instead of a session name. This is what lets `commit` /
   `checkpoint` / `finish` recognize "there is active work for this slug, but no session
   file" rather than reporting a bare no-session error — see § Command behavior below.
   `path-resolution.md` documents the two `_active` shapes.
3. **Updates land in the native record, not a session file.**
   - Plugin/personal: append progress notes directly to `_inbox/<id>.md` under a
     `### Progress log` section.
   - Story: post a Jira comment — same business-readable convention `/story:comment`
     already uses (status + milestone, no file paths/class names/token names).
   - CAB: post a Jira comment on the CAB issue — same convention `commit.md` already uses
     for CAB-type Jira comments today (posted to each story in `Related stories`; for
     lite, post to the CAB issue itself as the primary target, since the CAB record's
     whole job is pulling links together in one place — additionally to `Related
     stories` only if the change is story-specific, not CAB-wide).
4. **No injection scan / maturity guard re-run** beyond what pickup already did — those
   guards ran (or were explicitly overridden) at the original pickup moment; choosing
   lite doesn't change what was already folded into scope.

## Resuming lite work

**Plugin/personal already has a durable tell:** the inbox item itself carries `status:
in-progress` — visible in the pickup list regardless of which terminal or machine is
asking. `code <id>` on an item already at `status: in-progress` is a **resume**, not a
re-pickup: **do not** re-ask the session-vs-lite question (already decided), **do not**
re-run the injection scan or the fold — just re-affirm `_active` as `lite:<id>` (in case
a different/fresh terminal lost track of it) and continue from the item's existing
progress log as context.

**Story/CAB has no equivalent record-level marker** — Jira's own workflow status (e.g.
*In Progress*) isn't a lite-vs-session distinction, just a work-status one. So the resume
tell is `_active`, which is local-only by design (same as every other `_active` use in
this plugin — it is a per-user pointer, never synced across machines):

- **No session file exists, `_active` reads `lite:<KEY>`** (matching the target) → this
  is a **resume**: skip the Jira transition and branch creation (already done at the
  original pickup), skip the session-vs-lite question, and continue — post-comment
  updates as usual, same as any other lite checkpoint/commit.
- **No session file exists, `_active` does NOT match, and the Jira issue's status is
  already past its fresh-pickup state** (story: not *Gathering Requirements* / *Ready
  For Work*; CAB: not a fresh un-started card) → this is genuinely ambiguous — it could
  be lite work started from a different terminal/machine, or a story left *In Progress*
  with no local record at all. **Ask rather than silently re-kickoff** (re-transitioning
  or re-branching a story that's already underway would be actively wrong):
  ```
  <KEY> is already <status> with no local session file or record of lite
  pickup on this machine — resume as lite (no file, comments only), or start
  a session file to track it from here?
    resume-lite   ·   start-session   ·   not mine (leave it)
  ```
  - **resume-lite** → set `_active` to `lite:<KEY>`, skip re-transition/re-branch (verify
    the branch matches, offer to switch if not — same as a normal story resume), continue.
  - **start-session** → treat as a normal resume-into-session-file (derive a session
    around the existing in-progress story, same as picking up mid-flight work anyone
    else started).
  - **not mine** → stop; don't touch anything.
- **No session file exists, `_active` does NOT match, and the Jira issue is still in its
  fresh-pickup state** (story: *Gathering Requirements* / *Ready For Work*; CAB: not yet
  started) → this is a genuine **new kickoff** — ask the session-vs-lite question as
  documented above.

## Command behavior — commit / checkpoint / finish with no session file

Each of `commit.md` / `checkpoint.md` / `finish.md` resolves `_active` at Step 0. Today
that value is always a plain session name, and its *absence* is the "no session
established" stop. Lite adds a second shape to check for, in every zone:

- **`_active` is a plain name, `<session_root>/<name>.md` exists** → unchanged, run the
  command exactly as documented.
- **`_active` is absent** → unchanged, the existing clean stop (`No session established
  for <slug>. Run /session:start first.`).
- **`_active` is `lite:<id>`** → there IS active work, just no session file for it.
  **Prompt, don't silently pick a side:**
  ```
  No session file for the active work (<id>) — create a session file now,
  or just add a note to the source record?
    create — graduate now: derive a name, write the session file (folding in
      the accumulated notes/comments as history), then continue this
      command's steps against it.
    note — stay lite: do this command's real work (the git commit; the
      checkpoint capture; finish's version bump + push + reinstall, or for
      story/CAB the Jira-side close) but record the result on the native
      record instead of a session file.
  ```
  - **create** → plugin/personal: run Item Pickup's graduation (`start-impl.md` § Work
    Pickup, steps 2–5) on the still-live item. Story/CAB: derive/confirm a session name,
    resolve Teams chat, write the session file seeded from the Jira comment trail. Then
    continue the invoking command's own steps against the fresh session file normally.
  - **note** → the invoking command still does its *real* work (this never skips actual
    git operations or, for `finish`, the actual deploy/Jira-close — none of that is
    session-file-dependent); only the *recording* target changes:
    - **commit** → plugin/personal: append to the item's progress log instead of the
      `Commits:` field. Story/CAB: post the same 1-line Jira comment `commit.md` § 2a
      already drafts for story/cab types (that step already runs regardless of session
      choice — lite just means there's no session file's `Commits:` field to also update).
    - **checkpoint** → same substitution, into the item progress log / a Jira comment.
    - **finish** → see § Closing below.

## Closing lite work

**Only a real completion action may stamp completion** — unchanged from
`inbox-convention.md` § Disposition & completion (acp-ajudd#42): planning/refine never
completes, only a coding action that actually built the work does.

- **Plugin/personal:** the closing action appends a final entry to the item's progress
  log, then archives it using the existing convention exactly — append the item verbatim
  (with a `[DONE YYYY-MM-DD]` stamp immediately under its header) to `_inbox_archive.md`,
  then delete the live `_inbox/<id>.md` file. There is no separate `status: done` value —
  completion is the archive-with-`[DONE]` move itself, same as every other item's
  completion.
- **Story:** post a final Jira comment summarizing what shipped, then transition the
  story per its normal terminal-status flow (same Jira-side behavior `/story:finish`
  already does) — the only thing skipped is the session-file completion (no file to
  complete).
- **CAB:** post a final Jira comment on the CAB issue, note deploy status — same
  Jira-side behavior as a normal CAB close, minus the session-file completion.

In every zone, clear `~/.claude/memory/sessions/<slug>/_active` on close, same as a
normal session close does.

## Open follow-ups (not solved by this pass)

- Whether a lite item/story/CAB that's been idle a long time needs its own staleness
  surfacing (today's `⚠ stale (>14d)` marker is session-list-only, keyed off a session
  file's `updated` date — a lite record has no equivalent field yet).
