---
description: Stop the persistent Playwright test browser gracefully.
allowed-tools: [Bash]
---

# E2E Stop

Stop the persistent Playwright test browser.

## Instructions

### 1. Check if browser is running

```bash
cat /c/dev/vo-playwright-tests/.browser-ws.txt 2>/dev/null
```

If the file does not exist, report "No browser running" and stop.

### 2. Stop the browser

```bash
cd /c/dev/vo-playwright-tests && npm run browser:stop
```

### 3. Clean up state file

```bash
rm /c/dev/vo-playwright-tests/.browser-ws.txt 2>/dev/null
```

### 4. Report

"Browser stopped."
