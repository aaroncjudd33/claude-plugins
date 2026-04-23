# Post-Creation Steps for Confluence Pages

After successfully creating any Confluence page, always perform these two steps before reporting done:

1. **Register the link** — add it via the links plugin so it's findable by key later
2. **Open it** — open it in the Confluence named browser workspace so the user can verify it

**Why:** Users expect both steps to happen automatically. The link registry keeps everything findable across sessions. Opening it immediately lets the user confirm the page rendered correctly.

**How:** After `createConfluencePage` succeeds:
1. Add to `browser-links.json`: `"docs:<page-key>": { "url": "<confluence-url>", "description": "<page title>" }`
2. Run `Open-EdgeUrl.ps1 -Url <confluence-url> -WindowName Confluence`
