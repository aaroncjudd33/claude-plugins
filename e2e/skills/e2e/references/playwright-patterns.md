# Playwright E2E Patterns

Cross-project patterns for the persistent browser + task model used by this plugin.

## Core Pattern: Persistent Browser + CDP

The browser launches once and stays open between task runs. Tasks connect via Chrome DevTools Protocol (CDP), execute, and disconnect without closing the browser. This avoids re-authentication on every run.

```
npm run browser:start    ← launch, auth, write CDP port to .browser-ws.txt
npm run browser:stop     ← close gracefully via CDP Browser.close
npm run t -- "<query>"   ← run tasks matching name or tag
npm run t -- --list      ← list all available tasks
```

## Task System

Tasks are functions with a name and a tags array. Run by name substring or tag:

```typescript
task('Page title is correct', ['aria', 'validate'], async (page) => {
  // self-navigate, assert, return { pass: true/false, message: '...' }
});
```

New tasks: add a file in `tasks/`, import it in the runner. The persistent browser + tags pattern is project-agnostic — add navigation helpers and reuse the same structure.

## Never Force-Kill the Browser

Never use `taskkill /F` or `kill -9` to close Chrome. Use `npm run browser:stop` (graceful CDP close). Force-killing triggers endpoint security alerts on managed machines.

## CDP on Windows — IPv6

Chrome binds CDP to `[::1]` not `127.0.0.1` on Windows. Connection code must try both. The runner handles this automatically.

## Port Conflicts

If the default CDP port (9222) is held: `CDP_PORT=9333 npm run browser:start`. Check `.browser-ws.txt` for the active port.

## Project Setup Checklist

For any new project using this pattern:
1. Add a `.npmrc` pointing to public npm registry (avoids CodeArtifact issues in personal projects)
2. Use `--remote-debugging-port=<port>` in the Chrome launch flags
3. Write the CDP port to a `.browser-ws.txt` file when ready — other scripts poll for it
4. Define a `t` script in `package.json` that invokes the task runner with tag/name filtering
