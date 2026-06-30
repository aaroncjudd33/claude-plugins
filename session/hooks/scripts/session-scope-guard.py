#!/usr/bin/env python3
import json, sys, os, re


def normalize(path, home):
    p = path.strip()
    if p.startswith("~"):
        p = home + p[1:]
    p = p.replace("\\", "/")
    p = re.sub(r'^/([a-zA-Z])/', lambda m: m.group(1).lower() + ":/", p)
    return p.lower().rstrip("/")


def session_active(home, slug):
    active = os.path.join(home, ".claude", "memory", "sessions", slug, "_active")
    return os.path.exists(active)


def read_active_name(home, slug):
    """The session name recorded in the slug's _active marker, or None."""
    active = os.path.join(home, ".claude", "memory", "sessions", slug, "_active")
    try:
        with open(active, encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


def read_session_mode(home, slug, active_name):
    """Mode from the active session file's YAML frontmatter — never the body.

    Frontmatter only (terminated at the second '---') so the hook never has to
    parse untrusted freeform markdown. Returns:
      - None  → no usable session file (no active_name, or the file is missing /
                a stale _active marker). Caller blocks: 'no session = no edits'.
      - 'coding' (default) → file exists but has no frontmatter or no `mode:`
                key (back-compat with older session files), or frontmatter is
                malformed (fail-open on parse — never crash, never silently
                block everyone).
      - the literal mode otherwise ('planning' / 'coding' / 'both').
    """
    if not active_name:
        return None
    path = os.path.join(home, ".claude", "memory", "sessions", slug, active_name + ".md")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return None  # stale _active — marker points at a file that isn't there
    if not text.startswith("---"):
        return "coding"  # no frontmatter block — back-compat default
    end = text.find("\n---", 3)
    if end == -1:
        return "coding"  # unterminated frontmatter — fail-open
    for line in text[3:end].splitlines():
        m = re.match(r'\s*mode\s*:\s*(\S+)', line)
        if m:
            return m.group(1).strip().lower()
    return "coding"  # frontmatter present, no mode key — default


def enforce_mode_zone(home, slug, fp, zone_label, inbox_hint):
    """Always-on, mode-aware gate for item-driven zones (plugin marketplace and
    personal projects). Edit/Write requires an active session in coding/both
    mode. Exits the process (2 = block, 0 = allow). Never returns."""
    if not session_active(home, slug):
        print(
            f"BLOCKED: '{fp}' is in {zone_label}, but no session is active for '{slug}'.\n"
            f"Editing here requires an active coding session. Read/search are always free.\n"
            f"Start one: /session:start — pick up or describe an inbox item.\n"
            f"Inbox: {inbox_hint}"
        )
        sys.exit(2)
    active_name = read_active_name(home, slug)
    mode = read_session_mode(home, slug, active_name)
    if mode is None:
        print(
            f"BLOCKED: '{fp}' — the active marker for '{slug}' points to "
            f"'{active_name or '(empty)'}', but no session file exists for it.\n"
            f"The session may have been deleted or renamed. Run /session:start to "
            f"pick up or create one."
        )
        sys.exit(2)
    if mode == "planning":
        print(
            f"BLOCKED: '{fp}' — the active session '{active_name}' is in planning mode "
            f"(read-only).\n"
            f"Planning sessions don't edit code. Switch to coding: re-run /session:start "
            f"and reply 'coding', or set 'mode: coding' in the session frontmatter, then retry."
        )
        sys.exit(2)
    sys.exit(0)  # coding / both / default → allow


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    fp = d.get("tool_input", {}).get("file_path", "")
    if not fp:
        sys.exit(0)

    home = os.path.expanduser("~")
    fp_norm = normalize(fp, home)

    # Always allow memory, scripts, cache — these are session/tool infrastructure.
    # Critically, session files themselves live under ~/.claude/memory/, so
    # creating a session is never chicken-and-egg blocked by the gate below.
    always_allow = [
        normalize("~/.claude/memory/", home),
        normalize("~/.claude/projects/", home),   # project memory tier — never gated
        normalize("~/.claude/scripts/", home),
        normalize("~/.claude/plugins/cache/", home),
    ]
    for prefix in always_allow:
        if fp_norm.startswith(prefix):
            sys.exit(0)

    # Read user-config for portable path definitions
    config_path = os.path.join(home, ".claude", "plugins", "user-config.json")
    try:
        with open(config_path) as f:
            config = json.load(f)
    except Exception:
        sys.exit(0)

    paths = config.get("paths", {})
    marketplace_name = paths.get("pluginMarketplaceName", "")
    work_repos_dir = paths.get("workReposDir", "")
    personal_dir = paths.get("personalProjectsDir", "")

    # ── Item-driven zones: plugin marketplace + personal projects ──
    # ALWAYS-ON and mode-aware, NOT behind sessionGate.enforce. For these zones
    # the "you must have a coding session to edit" rule is the whole point — an
    # opt-in flag defaulting off would silently neuter it. Plugin and personal
    # behave identically: same enforce_mode_zone() path, different slug source.

    # Plugin marketplace zone — one repo, slug = marketplace_name.
    if marketplace_name:
        marketplace_path = normalize(f"~/.claude/plugins/marketplaces/{marketplace_name}/", home)
        if fp_norm.startswith(marketplace_path):
            enforce_mode_zone(
                home, marketplace_name, fp, "the plugin marketplace",
                f"~/.claude/memory/sessions/{marketplace_name}/_inbox.md",
            )

    # Personal projects zone — each project is its own repo/slug under personal_dir.
    if personal_dir:
        personal_norm = normalize(personal_dir, home)
        if fp_norm.startswith(personal_norm + "/"):
            relative = fp_norm[len(personal_norm):].lstrip("/")
            slug = relative.split("/")[0] if relative else ""
            if slug:
                enforce_mode_zone(
                    home, slug, fp, f"personal project '{slug}'",
                    f"~/.claude/memory/sessions/{slug}/_inbox.md",
                )
            sys.exit(0)

    # ── Opt-in zone: work repos (story/cab) ──
    # Unchanged behavior — existence-only check, gated behind sessionGate.enforce
    # (defaults off). Story/cab work has an external system of record (Jira/CAB)
    # and keeps today's instruction-only Mode handling.
    if not config.get("sessionGate", {}).get("enforce", False):
        sys.exit(0)

    if work_repos_dir:
        work_norm = normalize(work_repos_dir, home)
        if fp_norm.startswith(work_norm + "/"):
            relative = fp_norm[len(work_norm):].lstrip("/")
            slug = relative.split("/")[0] if relative else ""
            if slug and not session_active(home, slug):
                print(
                    f"BLOCKED: '{fp}' is in work repo '{slug}' but no active session exists.\n"
                    f"Run /session:start in the '{slug}' project directory."
                )
                sys.exit(2)
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
