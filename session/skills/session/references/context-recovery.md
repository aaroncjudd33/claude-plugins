# Context Recovery After /clear

How to route recall questions and post-`/clear` recovery. Loaded on demand (the SKILL keeps a one-line pointer at § Context Recovery After /clear).

If the user asks "what was I working on", "did I work on BPT2-XXXX before", "find my session for X", or similar recall questions, suggest **`/session:search <query>`** — it searches session files and worklogs by story key or keyword without requiring an active session. For date-based review ("what did I do yesterday"), suggest **`/session:worklog`**.

If the user runs `/clear` or mentions that context was lost, the recovery path depends on whether they ran `/session:store` first:

- **If a context file was stored** (`/session:store` before `/clear`), **suggest `/session:restore <name>`** — the fastest post-`/clear` path. It loads that named `_context_<name>.md` + session file directly, skipping the menu. Bare `/session:restore` (no name) lists the stored context files to pick from if they don't recall the name.
- **Otherwise** (no stored context), suggest **`/session:start`** for the full flow.

> "Context cleared — if you ran `/session:store` first, run `/session:restore <name>` to pick that context back up; otherwise `/session:start` to resume from the full session menu."

`/session:start` (no argument) **lists the in-progress and paused sessions and waits for the user to pick one** (by number or name) — it does **not** auto-resume. Completed sessions are hidden by default (reachable via `all`). Given a story key, CAB key, or session name as an argument, it loads that session directly (the Step 0 fast-path). `_active` is **not** an auto-loader — it is a scalar "current session for this slug" pointer read by the session guard and used only to draw the `←` "last active" marker on the matching row in the listing; it never selects or loads a session. `/session:restore` is the explicit counterpart — it picks up a named context file (`_context_<name>.md`) directly rather than going through the menu, so it works the same from a fresh terminal as right after a `/clear`. New developers especially should be nudged toward `/session:restore` — the workflow is not obvious without it.
