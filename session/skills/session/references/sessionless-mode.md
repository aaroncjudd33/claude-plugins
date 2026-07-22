# Sessionless Coding (acp-ajudd#154/#143)

A **toggleable, explicit choice** at pickup time: build the picked-up work with the full
session-file lifecycle (**session**, the existing default and behavior), or without ever
writing a session `.md` file (**sessionless**) — using the work's own native record (an
inbox `work` entry for plugin/personal; a Jira story for work repos) as the only place
state lives.

**v1 scope: plugin / personal zones only.** Story/cab kickoff already bundles Jira
transition + branch creation + CAB/Teams wiring into `code`, so extending the explicit
choice there is a larger surface than this pass covers — revisit once the pattern is
proven here. General has no session file *or* record either way, so this doesn't apply
to it.

## Why this exists

Session files are real, useful ceremony for continuity — Open items / Next steps as a
resume aid, a Teams chat link, a written record for teammates and the worklog. But that
ceremony has a cost, and not every picked-up item needs it: a quick, one-sitting fix
doesn't benefit from a resume aid it will never be resumed *from*. `code`-ing a `work`
entry today always pays that cost. Sessionless lets the size of the work decide.

## The choice — asked once, at pickup

When graduating a `work` entry via `code <n>` / `code <id>` (`start-impl.md` § Work
Pickup), **before** deriving a feature name, ask (plain text, not a picker — same rule as
every other prompt in this flow):

```
Session file or sessionless for this work?

  session (default) — full session file: Open items / Next steps as a resume
    aid across sittings, a Teams chat link, commit/checkpoint/finish tracking.
    Costs a little overhead to maintain as you build.
  sessionless — no session file. The inbox item is the only record; updates
    get appended to it as notes. Less overhead, but if you hand this off or
    come back much later, you're working from just the item note — none of
    the session extras (chat link, resume fields, connections) exist.

Reply with an override, or "go" to accept session (default).
```

**Default stays session — this is a deliberate opt-*in* to less ceremony, never a
silent opt-out of it.** "go" (or any reply that doesn't say `sessionless`) takes the
session path exactly as documented today; nothing about the existing flow changes.

**Toggle in both directions, at any point:**
- **Sessionless → session:** run the normal Item Pickup graduation on the still-live
  item (it was never consumed) — derives a name, folds the item, writes the session
  file. The item's accumulated progress-log notes fold in as the session's provenance
  block, same as any other pickup.
- **Session → sessionless:** delete the session file. Whatever state lived *only* in
  that file (Open items, Next steps, Teams chat link, commit history) is lost — this is
  an accepted, explicit-confirm risk, not a silent one: confirm once (`Delete <name>'s
  session file? State not captured elsewhere is lost. (yes / cancel)`) before removing
  it. The underlying work item, if not yet archived, stays exactly where it was.

## What sessionless skips

Everything in `start-impl.md` Steps 6–8 that exists *because* a session file exists:
**Establish Session Identity**, **Teams Chat Setup**, **Write Session State** (no
`<name>.md`, no `_index.md` row). The **fold-then-archive** consume at Item Pickup step 5
is also skipped — the item is **not** archived at pickup; it stays live.

## What sessionless does instead

1. **Status flip, in place.** Change the item's metadata line to
   `> [type: work · status: in-progress]` — a new lifecycle stage, reachable only via a
   sessionless pickup (a session-graduated pickup never lingers in the inbox at all, so
   this status never appears on a session-consumed item). `inbox-render.py` renders it
   distinctly: `· in-progress (sessionless)` in the pickup list, `— in progress
   (sessionless)` in the resume-inbox block (see `inbox-convention.md` § Lifecycle for
   how this sits alongside the existing per-session in-progress marker — same slot,
   different inbox kind).
2. **`_active` marker.** Write `~/.claude/memory/sessions/<slug>/_active` as
   `sessionless:<id>` (e.g. `sessionless:acp-ajudd#154`) instead of a session name. This
   is what lets `commit` / `checkpoint` / `finish` recognize "there is active work for
   this slug, but no session file" rather than reporting a bare no-session error — see
   § Command behavior below. `path-resolution.md` documents the two `_active` shapes.
3. **Updates land in the item, not a session file.** As work happens, append progress
   notes directly to `_inbox/<id>.md` under a `### Progress log` section — what changed,
   decisions made, open questions — exactly the content that would otherwise go into a
   session's Open items / Next steps.
4. **No injection scan / maturity guard re-run** beyond what Item Pickup already does —
   those guards ran (or were explicitly overridden) at the original pickup moment; going
   sessionless doesn't change what was already folded into scope.

## Command behavior — commit / checkpoint / finish with no session file

Each of `commit.md` / `checkpoint.md` / `finish.md` resolves `_active` at Step 0. Today
that value is always a plain session name, and its *absence* is the "no session
established" stop. Sessionless adds a second shape to check for:

- **`_active` is a plain name, `<session_root>/<name>.md` exists** → unchanged, run the
  command exactly as documented.
- **`_active` is absent** → unchanged, the existing clean stop (`No session established
  for <slug>. Run /session:start first.`).
- **`_active` is `sessionless:<id>`** → there IS active work, just no session file for
  it. **Prompt, don't silently pick a side** (Aaron's explicit call — this is a decision
  the user makes at the point of use, not something the command infers):
  ```
  No session file for the active work (<id>) — create a session file now,
  or just add a note to the source item?
    create — graduate now (same as `code <id>`): derive a name, fold, write
      the session file, then continue this command's steps against it.
    note — stay sessionless: do this command's real work (the git commit;
      the checkpoint capture; finish's version bump + push + reinstall) but
      write the resulting summary into the item note instead of a session
      file.
  ```
  - **create** → run Item Pickup's graduation (`start-impl.md` § Work Pickup, steps
    2–5) on the still-live item, write `_active` as the new session name, then continue
    the invoking command's own steps against the fresh session file exactly as normal.
  - **note** → the invoking command still does its *real* work (this never skips actual
    git operations or, for `finish`, the actual deploy — those aren't session-file
    dependent in the first place); only the *recording* target changes from a session
    `.md` to the item note. See each command's own Step 0 addendum for the specific
    substitution (commit's `Commits:` field → an item progress-log line; checkpoint's
    state capture → the same; finish's session-completion write → a `[DONE]` stamp +
    archive on the item itself, per § Closing below).

## Closing sessionless work

**Only a real completion action may stamp `[DONE]`** — this is unchanged from
`inbox-convention.md` § Disposition & completion (acp-ajudd#42): planning/refine never
completes, only a coding action that actually built the work does. For sessionless work
that never graduates to a session, the completing action is a `finish`-equivalent that
chooses **note** at the prompt above: it appends the closing summary as a final entry in
the item's progress log, then archives it using the existing convention exactly — append
the item verbatim (with a `[DONE YYYY-MM-DD]` stamp immediately under its header) to
`_inbox_archive.md`, then delete the live `_inbox/<id>.md` file. There is no separate
`status: done` value — completion is the archive-with-`[DONE]` move itself, same as
every other item's completion. Sessionless just means no session file was ever the
intermediate.

## Open follow-ups (not solved by this pass)

- Story/cab extension of the same explicit choice — deferred per v1 scope above.
- Whether a sessionless item that's been idle a long time needs its own staleness
  surfacing (today's `⚠ stale (>14d)` marker is session-list-only, keyed off a session
  file's `updated` date — a sessionless item has no equivalent field yet).
