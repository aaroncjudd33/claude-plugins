---
name: handoff
description: Hand off the current work to another terminal (Claude Code conversation). From a coding session it prints a paste-ready block (text only). From a sessionless planning context it also writes a durable local resume file a fresh /session:start or /session:restore picks up — planning is the context that most needs to hand off (planning → coding).
---

# Session Handoff

Assemble the current work into the **standard handoff block** (Session Skill § Cross-Session Paste Handoff) so another terminal can continue it. `handoff` has **two forms**, chosen automatically by whether a coding session is active:

| Context | Primary output | Durable file? | Why |
|---------|----------------|---------------|-----|
| **Coding session** (a session file exists) | the paste block — text only | no | the human copies it into a live terminal elsewhere |
| **Sessionless / planning** (no session file) | a **durable local resume file** a fresh session picks up | **yes** | paste is friction and lost with the clipboard; planning → coding is the crossing that most needs to survive a restart (acp-ajudd#29) |

**The sessionless path is the point.** A planning stance is *deliberately* sessionless (Session Skill § Session Stance) — yet it is the context that most needs to hand off, because the only sanctioned planning→coding path is **handoff into a fresh coding session** (never in-place conversion — acp-ajudd#32). This command is that **cheap exit**: it captures the planning context into a file so starting the coding session costs one command and loses nothing that mattered. Before acp-ajudd#29 this command stopped cold with "no session" — the one context that should produce handoffs couldn't.

**This command drives both moving legs of the dispatch↔code loop.** When work is dispatched, the dispatch→code work order (leg 1) and the coding session's command-invoked return handoff (leg 3) are both `/session:handoff` calls — see Session Skill § **The dispatch↔code loop — deploy-then-validate** for the full round-trip (dispatch hands off with Done-whens → code implements and, in the happy path, self-verifies + **SHIPS by default** (the deploy) with **no HOLD**, then **reports a `State: IMPLEMENTED-DEPLOYED` block but does NOT self-close** — shipping is not closing, acp-ajudd#94 → dispatch confirms the working tree post-hoc, non-gating → dispatch **orders the close** (`SAFE-TO-CLOSE` / `Action: CLOSE`), and the still-open coding session runs `/session:finish`). Code stops mid-build **only** on the escape hatch (question / unclear / disagreement / found problem). A solo coding session with no dispatcher doesn't run the loop; this command is just its outbound handoff. **Inbox zones only** — work repos have no dispatch role.

Distinguish `handoff` from the file-based same-machine paths:

| Path | Mechanism | Crosses machines? |
|------|-----------|-------------------|
| `/session:inbox` | writes a capture into a target slug's `_inbox/` (one file per item) | no — same machine |
| `/session:spawn` | writes a `[spawn]` inbox item staging a linked session | no — same machine |
| **`/session:handoff`** | **prints a paste block (both forms) + writes a durable resume file (sessionless form)** | **paste block: yes, you carry it; resume file: no, same machine** |

Because a receiving session has none of this conversation, every handoff — block and file alike — must be **self-contained**. The Session Skill § **Cross-Session Paste Handoff** owns the block format; this command does not restate it.

**Receiving side — verify before acting (acp-ajudd#69).** This command *emits* handoffs. The mirror-image duty falls on whatever terminal a block is pasted **into**: before acting on a pasted handoff block, it must verify the note is **for it** — a hard `Slug` check against `pwd` (always), plus a `<to-role>` check when it already has an established role — and **STOP + flag** on a mismatch rather than blindly doing the work (a wrong-repo mispaste is otherwise acted on in the wrong repo). Every role's flow runs this on detecting a block. The rule + the two mismatch messages live in **Session Skill § Cross-Session Paste Handoff → Receiving side — verify the target before acting**; this command does not restate them.

## Instructions

### 1. Identify the Context — Coding Session or Sessionless

Run `pwd` and extract the repo slug (last path component). Resolve `session_root` and `handle` using Path Resolution (`references/path-resolution.md`).

Determine whether a **coding session** is active (same pattern as `commit`/`checkpoint`):
1. Look for the most recent "Resuming `<name>`" (from `session:start`) or "Switching to `<name>`" (from `session:switch`) line. Use whichever is most recent.
2. Fall back to reading `~/.claude/memory/sessions/<slug>/_active` if not in context.

**This command does NOT enforce a session (acp-ajudd#29).** Unlike `commit`/`checkpoint`/`store` (which stop cleanly with `No session established…`), `handoff` treats "no session" as a **valid mode**, not an error — it is the whole reason the command exists for planning. Branch:

- **A coding session is current** → **Coding-session path** (Step 2 → Step 4 → Step 5A). The block is text only, exactly as before.
- **No session** (sessionless / planning stance) → **Sessionless path** (Step 2 → Step 3 → Step 4 → Step 5B). Assemble the handoff from the conversation and the records this planning context produced, write a durable resume file (primary), and print the block (secondary).

### 2. Gather Handoff Context

Assemble what a *fresh* receiving session needs. State everything self-contained — never write "as we discussed above" or reference anything visible only in this conversation; the receiver reads it cold. Cap the body at what's genuinely needed.

**Coding-session path** — read `<session_root>/<name>.md` for the durable state (branch, open items, next steps, scope, related keys, loaded memories, recent commits), and combine it with what the conversation surfaced.

**Sessionless path** — there is no session file, so assemble from:
- the **conversation** — the task, the reasoning, what's decided vs. still open;
- the **work this planning context produced** — `work` entries it wrote/scoped for this slug (their `<acronym>-<handle>#<n>` IDs), Jira stories it created/refined, decisions and rejected options;
- the **exact next action** — the single concrete thing the coding session should do first.

Both paths collect the same shape:
- **What we're doing** — the task in one or two sentences, from scratch.
- **Key decisions** — choices made and options rejected (so the receiver doesn't relitigate them).
- **Exact next action** — the single concrete next step, not a vague direction.
- **Guardrails / do-NOTs** — constraints, out-of-scope areas, conventions.
- **Relevant paths / inbox IDs** — files to open, `<acronym>-<handle>#<n>` item IDs, story/CAB keys, branch name.

**Target label:** if the user passed an argument (`/session:handoff <target>`), use it verbatim for the `To:` line. Otherwise infer a short target from context (a slug, session name, or topic).

### 3. Write the Durable Resume File (sessionless path only)

**The file is the primary deliverable of the sessionless handoff (Aaron, acp-ajudd#29)** — paste is friction and lost if the clipboard is; a durable file survives a restart and a fresh terminal. This is the sessionless analog of `store`/`restore`: write a resume file that a later `/session:restore` picks up.

Reuse the **existing `_context_<name>.md` convention** so the file is discoverable with **no change to any other command** — bare `/session:restore` already lists `_context_*.md` files in the local session dir and loads the one you pick (see `commands/restore.md`; it degrades gracefully when there is no matching session file, which is exactly the sessionless case). Do **not** invent a new filename that nothing reads.

1. **Name it** `_context_planning-<topic-slug>.md`, where `<topic-slug>` is a short kebab-case slug of the target/topic (e.g. `_context_planning-session-stance-model.md`). The `planning-` prefix makes it self-describing in the restore list. Collision → append a disambiguator.
2. **Write it always to the local path** `~/.claude/memory/sessions/<slug>/_context_planning-<topic-slug>.md` — never in a repo, never migrated (identical rule to `store`: a resume point is a personal, ephemeral, local stash).
3. **Content** — mirror the `store` context-file structure (so `restore` displays it cleanly), framed as a planning handoff:
   ```markdown
   # Planning Resume — <topic>
   Generated: <YYYY-MM-DD HH:MM>   (sessionless planning handoff — no session file)

   ## Problem Being Solved Now
   <what this work is, one paragraph — self-contained>

   ## Decisions Made / Options Rejected
   - <decision> — **Why:** <reasoning>
   - <rejected option> — **Why not:** <reason>

   ## Work Produced This Planning Context
   - <acronym>-<handle>#<n> — <inbox entry summary + status>
   - <Jira key> — <story summary>   (work repos)

   ## Guardrails / Do-NOTs
   - <constraint / out-of-scope area / convention>

   ## Relevant Paths / IDs
   - <files, branch, story/CAB keys, inbox IDs>

   ## Exact Next Action
   <the single concrete first step for the coding session>
   ```
4. **Secrets & PII guard (BLOCKING — reuse `store` § 2a).** Before writing, scan the composed content for the same secrets/PII patterns `store`/`session-commit-guard.py` use (DB connection strings with passwords, `password=`/`token=`/`api_key=`, `AKIA…`, JWTs, private-key blocks, `fedTaxNum`/`ssn`/`taxId`, real-name↔custid pairings). Redact to a placeholder + pointer and report what was scrubbed. This is the file's only line of defense (local-only, never committed/migrated), so the scan is blocking — do not restate the procedure; follow `store.md` § 2a.

### 4. Emit the Handoff Block (both paths)

Print the block in the **standard handoff format** — the **Session Skill § Cross-Session Paste Handoff** owns the exact template and rules; this command does not restate them (single source of truth). The block is **role-aware** (`<role>` ∈ {refine/refinement, dispatch, coding} — § The three roles; the planning-side **handoff token** is written `PLANNING`, the canonical name for the refine/refinement role — SKILL § Cross-Session Paste Handoff). Determine this context's role first: a **session file present** → `coding`; **sessionless + dispatch role assumed** (via `/session:dispatch`, or a pasted briefing on another machine) → `dispatch`; **sessionless otherwise** → `refine` (its handoff token is `PLANNING`). Fill the provenance header from Steps 1–2:
- **Title** — names **both ends**, uppercased: `<FROM-ROLE> ──▶ <TO-ROLE> HANDOFF` (e.g. `CODING ──▶ DISPATCH HANDOFF`, `DISPATCH ──▶ CODING HANDOFF`, `DISPATCH ──▶ PLANNING HANDOFF`) — acp-ajudd#69. `<FROM-ROLE>` is this context's origin role and always matches the left side of the `──▶` provenance line (acp-ajudd#45); `<TO-ROLE>` is the destination and **is the routing instruction** that tells the human which terminal to paste into (load-bearing in the strict-hub topology — § The three roles). The SKILL § Cross-Session Paste Handoff owns the exact title wording; this command does not restate it.
- **`[YYYY-MM-DD HH:MM @handle] <from-role> (<from-name>) ──▶ <to-role> (<target>)`** — the origin is `coding (<session-name>)` on the coding path, or `dispatch (<slug>)` / `planning (<slug>)` (the refine/refinement role — canonical token `planning`) on the sessionless path (whichever role this context declared); `<target>` is the label from Step 2. **The `HH:MM` comes from a real `date` call run at emit time (e.g. `date +"%Y-%m-%d %H:%M"`) — never guessed** (acp-ajudd#82; the SKILL § owns the mechanism). The same stamp is echoed in the footer recap.
- **`Action:` / `State:`** — add **`Action:`** on an outbound note (the sender's intent: `PICK UP #X`, `FIX`, `VALIDATE`, `CLOSE`, `HALT`) or **`State:`** on a return note (what happened: `IMPLEMENTED-DEPLOYED`, `VALIDATED`, `FOUND-ISSUE`, `REQUIREMENTS-CHANGE`, `BLOCKED-QUESTION`, `HALTED`) — one or the other, never both. `HALT`/`HALTED` stand down dispatched work mid-flight (Session Skill § HALT — no publish, no commit, WIP preserved). Omit if this handoff is neither (a bare informational pass).
- **Close-signal** — on a **dispatch** validation/close note, fill the close-signal slot of the footer recap (`SAFE-TO-CLOSE` / `HOLD`) and voice it to the human via the fixed courier-line vocabulary (SKILL § Cross-Session Paste Handoff → The courier line — `SAFE-TO-CLOSE` maps to the `✅` line, `HOLD` to `⏸`). Other roles omit it.
- **`Re:`** = topic + any inbox IDs / story keys carried (omit the ID clause if none). **`Slug` / `Zone`** = current repo slug + session type. **Footer** = the **one-line state recap** (acp-ajudd#82): `END HANDOFF · [YYYY-MM-DD HH:MM @handle] · from ──▶ to · <ids> · <Action/State> · <return instruction> · <close-signal, dispatch legs only>` — one compressed scannable line echoing the header state so the last thing visible in the window orients the human without scrolling up. **When the return leg must come back as a block the return instruction must be command-invoking (acp-ajudd#43, generalized):** tell the receiver to *run `/session:handoff`* to reply with a handoff block — do not have it free-form the report. This applies to a **dispatch→code work order** (the return `State: IMPLEMENTED-DEPLOYED` / stop-reason must come back as a block). The SKILL § Cross-Session Paste Handoff owns the exact footer wording; this command does not restate it.

Then write the self-contained, paragraphed body (what we're doing · key decisions · exact next action · guardrails · relevant paths/IDs). **The note carries the *run*, not the *spec* — never regurgitate the picked-up inbox item's contents; the coding session reads the item itself. A dispatch→code work order is `code #X` plus process instructions (watch-fors, report-back protocol).** Apply the SKILL section's rules as written — fenced block mandatory, heavier outer fence if the body has its own ``` fences, rule-separated header/body/footer — do not re-explain them to the user.

Precede the block with the **courier line** — one bold action line, above the block, drawn from the fixed vocabulary (SKILL § Cross-Session Paste Handoff → The courier line; acp-ajudd#81 — no bespoke lead-in phrasings):
- **Coding-session path:**
  ```
  **▶ PASTE TO <TO-ROLE> — carry the block below to the <to-role> terminal**
  ```
- **Sessionless path:** name the resume file first, since it's the primary artifact, then the same courier line:
  ```
  Wrote planning resume → _context_planning-<topic-slug>.md
  Pick it up in a fresh session with:  /session:restore planning-<topic-slug>

  **▶ PASTE TO <TO-ROLE> — or carry the block below to a live <to-role> terminal elsewhere**
  ```

### 5. Finish — Touch Nothing Else

**Step 5A — Coding-session path.** `handoff` here **produces text only.** It writes no files, sends no messages, and does **not** touch `_active`, the session file, `_index.md`, `_history.md`, the inbox, or the worklog. The current session is completely unchanged. Delivery is the human's job (paste).

**Step 5B — Sessionless path.** `handoff` wrote **exactly one** artifact: the local `_context_planning-<topic-slug>.md` resume file (Step 3). It **sends nothing** (no Teams), and touches **no** `_active`, **no** session file, **no** `_index.md`, **no** `_history.md`, and does **not** consume or create inbox items. Writing a session file or `_active` here would be starting a coding session — which is exactly the in-place conversion acp-ajudd#32 forbids. The planning context stays planning; the coding session is born fresh when the human runs `/session:restore` (or `/session:start`).

If the user wants a *file-based* handoff on the same machine that stages actual work rather than a resume point, point them at `/session:spawn` (stage a linked session) or `/session:inbox` (drop an item/capture into a target inbox).
