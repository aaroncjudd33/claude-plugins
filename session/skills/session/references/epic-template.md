# Epic Memory Template

Use this as the structural reference when creating a new epic memory file at
`~/.claude/memory/epics/<epic-key>.md`.

---

```markdown
---
updated: YYYY-MM-DD
epic: BPT2-XXXX
title: <Epic Title from Jira>
---

# Epic Memory — BPT2-XXXX
# <Epic Title>

> **Purpose:** Single source of truth for cross-story decisions, implementation details,
> and open questions. Any session working on a story in this epic should read this file
> at start and update it when decisions land or stories ship.
> Detail lives in individual session files. This captures only what crosses story boundaries.

---

## For Developers

<One paragraph describing what this epic is building and why. Write it for a developer
picking up a story cold — what context do they need before writing any code?>

**If you're picking up a story in this epic:**
- Read the Implementation Reference section below before writing any code
- The Architecture Decisions section captures the *why* behind choices already made
- Open Questions and Blockers flag what's still unresolved
- For deeper context reach out to <owner> (<email>) — they have Claude session context
  that goes further than what's written here

---

## Story Map

| Story | Title | Scope | Status | Owner |
|-------|-------|-------|--------|-------|
| BPT2-XXXX | <title> | <service/repo> | <status> | <owner> |

---

## Implementation Reference

### Key Files
<!-- List the most important files a developer would need to know about -->
- `<path>` — <what it does>

### API Contract
<!-- Endpoints, request/response shape, notable quirks -->

### Data Model
<!-- DynamoDB tables, Oracle tables/columns, key fields and their meaning -->

### VO / Frontend
<!-- Angular components, feature flags, key files -->

---

## Architecture Decisions

<!-- One ### block per decision. Keep only decisions that cross story boundaries —
     story-specific decisions live in the story's session file. -->

### [DECIDED] <Decision Title>
<What was decided and why. What alternatives were considered and why they were rejected.>
- **Decision:** <the chosen approach>
- **Rationale:** <why>
- **Source:** <session-name> <YYYY-MM-DD>

---

## Blockers

<!-- Active blockers only. Remove when resolved. -->
| # | Description | Owner | Status |
|---|-------------|-------|--------|
| 1 | <blocker> | <owner> | 🔴 Critical / 🟡 Watch |

---

## Open Questions

<!-- Questions that need answers before or during implementation. -->
| # | Question | Asked by | Status |
|---|----------|----------|--------|
| 1 | <question> | <session-name> | Open |

---

## Resolved

<!-- Move items here from Blockers/Open Questions when resolved. -->
| Type | Description | Resolution | Date |
|------|-------------|------------|------|
| Question | <question> | <answer> | YYYY-MM-DD |
| Blocker | <blocker> | <how resolved> | YYYY-MM-DD |
```
