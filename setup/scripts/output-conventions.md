<!-- begin acp-output-conventions (managed by /setup:onboarding and /setup:update - do not edit between markers) -->
## Claude Output Conventions

Format signals type: a `✓` prefix marks informational / done / skippable content (internal
reasoning, routine confirmations); standard working content carries no marker, read in
order; `⚠ read before proceeding:` marks a hard gate — a caveat, a blocked state, or a
decision only you can make — bolded, surfaced first when it's the point of the reply,
never skipped. Paste-ready artifacts (handoff blocks, commands, commit text) stay in
fenced code blocks.

Every non-trivial reply ends with one verdict line — safe-to-proceed / safe-to-close /
next-action / blocked — so it survives a reply that scrolled out of view. Mirror it at
the top too if useful; the bottom line is required.

No all-caps — not in labels, not in content. Use bold text or a leading symbol for
emphasis instead.

### Response verbosity — the 0-5 dial

How much to write, on a dial that can change any time. Say "v3", "verbosity 4", or
"level 1" in any session to set it for that session; the default below applies until
then.

Two things are constant at every level — the format-signals-type rule above, and never
duplicating what was just pasted or what a file already says (only the delta: verdict +
action).

The dial governs proactive output only — never answers to direct questions. When a
question is asked directly, answer in full regardless of level; asking is the bypass. A
follow-up on the same topic goes deeper still, uncapped. The dial only scales what gets
volunteered — status, confirmations, recaps, reasoning nobody asked for.

- v0 — results only. Bare outcome, one line. No context, no reasoning, no "what I did."
- v1 — result + essential flag. Outcome plus at most one short line if something must be
  flagged (a caveat, the next step). ~1-3 lines.
- v2 — brief. The answer/action + the core "why" in a sentence or two. No tables, no
  multi-section layouts, no standing recaps. Reads like a short chat reply.
- v3 — brief + reasoning. Tradeoffs / the "why" on non-trivial calls; light structure
  okay (short lists, a small table).
- v4 — thorough. Full reasoning, options weighed, what changed and why, cross-refs,
  tables.
- v5 — everything. Exhaustive: step-by-step, all reasoning, all state, recaps,
  alternatives.

Default: __VERBOSITY_DEFAULT__
<!-- end acp-output-conventions -->
