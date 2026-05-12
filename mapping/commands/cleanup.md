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

4. **Find stale entries** — for each command key (skip `_config`):
   - Entry has `last_used` older than threshold → stale
   - Entry has no `last_used` AND `added_date` is older than threshold → stale (never fired, grace period expired)
   - Entry has no `last_used` AND `added_date` is within threshold (or absent) → **skip** (newly added, still in grace period)

4. **If none stale** — say: "All entries used within the last [threshold] days. Nothing to clean up." and stop.

5. **Display candidates** — list each stale entry with phrase count and last-used status:

```
Stale entries (unused 14+ days):

  /release:deploy — Execute a production deployment  ⚠ never used  (5 phrases)
  /comms:sweep — Clean the inbox  ⚠ unused 18d  (4 phrases)
  /links:open — Open a named link  ⚠ never used  (4 phrases)
  ...

X entries total. Review each one:
```

6. **Review loop** — for each stale entry, prompt:

```
/release:deploy (never used)
  - deploy to prod
  - run the deployment
  - execute the deploy
  - deploy it
Remove? [Yes / Keep / Skip all remaining]
```

   - **Yes** — remove the command key from the JSON object
   - **Keep** — leave it; set `last_used` to today so it won't surface again for another threshold period
   - **Skip all remaining** — stop the loop, write what's been decided so far

7. **Write** the updated `~/.claude/plugins/phrases.json`

8. **Summary:**
```
Cleanup complete.
  Removed: X entries
  Kept:    Y entries
  Run /mapping:list to see your updated registry.
```

## Auto mode

When called with `--auto` (e.g. from a scheduled agent):

1. Read registry and threshold (same as steps 2–4 above)
2. Silently remove all stale entries — no prompts
3. Write the updated file
4. Print a one-line summary: `Mapping cleanup: removed X stale entries, Y kept.`

Auto mode never removes entries still within their grace period (`added_date` within threshold).

## Notes

- Shipped defaults (`mapping/.claude-plugin/phrases.json`) are never touched — only user phrases
- Keeping an entry resets its clock — it won't appear again until another threshold period passes
- To change your threshold: add or edit `_config` in `~/.claude/plugins/phrases.json`:
  ```json
  { "_config": { "cleanup_threshold_days": 30 } }
  ```
