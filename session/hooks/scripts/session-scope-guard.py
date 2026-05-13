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

    # Always allow memory, scripts, cache — these are session/tool infrastructure
    always_allow = [
        normalize("~/.claude/memory/", home),
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

    # Plugin marketplace zone
    if marketplace_name:
        marketplace_path = normalize(f"~/.claude/plugins/marketplaces/{marketplace_name}/", home)
        if fp_norm.startswith(marketplace_path):
            if not session_active(home, marketplace_name):
                print(
                    f"BLOCKED: '{fp}' is in the plugin marketplace but no plugin session is active.\n"
                    f"Run /session:start or inbox this work: "
                    f"~/.claude/memory/sessions/{marketplace_name}/_inbox.md"
                )
                sys.exit(2)
            sys.exit(0)

    # Work repos zone
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

    # Personal projects zone
    if personal_dir:
        personal_norm = normalize(personal_dir, home)
        if fp_norm.startswith(personal_norm + "/"):
            relative = fp_norm[len(personal_norm):].lstrip("/")
            slug = relative.split("/")[0] if relative else ""
            if slug and not session_active(home, slug):
                print(
                    f"BLOCKED: '{fp}' is in personal project '{slug}' but no active session exists.\n"
                    f"Run /session:start in the '{slug}' project directory."
                )
                sys.exit(2)
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
