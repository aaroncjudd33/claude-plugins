---
description: Launch the persistent Playwright test browser, auto-login via SSO, and confirm it is ready for task runs.
allowed-tools: [Bash]
---

# E2E Start

Launch the persistent Playwright test browser for automated task validation.

## Instructions

### 0. Resolve e2e directory

Read `~/.claude/plugins/user-config.json` and extract:
- `paths.pluginMarketplaceName` (default: `ajudd-claude-plugins`)
- `paths.workReposDir`

Read the active session file to check for an existing `e2eTestsDir` field:

```bash
slug=$(basename $(pwd))
session_name=$(cat ~/.claude/memory/sessions/$slug/_active 2>/dev/null)
```

If `session_name` is set, read `~/.claude/memory/sessions/<slug>/<session_name>.md` and look for:
```
- **E2E tests dir:** /path/to/tests
```

**If found and the directory exists:** use it as **E2E_DIR** and skip to Step 1.

**If not found or directory does not exist:**

Ask:
```
Where are the Playwright tests for this project?
  Type a path to an existing directory, or type 'new' to create one now.
```

- **Path provided:** verify the directory exists, then save `e2eTestsDir` to the session file (see below) and use as E2E_DIR. Skip scaffolding.
- **'new':** proceed to scaffold a fresh test directory.

**Scaffold flow:**

1. Determine target path: `<workReposDir>/<slug>-playwright-tests`
   - If `workReposDir` is empty, ask: "Where should the new test directory be created? (parent folder)"
   - Append `/<slug>-playwright-tests` to the chosen parent.

2. Copy the runner scaffold:
   ```bash
   RUNNER=~/.claude/plugins/marketplaces/<pluginMarketplaceName>/e2e/runner
   cp -r "$RUNNER" "<target-path>"
   ```

3. Ask: "What URL should open when the browser starts? (e.g. http://localhost:3000)"
   Write `.e2e.json` in the new directory:
   ```json
   { "tabs": [{ "url": "<url>", "bringToFront": true }] }
   ```

4. Copy `.env.example` to `.env`:
   ```bash
   cp "<target-path>/.env.example" "<target-path>/.env"
   ```
   Tell the user: "Edit `<target-path>/.env` to set `SSO_EMAIL` and `SSO_PASS` if your app uses Microsoft SSO. Leave blank if not needed."

5. Install dependencies:
   ```bash
   cd "<target-path>" && npm install
   ```
   Run with `run_in_background: false` — wait for completion.

6. Install Playwright browsers if needed:
   ```bash
   cd "<target-path>" && npx playwright install chromium
   ```

7. Report: "Test directory created at `<target-path>`. Ready to launch."

**Save e2eTestsDir to session file:**

After resolving the path (either provided or scaffolded), write it to the active session file.
Find the `- **E2E tests dir:**` line and update it, or append it after the `Next step:` line if absent:
```
- **E2E tests dir:** <resolved-path>
```

Use **E2E_DIR** = the resolved path for all steps below.

### 1. Check if browser is already running

```bash
port=$(cat "$E2E_DIR/.browser-ws.txt" 2>/dev/null)
if [ -n "$port" ]; then
  curl -s "http://localhost:$port/json/version" > /dev/null 2>&1 && echo "alive:$port" || echo "stale"
fi
```

- **`alive:<port>`** — report "Browser already running on port `<N>`" and stop.
- **`stale`** — delete stale files and proceed to Step 2:
  ```bash
  rm "$E2E_DIR/.browser-ws.txt"
  rm "$E2E_DIR/.browser-owner.txt" 2>/dev/null
  ```
- **No file** — proceed to Step 2.

### 2. Start the browser

```bash
cd "$E2E_DIR" && npm run browser:start
```

Run with `run_in_background: true`.

### 3. Poll for ready signal

```bash
for i in $(seq 1 12); do
  sleep 5
  port=$(cat "$E2E_DIR/.browser-ws.txt" 2>/dev/null)
  [ -n "$port" ] && echo "ready:$port" && break
  echo "waiting... attempt $i/12"
done
```

### 4. Write ownership record

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

- "Browser ready on CDP port <N>"
- "Run tasks with: `npm run t -- \"<query>\"`  or  `npm run t -- --list`"

### 6. Handle failures

- **Port in use:** the start script handles graceful close. If it fails, suggest `npm run browser:stop` first.
- **Auth failure:** SSO_PASS missing or wrong — browser stays open for manual login. Report and suggest manual login.
- **Timeout (60s):** check background output, clean up stale files:
  ```bash
  rm "$E2E_DIR/.browser-ws.txt" 2>/dev/null
  rm "$E2E_DIR/.browser-owner.txt" 2>/dev/null
  ```
