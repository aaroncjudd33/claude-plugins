# Inbox — ajudd-claude-plugins

---

## Post-Deploy Validation Checklist — Triggered by release:deploy
_Added 2026-04-23_

### What
Add a structured post-deployment validation step to the story/release workflow. When `release:deploy` finishes a successful GitHub Actions run, it automatically reads the post-deploy checklist for each linked story and walks through them inline — no separate command needed.

### Why
After a CAB deploys, stories get closed out informally. There's no structured "you must verify X in prod before marking this done" gate. Validation steps get forgotten under pressure.

Real example that prompted this: GLB Lookback Import inactivity alarms fire every 2 hours. A fix is pending CAB deployment. After deploy, someone needs to watch for 2+ hours to confirm the alarms stop — but there's no place to capture that requirement tied to the story.

### Design decisions
- **No new slash commands.** `release:deploy` owns the full lifecycle: merge → workflow runs → succeed → validate → close stories.
- **Data lives in story memory files.** Add a `postDeployChecks` markdown checklist field to each story's session file (e.g. `~/.claude/memory/sessions/<slug>/BPT2-XXXX.md`). Lightweight, readable, no new infrastructure.
- **Async/time-boxed checks handled gracefully.** If a check requires waiting (e.g. "monitor alarms for 2 hours"), the skill notes it as a timed reminder rather than blocking the session — user is told to come back and verify before closing.
- **Auto-close when all checks pass.** If all checklist items are confirmed, `release:deploy` transitions the linked stories to Done/Released automatically.
- **Stories with no checklist** close normally — no friction added to the happy path.

### Plugin work needed

1. **Story memory file format** — document the `postDeployChecks` convention (a `## Post-Deploy Checks` section with `- [ ]` items). Update the `story:create` skill to prompt for these when creating a story if the context suggests deployment validation steps.

2. **`release:deploy` skill update** — after workflow succeeds:
   - Read the CAB card to find linked story keys
   - For each story, check `~/.claude/memory/sessions/<slug>/<story-key>.md` for a `## Post-Deploy Checks` section
   - If checks exist, surface them one by one; user confirms/fails each
   - Timed checks: print the check with a note ("requires X hours — come back to verify") and leave story in Ready For Test
   - If all synchronous checks pass → transition story to Done/Released

3. **`story:update` (optional enhancement)** — when transitioning a story to Done manually, check for unchecked post-deploy items and warn before allowing the transition.

### Acceptance criteria
- [ ] Can add `## Post-Deploy Checks` to a story memory file during or after story creation
- [ ] `release:deploy` reads linked stories' checks after a successful workflow run
- [ ] Synchronous checks are walked through inline with y/n confirmation
- [ ] Timed/async checks are noted and story is left open with a reminder
- [ ] Stories with no checks close normally — no change to current behavior
- [ ] BPT2-6333 (GLB alarm fix) validated as the first real-world use of this flow
