# Finish — Story/CAB Apparatus

Loaded by `finish.md` **only when the session type is `story` or `cab`** (type is known at finish.md Step 0). Plugin / personal / general finishes never read this file — the Jira, epic, Confluence, browser, and Teams logic below is structurally absent for those types, which is both the correctness guarantee (work-tracking steps cannot fire on a non-work session) and the context/thinking-token saving.

`finish.md` stays the orchestrator: it owns every universal step and the **Step 7 batch skeleton** (the slot table, the running numbering, the `go` parsing, the assembled example, the auto-purge). This file holds only the *bodies* of the story/cab-specific pieces. The Step 7 slots defined here splice into the orchestrator's numbered list at the positions its slot table specifies — finish.md assigns each running number `(N)`.

---

## Step 4 — Jira Update *(story/cab only)*

Silently perform Jira actions before the batch block.

**story:**
- Is the story status current? Transition if needed.
- Post a closing Jira comment: what was accomplished this session, what's next (testing, CAB, deployment). Business-readable — no file paths or class names. Check the most recent existing comment first; only post if it doesn't already cover this session's work.
- Read the session file's `Epic` field and fetch Jira issue data to determine if the story was just transitioned to Ready For Test, Approved for Release, or Done this session. Record this for the batch block (slot B below).

**cab:**
- Are the CAB card fields up to date?
- Is the release branch reflected correctly?
- Post a closing comment to each story in `Related stories` (same format as story above).
- Check each story in `Related stories` for an `Epic` field — note any stale epic Story Map entries for the batch block (slot B2 below).

---

## Step 6 — Pre-Batch Prep *(story/cab additions)*

These supplement finish.md Step 6's universal reads (inbox, plugin version, loaded memories). Issue them in the **same parallel batch** as the universal reads.

3. **Epic file:** if session has `Epic` field and the epic file exists, note whether it has a Confluence page link.
4. **Story doc path:** read `paths.jiraStoriesDir` from user-config. Derive doc path: `<jiraStoriesDir>/<jiraProject>/<session-name>-<slug>.md`. Check if it exists.
5. **Browser:** if type is story, check `<voPlaywrightTestsDir>/.browser-ws.txt`. If it exists, read `<voPlaywrightTestsDir>/.browser-owner.txt` and compare owner to current `<slug>/<session-name>`. Include in batch only if owner matches or file is absent.
6. **Teams guide pre-fetch:** if `teams_chat != "none"`, read `~/.claude/plugins/marketplaces/<pluginMarketplaceName>/comms/skills/comms/references/teams-html-guide.md` now — it will be needed if the user answers yes to the Teams question (slot K). (O9)

---

## Step 7 — Story/CAB batch item bodies

Each slot below corresponds to a row in finish.md's Step 7 slot table. finish.md assigns the running number `(N)`; the prompt template and apply-logic live here. Omit any slot whose condition isn't met.

### Slot A — CDK/DynamoDB check *(story/cab)*

Prompt:
```
  (N) CDK/DynamoDB patterns verified?    not-applicable / yes / remind
```
Applying:
- **not-applicable / yes:** proceed silently.
- **remind:** surface after batch: "Run `/yl-cdk-migration` and `/yl-cdk-monitoring` before closing this story."

### Slot B — Epic update *(story/cab, if session file has an `Epic` field AND story moved to completion status this session)*

Prompt:
```
  (N) Epic update (<key>) — mark story done and record final notes?    skip / yes
```
If the epic file has a Confluence page link, include the next slot immediately:
```
  (N+1) Push epic update to Confluence architecture page?    skip / yes
```
Applying:
- **yes:** after batch is processed, ask follow-up: "What should be recorded? (decisions, resolved questions, or final notes)" — justified stop (content couldn't be asked before). Append to epic file. Update Story Map row to Done/RFT with today's date.
- **skip:** no changes to epic file.
- **Confluence sync (B+1):** if yes → push epic memory to linked Confluence page after applying epic changes. If skip → no sync.

### Slot B2 — Epic validation for CAB *(cab only, for each story in `Related stories` whose epic Story Map shows the story as incomplete)*

Prompt:
```
  (N) Epic memory for <key> may be out of date for <story> — update now?    skip / yes
```
Applying: same flow as slot B, per story.

### Slot C — Confluence story page *(story/cab, if a Confluence page was explicitly created and linked for this story)*

Prompt:
```
  (N) Update Confluence page for this story?    skip / yes
```
Applying:
- **yes:** update as clean implementation record — what was built, key decisions, gotchas, what a developer picking this up cold would need to know. Strip planning debris.
- **skip:** no update.

### Slot D — Story doc *(story only, if `paths.jiraStoriesDir` is configured)*

Prompt:
```
  (N) Story doc (exists — update / does not exist — create)?    skip / yes
```
Applying:
- **yes:** write or update with root cause, implementation approach, testing notes, gotchas.
- **skip:** no action.

### Slot E — Browser *(story only, if browser is running and owned by this session)*

Prompt:
```
  (N) Browser still running — stop it?    skip / stop
```
Applying:
- **stop:** run `npm run browser:stop` from `<voPlaywrightTestsDir>`, delete `.browser-ws.txt` and `.browser-owner.txt`.
- **skip:** leave running.

### Slot K — Teams update *(story/cab, if `teams_chat` is not `none`)*

Prompt:
```
  (N) Post closing update to [teams_chat]?    skip / yes
```
Applying:
- **skip:** proceed without posting.
- **yes:** draft the closing update now using the Standard Message Template (read `comms/skills/comms/references/teams-html-guide.md` from the plugin marketplace — already pre-fetched in Step 6), then stop for approval (Pattern 4 — justified second stop, content can't be shown until drafted):
  ```
  Teams update draft:
  ---
  [full draft]
  ---
  Send this? (go / edit: <your version> / skip)
  ```
  Send on `go`, apply edits on `edit:`, skip on `skip`.

---

## Step 9 — Post-deployment checks *(story only)*

Check the current `Post-deployment checks:` field (if present):
```
Post-deployment checks — anything to add or update? (enter new checks, or 'skip')
```
If the user enters checks, append as `- [ ] <check>` items. If the field doesn't exist and the user enters checks, create it. If the user skips, preserve the existing value as-is. (This is a brief inline prompt — not a batched item — because it only applies to story type and requires free-text input.)
