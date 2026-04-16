---
name: links
description: This skill should be used when the user wants to open a URL, navigate to a named link, open or manage a workspace in Edge, close a workspace window, search for a saved link, add a new link or workspace, or when any plugin needs to open something in the browser. Trigger phrases include "open", "go to", "launch", "show me", "open workspace", "close workspace", "close window", "close the [name] window", "search links", "add link", "register link", "open BPT2-XXXX", "open CAB-XXX", "open the Jira workspace", "open Github workspace".
---

# Links Skill

Central browser and link management. All URL opens go through this skill — named links, dynamic links (stories, PRs, CABs), and workspaces (named Edge windows).

---

## Data File

`C:\Users\ajudd\.claude\browser-links.json`

Read before any link operation. Write back after any mutation.

---

## Schema

```json
{
  "prefixDefaults": {
    "story":   "Jira",
    "jira":    "Jira",
    "cab":     "Cab",
    "git":     "Github",
    "pr":      "Github",
    "actions": "Github",
    "docs":    "Confluence",
    "aws":     "AWS",
    "ai":      "AI",
    "claude":  "AI",
    "forge":   "Forge",
    "trans":   "Contentful",
    "openid":  "OpenID",
    "youtube": "YouTube",
    "braze":   "Braze"
  },
  "workspaces": {
    "WorkspaceName": {
      "description": "...",
      "type": "story|cab",
      "links": ["key1", "key2"]
    }
  },
  "links": {
    "prefix:name": {
      "url": "https://...",
      "description": "...",
      "window": "OverrideWindowName"
    }
  }
}
```

`window` on a link is a hard override — the link always opens in that window regardless of workspace context. Omit it in most cases; `prefixDefaults` handles resolution automatically.

`type` on a workspace identifies story (`story`) or CAB (`cab`) workspaces. Omit it for custom workspaces — most workspaces are custom and have no type.

---

## Window Resolution (priority order)

1. Link has explicit `window` field → always use that window
2. Opening via a workspace → use the workspace name as the window
3. Opening standalone → look up the key's prefix in `prefixDefaults`
4. No match → open without a named window (default browser behavior)

---

## Scripts

Location: `C:\Users\ajudd\.claude\scripts\`

```bash
# Open URL in named Edge window (creates window if not found)
powershell -ExecutionPolicy Bypass -File "C:\Users\ajudd\.claude\scripts\Open-EdgeUrl.ps1" -Url "<url>" -WindowName "<window>"

# Close a named Edge window
powershell -ExecutionPolicy Bypass -File "C:\Users\ajudd\.claude\scripts\Close-EdgeWindow.ps1" -WindowName "<window>"
```

**IMPORTANT:** Never use `start <url>` or `Start-Process msedge` directly — Edge's `--window-name` flag is silently ignored when Edge is already running. Always use `Open-EdgeUrl.ps1`.

---

## Opening a Single Link

1. Read `browser-links.json`
2. Look up key in `links` section
3. Resolve window using priority order above
4. Run `Open-EdgeUrl.ps1 -Url <url> -WindowName <window>`
5. Print: `Opened [key] in [window] window`

---

## Opening a Workspace

1. Read `browser-links.json`
2. Look up workspace in `workspaces` section
3. Window = workspace name
4. For each key in workspace's `links` array:
   - Look up link in `links` section
   - If link has `window` field → use that (link wins)
   - Else → use workspace name
   - Run `Open-EdgeUrl.ps1`
   - Wait 2 seconds after first URL (window creation), 1 second between subsequent URLs
5. Print: `Opened [N] links in [workspace] workspace`

---

## Ambiguity

If a query matches both a workspace name and a link key → ask: "Found both a workspace and a link named '[arg]'. Open workspace (all links) or just the link?"

---

## Link Registration from Other Plugins

When creating a resource, register it in `browser-links.json` and add it to the appropriate workspace. Pattern:

1. Read `browser-links.json`
2. Add entry to `links` section: `{ url, description }`
3. Add key to target workspace's `links` array (create workspace first if it doesn't exist)
4. Write back

| Event | Key | Workspace |
|-------|-----|-----------|
| `story:create` or session pickup | `story:BPT2-XXXX` | Create `BPT2-XXXX` (type: story) |
| `release:create` | `cab:CAB-XXX` | Add to linked story workspace(s) |
| PR created | `pr:repo-name#NNN` | Add to story workspace |
| Actions run | `actions:repo-name#run-NNN` | Add to story workspace |

---

## Naming Conventions

| Prefix | Meaning | Example |
|--------|---------|---------|
| `story:` | Jira BPT2 story | `story:BPT2-6258` |
| `cab:` | CAB card | `cab:CAB-1234` |
| `pr:` | GitHub pull request | `pr:virtual-office#789` |
| `actions:` | GitHub Actions run | `actions:virtual-office#run-456` |
| `git:` | GitHub repo root | `git:virtual-office` |
| `jira:` | Jira navigation (non-story) | `jira:board`, `jira:calendar` |
| `docs:` | Confluence page or space | `docs:bpt2` |
| `aws:` | AWS console link | `aws:accounts` |
| `ai:` | AI tool | `ai:claude`, `ai:gpt` |
| `claude:` | Claude-specific URLs | `claude:usage` |
| `forge:` | Forge personal project — Forge and ForgeDev workspaces | `forge:ui`, `forge:supabase` |
| `yl:` | Young Living internal tools | `yl:bridge` |
| `trans:` | Contentful / translations | `trans:login` |
| `openid:` | OpenID admin tool | `openid:dashboard` |
| `youtube:` | YouTube | `youtube:volbeat` |
| `braze:` | Braze | `braze:login` |

---

## Reference

See `references/browser-windows.md` for the full list of named Edge windows and their purposes.
