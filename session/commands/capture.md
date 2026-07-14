---
name: capture
description: Assume the capture role — a sessionless ideation window upstream of refine. Bank a raw idea fast, optionally peek at the repo for a one-line viability sniff, and write a `capture`-type inbox entry (or drop it). Never scopes, never designs, never codes. Creates no session file. Inbox zones only (plugin / personal).
argument-hint: "[optional: the idea to bank]"
---

# Session Capture

Assume the **capture role** (Session Skill § The three roles — *the ideation station upstream of the three roles*). Capture is the **head of the pipe** — `capture ─▶ refine ─▶ dispatch ─▶ code`. It exists to remove the last multi-window bottleneck: **banking a new idea should never force you to interrupt whatever window is busy.** `refine` is full planning (explores, scopes, produces `refining`/`ready` work) — too heavy for "jot this for later." Capture is a free-sitting window you fire ideas at anytime, and its **only** durable output is a `capture`-type inbox entry the `refine` window later drains. It is **sessionless** — like `refine` and `dispatch`, it creates **no session file** and never touches `_active`.

> **Vocabulary:** `capture`, `refine`, `dispatch`, `work`, and the capture disposition are *defined* in the Session Skill § Terminology glossary (acp-ajudd#70); this command owns the capture **mechanics** below. The read-flow for captures once written lives in `references/inbox-convention.md` § Captures inbound (acp-ajudd#10).

This command gives capture a **first-class start** — same shape as `/session:dispatch`. Invoking `/session:capture` **is** the "told" that determines the role: the command declares the context as capture, loads the discipline, and stands ready for ideas.

## Scope — inbox zones only (plugin / personal)

Capture exists only where there is a **local inbox to write captures into**. In **work / general** repos there is no capture layer — work is scoped in Jira (`refine` → *Gathering Requirements*), and a stray idea leaves via a `/session:inbox` capture aimed at a repo that *does* have a system of record. This command is therefore **advertised only in plugin/personal** (Session Skill § The three roles; `commands/start.md`). It stays **invocable** in any zone for the deliberate case, but in work/general it will tell you the model doesn't apply and stop.

## The load-bearing boundary — triage vs. spec (NOT read vs. no-read)

Capture and refine are separated by **output and commitment, not tool access** — both may read the repo:

- **Capture answers "is this worth planning's time?"** — a viability gate. It **MAY read/search the code** to answer that, so planning's hopper isn't flooded with non-viable ideas.
- **Refine answers "here's exactly what to build."** — a scoped spec.

The peek earns its keep: the viability note is an **artifact** — when `refine` later picks the capture up, it starts **pre-warmed** ("capture already sniffed this: feasible, ~medium, touches `inbox-id.py`") instead of cold.

## Key properties

- **Capture MAY:** read/search code, assess rough difficulty and cost-benefit, give a **one-line** viability verdict.
- **Capture MUST NOT:** edit or write code · produce a design or scoped spec (acceptance criteria, approaches, file-by-file plans) · set any status past `capture` · "start refining." **The hard rule mirrors "refine never offers to code" — here it is "capture never refines."**
- **Capture emits NO handoff blocks.** It sits **outside** the planning↔dispatch↔coding paste-handoff relay (§ Cross-Session Paste Handoff). Its only output is a `capture`-type inbox entry (file-based) — never a `PLANNING ──▶ …` / `CODING ──▶ …` note.
- **Two exits, only:**
  1. **Write a `capture`-type entry** — the raw idea (body ~verbatim) plus a **one-line viability note**.
  2. **Drop it** — talked out of it after a peek; nothing written. **A cheap death is a *win*, not a waste** — filtering a non-viable idea before it reaches planning is the point.
- **Depth guard — the peek is a viability *sniff*, not a design pass.** Time-box it. If "is this viable?" starts turning into a deep read, note **"worth a proper look"** and **STOP** — deep scoping is refine's job. The hard cap is on **output**: capture emits a *note or nothing*, never a spec. The moment it starts emitting acceptance criteria or approaches, the window has silently become a second planner and the station's purpose dissolves.
- **Sessionless — creates no session file, no `_active` change.** A coding session already active stays active alongside this capture context, unaffected. Concurrency-safe as a 4th window because the atomic ID mint already landed (acp-ajudd#31 atomic mint, #66 self-heal); capture only **appends new items** — it never forks or mutates an in-flight entry (consumed = frozen holds).

## Instructions

### 1. Resolve and Check Zone

Run `pwd`, extract the repo slug (last path component). Read `handle` per the Session Skill's handle lookup. Read `~/.claude/plugins/user-config.json` → `paths` and classify the zone (same logic as `session:start` / `dispatch` / `refine`):

| Zone | Detection | Capture applies? |
|------|-----------|------------------|
| **plugin** | pwd contains `pluginMarketplaceName` | **yes** |
| **personal** | pwd begins with `personalProjectsDir` (fallback: `/c/claude/`) | **yes** |
| **work repo (story/cab)** | pwd begins with `workReposDir` (fallback: `/dev/`) | no — Jira flow, no local inbox |
| **general** | anything else | no — no system of record |

**If the zone is work or general**, state plainly and stop — do not write anything:
```
This is a <work/general> repo — the capture model doesn't apply here (no local inbox to
write into). To bank an idea for a plugin/personal repo, drop a /session:inbox capture at
that repo's inbox.
```
Only proceed to Step 2 for plugin/personal.

### 2. Declare the Role and Load the Discipline

State the role explicitly so the context is unambiguous:

```
Capture role assumed for <slug> (sessionless — no session file).
Operating under: triage-not-spec · MAY peek for a one-line viability sniff · note-or-nothing
(never a spec) · depth-guarded (deep read → "worth a proper look" + STOP) · never refines,
never codes, emits no handoff blocks.
```

The authoritative discipline is the Session Skill § The three roles (*the ideation station upstream of the three roles*) and § Captures Inbound. Then stand ready: invite the idea (`What do you want to bank?`) unless one was already passed as the argument.

### 3. For Each Idea — Sniff, then Take One of the Two Exits

For every idea the user fires:

1. **Optional viability peek.** If it helps answer *"is this worth planning's time?"*, read/search the repo — but keep it a **sniff**: rough feasibility, rough size, roughly where it lands. Honor the **depth guard** — if it's turning into a design pass, stop and let the note say "worth a proper look."
2. **Decide the exit:**
   - **Drop it** — if the peek talked you (or the user) out of it, write nothing and say so: `Dropped — <one-line why>. (nothing written)`. This is a good outcome.
   - **Write a `capture`-type entry** — otherwise, bank it (Step 4).

Do **not** design, scope, or produce acceptance criteria — that is refine's job. If the user starts asking you to scope it, say plainly: `That's a refine pass — I'll bank it as a capture and refine can scope it.`

### 4. Write the Capture Entry (exit 1)

**Mint a stable ID atomically** (never hand-write the header — acp-ajudd#66):
```bash
python3 "<session>/scripts/inbox-id.py" next --slug <slug> --handle <handle>
# on a box without python3, use: python
```
Then **append** a self-contained `capture`-type entry to `~/.claude/memory/sessions/<slug>/_inbox.md` (create with header `# Inbox — <slug>` if missing). Use the exact `_inbox.md` header format, the `> [type: capture]` line (no `status` — captures have no lifecycle), the raw idea ~verbatim, and the **one-line viability note**. The provenance surrogate is the command itself (there is no originating session): `from <slug> / capture (<zone>)`:

```markdown
## <id> · [YYYY-MM-DD @<handle>] from <slug> / capture (<zone>) — <Summary>
> [type: capture]

**Idea (<user>, verbatim-ish):** <the raw idea, kept close to how it was said>

**Viability note (capture sniff):** <ONE line — feasible? rough size? roughly where it lands; or "worth a proper look" if the depth guard tripped>

**Provenance:** captured YYYY-MM-DD by the `capture` terminal on <user>'s idea. <what you peeked at, then stopped>. ID <id> via the self-healing minter.
```

**Free rein, but never silent (acp-ajudd#5).** Writing a capture is not gated by any propose→approve step. The one rule is **visibility** — the instant you write it, surface a **one-line receipt** leading with the `<id>`:
```
Captured <id>: <one-line summary>
```
Then **wait for the next idea** — capture is a long-sitting window you keep firing at.

### 5. Done — Touch Nothing Else

Capture is sessionless and single-purpose: it wrote **no** session file, changed **no** `_active`, and touched **no** existing inbox entry (consumed = frozen; item-immutability hold — § State-Exclusivity). Everything it produced is new `> [type: capture]` entries awaiting disposition. Those drain forward: the **`refine` window surfaces "N captures waiting"** and promotes the viable ones to `work` (`references/inbox-convention.md` § Captures inbound; `commands/refine.md`). Capture never disposition its own entries — writing and draining are different stations.
