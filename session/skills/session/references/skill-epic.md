# Epic Context — Cross-Story Research

Read this when the active session has an `Epic` field and the task crosses story boundaries (architecture decisions, blockers, open questions, story map, or anything a sibling story may have already answered).

When the active session has an `Epic` field, the epic file (`~/.claude/memory/epics/<key>.md`) is the canonical source for anything that crosses story boundaries: architecture decisions, blockers, open questions, and the story map.

**Check the epic file first** before investigating code or asking Jira when the question is architectural — decisions are already recorded there and re-investigating wastes time.

**Sibling story lookup:** When researching something that a sibling story may have already answered (data formats, API contracts, cross-repo contracts, design decisions), check the sibling's session file:
1. Open the epic file — find the story in the Stories table
2. Derive the repo slug from the story key or the Scope field in the sibling's session file
3. Read `~/.claude/memory/sessions/<repo-slug>/<story-key>.md`

Example: working on BPT2-6382 (frontend) and need the wire format for `periodId` — check BPT2-6379's session file (`~/.claude/memory/sessions/virtual-office/BPT2-6379.md`) before digging through code or calling Jira.

**When to use sibling sessions proactively:**
- Any question about data shapes, API contracts, or field formats that another story's SPIKE or backend work would have answered
- Cross-repo coordination ("what's the other side expecting?")
- When a blocker or open question in the epic points to a sibling story as owner

**Explicit "look across the epic":** If the user says "check what other stories found" or "look across the epic for X", read *all* sibling session files listed in the epic's Stories table and surface their open items, next steps, and relevant notes.
