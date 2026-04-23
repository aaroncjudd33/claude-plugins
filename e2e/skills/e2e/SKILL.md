---
name: e2e
description: "Background skill — do not run directly. Use /e2e:start to launch the test browser. Auto-loads when: launching Playwright, starting E2E tests, or managing the persistent browser."
---

# E2E / Playwright Skill

## Purpose

Manage a persistent Playwright test browser for automated task validation. The browser stays open between task runs — tasks connect via CDP, run, and disconnect without closing it. Works for any web project, not just VO.

## Project Location

The Playwright test directory (`E2E_DIR`) is stored per-session in the active session file as `E2E tests dir:`. On first use for a project, `/e2e:start` either prompts for an existing path or scaffolds a fresh test directory from the runner template bundled in this plugin.

Convention: `<workReposDir>/<project-abbreviation>-playwright-tests/` as a sibling to the project repo.
- Example: `vo-playwright-tests/` next to `virtual-office-vp/`
- Example: `glb-playwright-tests/` next to `gen-leadership-bonus/`

## Runner Scaffold

The plugin ships a generic runner at `~/.claude/plugins/marketplaces/<pluginMarketplaceName>/e2e/runner/`. When a test directory is scaffolded, this template is copied to the target location and `npm install` is run automatically. The scaffold includes:

- `scripts/browser-start.ts` — launches Chrome via CDP, loads tabs from `.e2e.json`
- `scripts/browser-stop.ts` — closes browser gracefully
- `helpers/runner.ts` — task/story registration and run framework
- `scripts/run-checks.ts` — task runner entry point (add your task imports here)
- `package.json`, `tsconfig.json`, `playwright.config.ts`, `.env.example`, `.gitignore`

## Key Commands

Run from `E2E_DIR`:

```
npm run browser:start     ← launch Chrome, write CDP port to .browser-ws.txt
npm run browser:stop      ← close browser gracefully
npm run t -- "<query>"    ← run tasks matching name or tag
npm run t -- story <id>   ← run all tasks for a story
npm run t -- --list       ← list all tasks
```

## Tab Configuration

`browser:start` reads `.e2e.json` in the test directory for which URLs to open:
```json
{ "tabs": [{ "url": "http://localhost:3000", "bringToFront": true }] }
```
If no `.e2e.json` exists, falls back to `BASE_URL` from `.env`.

## Environment Variables (.env)

- `SSO_EMAIL` / `SSO_PASS` — Microsoft SSO auto-login (leave blank if not needed)
- `TARGET_DOMAIN` — domain used to identify the target page in the browser
- `BASE_URL` — base URL for Playwright tests
- `CDP_PORT` — default 9222; change if port is in use
- `HTTP_AUTH_USER` / `HTTP_AUTH_PASS` — HTTP Basic Auth if required

## CDP Connection Details

- Default port: 9222. If held, set `CDP_PORT=9333` in `.env`
- IPv6 on Windows — Chrome binds to `[::1]` not `127.0.0.1`. The runner handles both.
- `.browser-ws.txt` contains the CDP port number — written when the browser is ready

## Never Force-Kill

Never use `taskkill /F` or `kill -9` to close Chrome. Use `npm run browser:stop`. Force-killing triggers endpoint security alerts.
