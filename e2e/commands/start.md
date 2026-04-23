---
description: Launch the persistent Playwright test browser, auto-login via SSO, and confirm it is ready for task runs.
allowed-tools: [Bash]
---

# E2E Start

Launch the persistent Playwright test browser for VO E2E task validation.

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

### 1. Check if browser is already running

Read `$E2E_DIR/.browser-ws.txt` and do a live CDP probe:

```bash
port=$(cat "$E2E_DIR/.browser-ws.txt" 2>/dev/null)
if [ -n "$port" ]; then
  curl -s "http://localhost:$port/json/version" > /dev/null 2>&1 && echo "alive:$port" || echo "stale"
fi
```

- If `alive:<port>` — report "Browser already running on port `<N>`" and stop.
- If `stale` — the file exists but Chrome is not responding (crashed or killed). Delete the stale files and proceed to Step 2:

```bash
rm "$E2E_DIR/.browser-ws.txt"
rm "$E2E_DIR/.browser-owner.txt" 2>/dev/null
```

- If no file — proceed to Step 2.

### 2. Start the browser in the background

```bash
cd "$E2E_DIR" && npm run browser:start
```

Run with `run_in_background: true`. The script:
- Reads `SSO_PASS` from `.env` automatically
- Launches headed Chrome with CDP enabled
- Navigates to VO via SSO spoof URL
- Handles Microsoft SSO login automatically
- Writes the CDP port to `.browser-ws.txt` when ready

### 3. Poll for ready signal

Poll `$E2E_DIR/.browser-ws.txt` every 5 seconds for up to 60 seconds:

```bash
for i in $(seq 1 12); do
  sleep 5
  port=$(cat "$E2E_DIR/.browser-ws.txt" 2>/dev/null)
  [ -n "$port" ] && echo "ready:$port" && break
  echo "waiting... attempt $i/12"
done
```

The file contains the CDP port number (e.g. `9222`). Its presence means the browser is up and VO is loaded. If the loop completes without finding the file, proceed to Step 5 (timeout path).

### 4. Write ownership record

Derive the owner ID and write `.browser-owner.txt` alongside `.browser-ws.txt`:

```bash
slug=$(basename $(pwd))
session_name=$(cat ~/.claude/memory/sessions/$slug/_active 2>/dev/null)
if [ -n "$session_name" ]; then
  echo "$slug/$session_name" > "$E2E_DIR/.browser-owner.txt"
else
  echo "$slug" > "$E2E_DIR/.browser-owner.txt"
fi
```

### 5. Report success

Once ready:
- Report: "Browser ready on CDP port <N> — VO loaded at env6"
- Mention: run tasks with `npm run t -- "<query>"` or `npm run t -- story <id>`

### 6. Handle failures

- **Port already in use**: the script handles this gracefully — it tries a CDP close first. If it fails, report the error and suggest `npm run browser:stop` first.
- **Auth failure**: if SSO_PASS is missing or wrong, the script will log an error but keep the browser open for manual login. Report what happened and suggest the user log in manually.
- **Timeout (60s)**: if `.browser-ws.txt` never appears, check the background task output for errors and report them. Clean up any partial state files:
  ```bash
  rm "$E2E_DIR/.browser-ws.txt" 2>/dev/null
  rm "$E2E_DIR/.browser-owner.txt" 2>/dev/null
  ```

## Output

Report one of:
- "Browser already running on port <N>"
- "Browser ready on port <N> — VO loaded. Run tasks with: npm run t -- \"<query>\""
- Error with specific diagnosis
