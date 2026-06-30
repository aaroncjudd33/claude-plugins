---
name: add
description: Add or update a known customer record in the local user store. Auto-populates name and country from Oracle when only a custId is provided.
argument-hint: "[custId]"
---

# User Add

Add a YL member account to `~/.claude/memory/known-users.json` for future lookup.

## Instructions

### 1. Determine Entry Mode

**Auto-populate mode (default):** A custId was passed as an argument (or is the only thing provided). Query Oracle Clone for name and country — the user only needs to confirm the nickname.

**Manual mode:** No custId, or the user explicitly provides name + country up front. Collect all fields in one prompt block.

---

### 1a. Auto-Populate from Oracle (custId provided)

Run a targeted query against Oracle Clone (direct connection, no StrongDM needed):

**Bash:**
```bash
cat << 'SQLEOF' | /c/tools/sqlcl/sqlcl/bin/sql -S 'cmsuser/WychekEs8#Stasck@oracln.yleo.us:1521/ylcln.yleo.us'
SET PAGESIZE 50
SET LINESIZE 300
SET TRIMOUT ON
SET TRIMSPOOL ON
SET SQLFORMAT ansiconsole
SET HEADING ON
SET FEEDBACK OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE
ALTER SESSION SET current_schema = cmsuser;

SELECT c.CUSTID, c.NAME, c.FIRSTNAME, c.LASTNAME, co.ISOCOUNTRYCODE AS COUNTRY
FROM CUSTOMER# c
LEFT JOIN COUNTRY# co ON c.MAINCOUNTRYID = co.COUNTRYID
WHERE c.CUSTID = CUSTID_PLACEHOLDER;

exit
SQLEOF
```

**Replace `CUSTID_PLACEHOLDER` with the actual custId before running.**

If the query returns a row:
- `NAME` = full display name (use this; fallback to `FIRSTNAME + ' ' + LASTNAME` if NAME is null/empty)
- `ISOCOUNTRYCODE` = ISO 2-letter country code

Show the resolved record and ask **only** for nickname:

```
Found: Edie Wadsworth (custId: 1443424, US)

Nickname (optional — e.g. "edie"): 
Notes (optional — purpose, test scenarios, etc.):
```

If the query returns no rows: try prod next (see below).

If Oracle is unreachable (connection error, SQLcl not found): warn and fall through to manual mode (Step 1b).

**Prod fallback** — only if Clone returned no rows:

```bash
# Requires StrongDM tunnel: Ylprds2 Read Prod on 127.0.0.1:10013
cat << 'SQLEOF' | /c/tools/sqlcl/sqlcl/bin/sql -L anyuser/password@//127.0.0.1:10013/ylprd.yleo.us
SET PAGESIZE 50
SET LINESIZE 300
SET TRIMOUT ON
SET TRIMSPOOL ON
SET SQLFORMAT ansiconsole
SET HEADING ON
SET FEEDBACK OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE
ALTER SESSION SET current_schema = cmsuser;

SELECT c.CUSTID, c.NAME, c.FIRSTNAME, c.LASTNAME, co.ISOCOUNTRYCODE AS COUNTRY
FROM CUSTOMER# c
LEFT JOIN COUNTRY# co ON c.MAINCOUNTRYID = co.COUNTRYID
WHERE c.CUSTID = CUSTID_PLACEHOLDER;

exit
SQLEOF
```

If prod returns a row: use it (same extraction logic). If prod also returns no rows: "Customer [custId] not found in Clone or Prod." — fall through to manual mode (Step 1b). If prod is unreachable (StrongDM not connected): "Customer not found in Clone, and Prod StrongDM tunnel is not available." — fall through to manual mode (Step 1b).

---

### 1b. Manual Entry

Prompt for all fields in one message:

```
custId:    (numeric member/customer ID)
Name:      (full name)
Country:   (ISO 2-letter code — US, CA, AU, GB, MX, etc.)
Notes:     (optional — rank, downline, account quirks, etc.)
Nickname:  (optional short alias — e.g. "edie", "aussie")
```

CustId and Name are required; Country is strongly encouraged (primary search dimension).

---

### 2. Read Existing Store

```bash
cat ~/.claude/memory/known-users.json 2>/dev/null || echo "{}"
```

If the custId already exists: show the existing record and confirm: "Update existing record for `<name>` (custId: <id>)? yes / cancel"

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
       Nickname: edie · Notes: "commission-payments test member, period 533 validation"

Known users: N total
```
