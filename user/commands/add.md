---
name: add
description: Add or update a known customer record in the local user store.
argument-hint: "[custId]"
---

# User Add

Add a YL member account to `~/.claude/memory/known-users.json` for future lookup.

## Instructions

### 1. Collect Fields

If a `custId` was passed as an argument, use it. Otherwise prompt:

```
custId:    (numeric member/customer ID)
Name:      (full name)
Country:   (ISO 2-letter code — US, CA, AU, GB, MX, etc.)
Notes:     (optional — rank, downline, account quirks, etc.)
Nickname:  (optional short alias — e.g. "edie", "aussie")
```

Collect all fields in one message. CustId and Name are required; the rest are optional but Country is strongly encouraged (primary search dimension).

### 2. Read Existing Store

```bash
cat ~/.claude/memory/known-users.json 2>/dev/null || echo "{}"
```

If the custId already exists in the store: show the existing record and confirm: "Update existing record for `<name>` (custId: <id>)? yes / cancel"

Check for nickname conflicts: if the nickname is already used by a different custId, warn: "Nickname '<nick>' is already used by <existing-name>. Proceed anyway? yes / cancel"

### 3. Write

Merge the new/updated record into the JSON object and write back:

```bash
# Write the full updated JSON to the file
# Preserve all existing records; only add/replace the target custId entry
```

Format the JSON with 2-space indentation for readability.

### 4. Confirm

```
Added: Edie Wadsworth (custId: 1443424, US)
       Nickname: edie · Notes: "Sponsor with downline, used for VO rank tests"

Known users: N total
```
