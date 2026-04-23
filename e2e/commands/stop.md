---
description: Stop the persistent Playwright test browser gracefully.
allowed-tools: [Bash]
---

# E2E Stop

Stop the persistent Playwright test browser.

## Instructions

### 0. Resolve e2e directory

Read `~/.claude/plugins/user-config.json` and extract `paths.voPlaywrightTestsDir`.

If the field is missing or empty:
```
Where is your vo-playwright-tests directory?
(e.g. /c/dev/vo-playwright-tests)
```
Write the answer to `paths.voPlaywrightTestsDir` in `~/.claude/plugins/user-config.json` before continuing.

Use the resolved path as **E2E_DIR** throughout all steps below.

### 1. Check if browser is running

```bash
cat "$E2E_DIR/.browser-ws.txt" 2>/dev/null
```

If the file does not exist, report "No browser running" and stop.

### 2. Stop the browser

```bash
cd "$E2E_DIR" && npm run browser:stop
```

### 3. Clean up state files

```bash
rm "$E2E_DIR/.browser-ws.txt" 2>/dev/null
rm "$E2E_DIR/.browser-owner.txt" 2>/dev/null
```

### 4. Report

"Browser stopped."
