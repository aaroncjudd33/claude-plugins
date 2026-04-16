# Named Edge Windows

Each workspace in `browser-links.json` maps 1:1 to a named Edge browser window. The workspace name IS the window title.

## Windows

| Window | Workspace | Purpose |
|--------|-----------|---------|
| Jira | Jira | Jira board, calendar, in-progress stories |
| Github | Github | GitHub repos, PRs, Actions workflows |
| Confluence | Confluence | Confluence documentation and wiki |
| Cab | Cab | CAB cards and release calendar |
| AWS | AWS | AWS console and SSO |
| AI | AI | Claude, ChatGPT, Copilot — all AI tools |
| Forge | Forge | Forge personal project — live site and Gmail |
| ForgeDev | ForgeDev | Forge dev tools — GitHub, Vercel, Supabase, Resend, Namecheap |
| Braze | Braze | Braze marketing automation |
| Gmail | Gmail | Gmail (personal/work) |
| Contentful | Contentful | Contentful CMS — translations |
| OpenID | OpenID | OpenID admin tool |
| YouTube | YouTube | YouTube |
| DL | DL | Digital Library |

## Testing Browser

- **Virtual Office - Google Chrome for Testing** — VO app end-to-end testing. Managed by the `e2e` plugin (`/e2e:start`, `/e2e:stop`). Not an Edge window — uses Chrome for Testing.

## Script Reference

Scripts are at `C:\Users\ajudd\.claude\scripts\`:

- `Open-EdgeUrl.ps1 -Url <url> -WindowName <name>` — opens URL in named Edge window. Uses Win32 `EnumWindows` + `SetForegroundWindow` to reliably target the correct window. Creates the window if it doesn't exist.
- `Close-EdgeWindow.ps1 -WindowName <name>` — closes a named Edge window by posting `WM_CLOSE`.

**Why scripts are required:** Edge's `--window-name` flag is silently ignored when Edge is already running. Direct Win32 API calls are the only reliable way to target a specific named window.
