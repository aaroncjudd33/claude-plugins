---
allowed-tools: Read, Write
description: Review and remove phrases unused longer than your configured threshold
---

Remove stale command entries — ones that haven't been touched in a while.

Supports an `--auto` flag for unattended runs (no prompts, silent removal).

## Steps

1. **Check for `--auto` flag** in args. If present, run in auto mode (see [Auto mode](#auto-mode) below) instead of the interactive flow.

2. **Read registry** — read `~/.claude/plugins/phrases.json`. If it doesn't exist or is empty, say: "Nothing to clean up." and stop.

3. **Get threshold** — read `_config.cleanup_threshold_days` (default: 45). Today's date is known from context.

4. **Find stale phrases** — for each command key (skip `_config`), scan each phrase object:
   - `touched` older than threshold → stale
   - No `touched` field → treat as stale (legacy entry, no tracking data)

5. **If none stale** — say: "All phrases touched within the last [threshold] days. Nothing to clean up." and stop.

6. **Display candidates** — group stale phrases by command:

```
Stale phrases (untouched 45+ days):

  /release:deploy — Execute a production deployment
    - deploy to prod       (touched: 2026-03-01)
    - run the deployment   (touched: 2026-02-15)
    - execute the deploy   (never tracked)
    - deploy it            (touched: 2026-03-05)

  /comms:sweep — Clean the inbox
    - triage my email      (touched: 2026-03-10)
    - process my inbox     (never tracked)

X phrases across Y commands. Review each command:
```

7. **Review loop** — for each command with stale phrases, show stale phrases and prompt:

```
/release:deploy — 4 stale phrases:
  - deploy to prod, run the deployment, execute the deploy, deploy it
Remove all / Keep all / Review one by one?
```

   - **Remove all** — delete all stale phrase objects for this command; if `phrases` array is now empty, remove the command key
   - **Keep all** — set `touched` to today on all stale phrases (resets their clock)
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

When called with `--auto`:

1. Read registry and threshold (same as steps 2–4 above)
2. Silently remove all stale phrase objects — no prompts
3. Drop any command key whose `phrases` array is now empty
4. Set `_config.last_cleanup_date` = today
5. Write the updated file
6. Print a one-line summary: `Mapping cleanup: removed X stale phrases across Y commands.`

## Notes

- Shipped defaults (`mapping/.claude-plugin/phrases.json`) are never touched — only user phrases
- Keeping an entry resets its `touched` date — it won't appear again until another threshold period passes
- To change your threshold: edit `_config` in `~/.claude/plugins/phrases.json`:
  ```json
  { "_config": { "cleanup_threshold_days": 60 } }
  ```
- Or just ask Claude: "change my mapping cleanup threshold to 60 days"
