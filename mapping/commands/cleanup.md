---
allowed-tools: Read, Write
description: Review and remove phrases unused longer than your configured threshold
---

Remove stale command entries — ones you haven't triggered via natural language in a while.

Supports an `--auto` flag for unattended/scheduled runs (no prompts, silent removal).

## Steps

1. **Check for `--auto` flag** in args. If present, run in auto mode (see [Auto mode](#auto-mode) below) instead of the interactive flow.

2. **Read registry** — read `~/.claude/plugins/phrases.json`. If it doesn't exist or is empty, say: "Nothing to clean up." and stop.

3. **Get threshold** — read `_config.cleanup_threshold_days` (default: 14). Today's date is known from context.

4. **Find stale phrases** — for each command key (skip `_config`), scan each phrase object:
   - `last_used` older than threshold → stale
   - No `last_used` AND `added_date` older than threshold → stale (never fired, grace period expired)
   - No `last_used` AND `added_date` within threshold (or absent) → **skip** (newly added, grace period still active)

5. **If none stale** — say: "All phrases used within the last [threshold] days. Nothing to clean up." and stop.

6. **Display candidates** — group stale phrases by command:

```
Stale phrases (unused 14+ days):

  /release:deploy — Execute a production deployment
    - deploy to prod       ⚠ never used
    - run the deployment   ⚠ never used
    - execute the deploy   ⚠ never used
    - deploy it            ⚠ never used

  /comms:sweep — Clean the inbox
    - triage my email      ⚠ unused 18d
    - process my inbox     ⚠ never used

X phrases across Y commands. Review each command:
```

7. **Review loop** — for each command with stale phrases, show stale phrases and prompt:

```
/release:deploy — 4 stale phrases:
  - deploy to prod, run the deployment, execute the deploy, deploy it
Remove all / Keep all / Review one by one?
```

   - **Remove all** — delete all stale phrase objects for this command; if `phrases` array is now empty, remove the command key
   - **Keep all** — set `last_used` to today on all stale phrases (resets their clock)
   - **Review one by one** — prompt `Remove "[text]"? (yes/no)` for each stale phrase
   - **Skip remaining commands** — stop the loop, write what's been decided so far

8. **Write** the updated `~/.claude/plugins/phrases.json`

9. **Summary:**
```
Cleanup complete.
  Removed: X phrases across Y commands
  Kept:    Z phrases
  Run /mapping:list to see your updated registry.
```

## Auto mode

When called with `--auto` (e.g. from a scheduled agent):

1. Read registry and threshold (same as steps 2–4 above)
2. Silently remove all stale phrase objects — no prompts
3. Drop any command key whose `phrases` array is now empty
4. Write the updated file
5. Print a one-line summary: `Mapping cleanup: removed X stale phrases across Y commands.`

Auto mode never removes phrases still within their grace period (`added_date` within threshold).

## Notes

- Shipped defaults (`mapping/.claude-plugin/phrases.json`) are never touched — only user phrases
- Keeping an entry resets its clock — it won't appear again until another threshold period passes
- To change your threshold: add or edit `_config` in `~/.claude/plugins/phrases.json`:
  ```json
  { "_config": { "cleanup_threshold_days": 30 } }
  ```
