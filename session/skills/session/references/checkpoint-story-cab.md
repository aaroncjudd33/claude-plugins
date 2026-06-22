# Checkpoint — Story/CAB Apparatus

Loaded by `checkpoint.md` **only when the session type is `story` or `cab`** (type is known at checkpoint.md Step 0). Plugin / personal / general checkpoints never read this file — the Jira and epic logic below is structurally absent for them, which is both the correctness guarantee and the context/thinking-token saving on a command that runs frequently.

`checkpoint.md` stays the orchestrator: it owns every universal step and the **Step 6 batch skeleton** (slot table, running numbering, `go` parsing, assembled example, auto-purge). This file holds only the *bodies* of the story/cab-specific pieces. The Step 6 slots defined here splice into the orchestrator's numbered list at the positions its slot table specifies — checkpoint.md assigns each running number `(N)`.

These bodies are distinct from the `finish-story-cab.md` equivalents: checkpoint posts a *progress* comment (vs. finish's *closing* comment) and records *decisions or blockers* (vs. finish's *final notes / mark done*).

---

## Step 5a — Jira Progress Comment *(story/cab only)*

Post a 1–2 sentence progress comment to the Jira story.

- **story:** story key = session name (e.g. `BPT2-6258`)
- **cab:** post to each story in `Related stories`

Content: current status + what was just accomplished + what's next. Business-readable — no file paths, class names, or token names. Example: *"Extended filter validation: all three input types now show required errors immediately on Add/Apply click. Committed and deploying to env6 for QA review."* **Never mention "create PR to master" or "merge to master" as what's next** — that belongs to the release plugin, not the session.

Before posting, check if the most recent Jira comment is from today and already covers this milestone — if so, skip.

---

## Step 5b — Epic Check *(story/cab only)*

If the session file has an `Epic` field, read `~/.claude/memory/epics/<key>.md` (to have it in context for the batch block). Note whether the epic file exists and whether it has a Confluence link. This check is silent — the user question goes in Step 6 (slot C).

---

## Step 6 — Story/CAB batch item bodies

Each slot below corresponds to a row in checkpoint.md's Step 6 slot table. checkpoint.md assigns the running number `(N)`; the prompt template and apply-logic live here. Omit any slot whose condition isn't met.

### Slot A — CDK/DynamoDB check *(story/cab, if a commit was just made or is about to be)*

Prompt:
```
  (N) CDK/DynamoDB patterns verified?    not-applicable / yes / remind
```
Applying:
- **not-applicable / yes:** proceed silently.
- **remind:** surface note after the batch: "Run `/yl-cdk-migration` and `/yl-cdk-monitoring` before calling this story done."

### Slot C — Epic update *(story/cab, if session file has an `Epic` field)*

Prompt:
```
  (N) Epic update (<key>) — decisions or blockers to record?    skip / yes
```
If the epic file has a Confluence link, include the next slot immediately after:
```
  (N+1) Push epic update to linked Confluence page?    skip / yes
```
Applying:
- **yes:** after the batch is fully processed, ask as a follow-up: "What should be recorded? (decisions, resolved questions, or blockers)" — append to the epic file: new decisions under `## Architecture Decisions` as `### [DECIDED] <title>`; resolved questions moved to `## Resolved` with answer and `[YYYY-MM-DD <session-name>]` note. This follow-up stop is justified — content couldn't be asked before knowing the answer was "yes".
- **skip:** no changes to epic file.
- **Confluence sync (C+1):** only applies if epic update = yes. **yes** → push epic memory update to the linked Confluence page after applying epic changes. **skip** → no sync.
