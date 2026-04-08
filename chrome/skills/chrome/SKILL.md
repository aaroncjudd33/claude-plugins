# Chrome / Playwright Browser Skill

## Purpose

Manage the persistent Playwright test browser used for VO E2E task validation. The browser stays open between task runs — tasks connect via CDP, run, and disconnect without closing it.

## Project Location

`C:\dev\vo-playwright-tests\` (standalone, sibling to `C:\dev\virtual-office\`)

## Key Commands

```
npm run browser:start     ← launch Chrome, auto-login via SSO, write CDP port to .browser-ws.txt
npm run browser:stop      ← close browser gracefully
npm run t -- "<query>"    ← run tasks matching name or tag
npm run t -- story <id>   ← run all tasks for a story
npm run t -- --list       ← list all tasks
```

## SSO_PASS

`SSO_PASS` is stored in the project's `.env` file. `browser:start` reads it automatically via dotenv. No need to pass it manually.

## Start Sequence

When starting the browser:

1. Run `npm run browser:start` in the background from `C:\dev\vo-playwright-tests\`
2. Poll for `.browser-ws.txt` to appear (signals browser is ready and on VO)
3. Once ready, confirm the CDP port and report success

Use `run_in_background: true` on the Bash tool. Poll with a short sleep + cat `.browser-ws.txt`.

## Auth Details

Two auth layers on YL dev environments:
1. **HTTP Basic Auth** — credentials in `.env` as `HTTP_AUTH_USER` / `HTTP_AUTH_PASS`
2. **Microsoft SSO** — `SSO_EMAIL` + `SSO_PASS` in `.env`. `browser:start` handles the full login flow automatically.

After a successful login, `auth.json` is saved. The session lasts ~20 minutes. `browser:start` will re-authenticate if the session has expired.

## CDP Connection Details

- Default port: 9222. If held, use `CDP_PORT=9333 npm run browser:start`
- IPv6 on Windows — Chrome binds to `[::1]` not `127.0.0.1`. The runner handles both.
- `.browser-ws.txt` contains the CDP port number — written when the browser is ready

## Task Navigation

Tasks use `waitUntil: 'domcontentloaded'` for `page.goto` — the default `load` hangs on VO.

Origin detection: use `VO_BASE_URL` from `.env` (default `https://env6.youngliving.com`) as fallback — never use the current page origin if it's not a `youngliving.com` URL (e.g. after a redirect to auth-stage or Microsoft login).

## Never Force-Kill

Never use `taskkill /F` or `kill -9` to close Chrome. Use `npm run browser:stop` or the graceful CDP close. Force-killing triggers endpoint security alerts.
