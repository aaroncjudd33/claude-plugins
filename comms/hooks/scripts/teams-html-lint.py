#!/usr/bin/env python3
"""Teams HTML lint — PreToolUse gate shipped WITH the comms plugin.

Blocks Teams message WRITES whose HTML violates the Teams formatting guide, so a
cramped/dark-mode-broken message can never reach a chat. It ships inside the
plugin (auto-discovered via hooks/hooks.json — no ~/.claude/settings.json edit
required) which means:
  * it is active only when the comms plugin is enabled (never penalizes non-users),
  * it is portable to any teammate's machine on `claude plugin install comms`,
  * it versions and uninstalls with the plugin instead of rotting in loose config.

SINGLE SOURCE OF TRUTH: skills/comms/references/teams-html-guide.md
  Keep FORBIDDEN and the spacer rule below in step with that guide's Quick Rules
  (no <pre>/<code>/<h1>/<h3>/<hr>/<th>; <p>&nbsp;</p> spacers between elements).
  Guide synced: 2026-07-02.

SCOPE
  Teams WRITES only:
    - send_chat_message
    - execute_action  (only when the payload is a teams/channel operation)
  NOT email (send_email — email HTML follows different norms), NOT reads
  (list_chats / list_chat_messages / search_teams_messages are never touched —
  the matcher doesn't route them here, and this script also no-ops on them).

NAMESPACE ROBUSTNESS
  Routing keys on the tool-name SUFFIX (after the final "__"), never on a
  hardcoded MCP namespace. When yl-msoffice was rehosted the tool ids changed
  from  mcp__claude_ai_yl-msoffice__send_chat_message  to
        mcp__plugin_yl-msoffice_yl-msoffice__send_chat_message
  and the old settings.json matcher silently stopped firing. Suffix routing here
  (plus a suffix-based matcher in hooks.json) survives that class of rename.

FAIL-OPEN: any parse error exits 0. A lint bug must never wedge messaging.
"""
import json
import sys

# Forbidden tag prefixes (substring match) → human-readable reason. Mirrors the
# guide's "What to Avoid" table / Quick Rules 1, 2, 7.
# Printed strings stay ASCII-only: under the Windows `python` fallback stdout can
# be cp1252, and a non-ASCII char (em-dash) would raise UnicodeEncodeError and
# crash the hook instead of blocking cleanly. Use " - " not "—".
FORBIDDEN = [
    ("<pre", "<pre> (solid dark background - unreadable in dark mode; use nested <ul>)"),
    ("<code", "<code> (dark inline background - clashes in dark mode; use plain text or <b>)"),
    ("<h1", "<h1> (too large for chat - use <h2> for section headers)"),
    ("<h3", "<h3> (renders at/below body-text size, no hierarchy - use <h2>)"),
    ("<hr", "<hr> (visible horizontal line + extra spacing - use a <p>&nbsp;</p> spacer)"),
    ("<th", "<th> (dark bold header cells - use <td> with <b> inside)"),
]


def lint(body):
    """Return a list of guide violations found in an HTML message body."""
    errs = [reason for tag, reason in FORBIDDEN if tag in body]
    # Spacing — universal rule: 3+ paragraphs with no spacer collapses into a
    # wall of text. Matches the original settings.json heuristic exactly.
    if body.count("</p>") >= 3 and "<p>&nbsp;</p>" not in body:
        errs.append(
            "missing <p>&nbsp;</p> spacers between paragraphs - Teams collapses "
            "multi-paragraph messages into a wall of text"
        )
    return errs


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail-open — never wedge messaging on a parse error

    tool = payload.get("tool_name", "") or ""
    tool_input = payload.get("tool_input", {}) or {}
    suffix = tool.rsplit("__", 1)[-1] if tool else ""

    if suffix == "send_chat_message":
        body = tool_input.get("body", "") or tool_input.get("message", "")
        label = "Teams message"
    elif suffix == "execute_action":
        raw = json.dumps(tool_input)
        low = raw.lower()
        # execute_action is a generic dispatcher — only lint teams/channel sends.
        if "teams" not in low and "channel" not in low:
            sys.exit(0)
        body = raw
        label = "Teams execute_action"
    else:
        # send_email and anything else — not Teams HTML, not linted.
        sys.exit(0)

    errs = lint(body)
    if errs:
        # Block via the documented PreToolUse JSON contract (stdout + exit 0),
        # NOT exit-2+stderr: on this Claude Code version an exit-2 hook is framed
        # as a generic "hook error" and its stderr reason is not surfaced to the
        # assistant ("No stderr output"). permissionDecision=deny both blocks the
        # call AND feeds permissionDecisionReason back so the HTML can be fixed.
        reason = (
            "BLOCKED: " + label + " failed the Teams HTML guide "
            "(comms/skills/comms/references/teams-html-guide.md). Fix: "
            + "; ".join(errs)
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
