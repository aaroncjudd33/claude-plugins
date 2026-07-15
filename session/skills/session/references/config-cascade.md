# Config Cascade

Generic global→project resolver for settings that need a per-repo override on top of a
user-wide default (acp-ajudd#120). Loaded on demand by any command flow that needs to
resolve a cascade-able key — today, just `start.md`'s zone/flow routing.

**Algorithm** (three tiers, most-specific wins):

```
resolve(key, hardcoded_default):
  1. project_value = read ~/.claude/config/<slug>.json → <key>   (if present & non-empty)
  2. global_value  = read ~/.claude/plugins/user-config.json → <key>   (if present & non-empty)
  3. effective = project_value, else global_value, else hardcoded_default
```

Both files are flat JSON — the key lives at the top level (no nested `settings` object).
Read them the same way other single-field config reads in this repo already do (a direct
`Read` of the file, or `grep -o '"<key>"\s*:\s*"[^"]*"'` when only a quick existence check
is needed) — no new script, no new parsing dependency.

**Session-level tier: reserved, not implemented.** No session-level config store exists yet.
Noted here so a future tier (e.g. a per-session override) slots into the same 3-line lookup
without redesigning the cascade — it would simply become the new most-specific tier, checked
before `project_value`.

## Cascade-able keys (today)

| Key | Values | Hardcoded default | Consumed by |
|-----|--------|--------------------|-------------|
| `startFlow` | `wizard` \| `classic` | `wizard` | `start.md` — picks which flow file to load, all zones (acp-ajudd#120; `wizard` is `start-wizard.md`, one file for every zone, shipped acp-ajudd#124) |

**Adding a new cascade-able key:** document its allowed values + hardcoded default in the
table above, write it at whichever tier(s) need an override, and resolve it with the same
3-line lookup — no new mechanism is needed per key.
