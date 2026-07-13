# HALT — standing down dispatched work mid-flight (acp-ajudd#67)

The clean mid-flight stand-down of dispatched work: `Action: HALT` out / `State: HALTED` back. Loaded on demand (the SKILL keeps a one-line pointer at § HALT).

The dispatch↔code loop assumes work runs to completion (or bounces back on the escape hatch). **HALT is the other exit: dispatched work is stopped cleanly before it finishes**, because a prerequisite turns out to be missing, the ground shifted, or the work was scoped against a model that has since changed. This is not a failure state and not the escape hatch (question / unclear / disagreement / found-problem — those expect an *answer* and a resume); HALT means *stop, don't resume this run.* The vocabulary was improvised during the acp-ajudd#60 detour (dispatched before its prerequisite #62 had shipped, then stood down); acp-ajudd#67 makes it real.

**Two words, added to the handoff field set (§ Cross-Session Paste Handoff):**
- **`Action: HALT`** — the outbound stand-down. Dispatch (or planning, via dispatch) tells a running coding session to stop the dispatched work.
- **`State: HALTED`** — the return leg. The coding session confirms it stopped, and in what state it left things.

**Clean mid-flight stop procedure (what HALT actually does):**
1. **No publish.** Nothing outward-facing goes out — no Confluence publish, no Teams send, no PR opened. Whatever the work would have shipped stays unshipped.
2. **No commit / no deploy.** Do **not** run the `/session:finish` deploy (no version bump, no push, no reinstall) and do **not** land a commit for the halted work. A plugin only deploys when work is *done* (§ Development Lifecycle) — halted work is not done.
3. **Preserve the draft / WIP.** Keep the in-progress work where it is — the coding session file, any scratch draft, uncommitted edits. Nothing is thrown away; a HALT is recoverable. Record in the session file what was reached and *why* it halted.
4. **Return a `State: HALTED` handoff block** to the origin role naming the reason and the preserved WIP location, so dispatch/planning knows the run stopped and what survived.

**Halted work re-enters as a NEW entry citing the halted one — distinct from consumed = frozen (acp-ajudd#59).** These two look similar (both leave an entry that is "not to be reopened") but are different states with different resume patterns:
- **Consumed = frozen** (§ State-Exclusivity, acp-ajudd#59): a `work` entry that was *converted* into a coding session and completed. It is frozen because it is **done** — a change becomes a new entry only because implementation moved past it.
- **Halted**: work that was stood down *before* completion. If it was already consumed into a coding session when halted, that session's entry is archived-as-consumed like any other (the ID is retired — reopening the number would be a live+consumed exclusivity violation, acp-ajudd#13). So the work does **not** resume by reopening the halted entry — it **re-enters as a NEW `work` entry that cites the halted one** ("supersedes / re-run of `<id>`, halted because …"). This is exactly what **acp-ajudd#65 did for the paused acp-ajudd#60**: #65 is a fresh entry, new ID, that names #60 as the halted original it re-runs cleanly now that the prerequisite has landed. `refine` authors the re-entry (dispatch is read-only and routes the work-authoring to `refine`). **The pattern in one line: halted work resumes by citation, never by reopening.**
