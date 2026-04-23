---
description: Stop the persistent Playwright test browser gracefully.
allowed-tools: [Bash]
---

# E2E Stop

Stop the persistent Playwright test browser.

## Instructions

### 0. Resolve e2e directory

Read the active session file to find `E2E tests dir`:

```bash
slug=$(basename $(pwd))
session_name=$(cat ~/.claude/memory/sessions/$slug/_active 2>/dev/null)
```

If `session_name` is set, read `~/.claude/memory/sessions/<slug>/<session_name>.md` and extract the `- **E2E tests dir:**` line.

If not found in the session file, ask: "Where is your Playwright test directory? (e.g. /c/dev/vo-playwright-tests)"

Use the resolved path as **E2E_DIR**.

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
