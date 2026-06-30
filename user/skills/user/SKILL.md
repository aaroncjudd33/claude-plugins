---
name: user
description: "Known customer lookup skill. Load whenever resolving a person to a custId, running member-specific operations in e2e or oracle-legacy, or managing the known-users store (/user:add, /user:find, /user:remove)."
---

# User Skill — Known Customer Lookup

Manages a local store of YL member accounts used for testing and reference. The store lives in global memory and is accessible to any plugin that needs to resolve a name or nickname to a custId.

---

## Storage

**Path:** `~/.claude/memory/known-users.json`

**Global tier only — never migrated, never git-tracked.** This file contains real names and member IDs (PII). It must never be copied to a repo, included in a `/session:migrate` run, or referenced from any memory index. The `.json` extension keeps it out of memory plugin scans (which use `*.md` globs).

---

## Schema

The file is a JSON object keyed by `custId` (string). Every record:

```json
{
  "1443424": {
    "nickname": "edie",
    "name": "Edie Wadsworth",
    "country": "US",
    "notes": "Sponsor with downline, used for VO rank tests"
  },
  "7890123": {
    "nickname": "aussie",
    "name": "Jane Smith",
    "country": "AU",
    "notes": "Australian member, tests international shipping flow"
  }
}
```

Fields:
- `custId` (key) — YL customer/member ID, numeric string
- `name` — full name
- `country` — ISO 2-letter code (US, CA, AU, GB, MX, etc.)
- `notes` — freeform; anything worth knowing (rank, downline, enrollment year, account quirks)
- `nickname` — optional short alias for quick reference; not unique-enforced but should be

---

## Lookup Pattern (for consumer plugins)

When a user references a person by name or nickname in any member-specific operation, check `~/.claude/memory/known-users.json` before prompting for a custId:

```bash
# Read the file — it's small, always load the whole thing
cat ~/.claude/memory/known-users.json 2>/dev/null || echo "{}"
```

Match strategy (in order):
1. Exact nickname match (`nickname` field)
2. Case-insensitive name match (`name` field)
3. Partial name match

If a match is found: use its `custId` and report to the user which record was resolved (e.g., "Using Edie Wadsworth (custId: 1443424)").

If no match: ask the user for the custId directly, then offer to save it: "Add this person to known users? (y/n)"

---

## Search

`/user:find` supports:
- `country:XX` — filter by ISO country code (case-insensitive)
- Free text — matched against `name`, `nickname`, and `notes` (case-insensitive substring)
- Combinations: `country:AU downline` → Australian members with "downline" in notes

---

## Consumer Plugins

Any plugin that performs member-specific operations should reference this skill and apply the Lookup Pattern above:

- **e2e** — resolving a member for Playwright spoofing / URL injection
- **oracle-legacy** — customer-lookup queries (`/oracle-legacy:customer-lookup`)
- Any plugin that constructs member-specific URLs or API calls
