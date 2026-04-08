---
name: start
description: Launch the persistent Playwright test browser, auto-login via SSO, and confirm it is ready for task runs.
---

# Chrome Start

Launch the persistent Playwright test browser for VO E2E task validation.

## Instructions

### 1. Check if browser is already running

Read `C:\dev\vo-playwright-tests\.browser-ws.txt`. If it exists, try a quick connection check:

```bash
cd /c/dev/vo-playwright-tests && cat .browser-ws.txt
```

If the file exists and the browser is responding, report "Browser already running on port <N>" and stop — no need to start a new one.

### 2. Start the browser in the background

```bash
cd /c/dev/vo-playwright-tests && npm run browser:start
```

Run with `run_in_background: true`. The script:
- Reads `SSO_PASS` from `.env` automatically
- Launches headed Chrome with CDP enabled
- Navigates to VO via SSO spoof URL
- Handles Microsoft SSO login automatically
- Writes the CDP port to `.browser-ws.txt` when ready

### 3. Poll for ready signal

After starting, poll `.browser-ws.txt` every 5 seconds (max 60 seconds) until it appears:

```bash
sleep 5 && cat /c/dev/vo-playwright-tests/.browser-ws.txt 2>/dev/null
```

The file contains the CDP port number (e.g. `9222`). Its presence means the browser is up and VO is loaded.

### 4. Report success

Once ready:
- Report: "Browser ready on CDP port <N> — VO loaded at env6"
- Mention: run tasks with `npm run t -- "<query>"` or `npm run t -- story <id>`

### 5. Handle failures

- **Port already in use**: the script handles this gracefully — it tries a CDP close first. If it fails, report the error and suggest `npm run browser:stop` first.
- **Auth failure**: if SSO_PASS is missing or wrong, the script will log an error but keep the browser open for manual login. Report what happened and suggest the user log in manually.
- **Timeout (60s)**: if `.browser-ws.txt` never appears, check the background task output for errors and report them.

## Output

Report one of:
- "Browser already running on port <N>"
- "Browser ready on port <N> — VO loaded. Run tasks with: npm run t -- \"<query>\""
- Error with specific diagnosis
