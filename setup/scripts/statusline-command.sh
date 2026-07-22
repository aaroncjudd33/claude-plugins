#!/usr/bin/env bash
# Claude Code status line script
# Displays: user@host  dir  branch  model  context%

input=$(cat)

cwd=$(echo "$input" | jq -r '.cwd // empty')
dir=$(basename "${cwd:-$(pwd)}")

model=$(echo "$input" | jq -r '.model.display_name // empty')

branch=$(echo "$input" | jq -r '.workspace | if .git_worktree then .git_worktree else empty end // empty')
if [ -z "$branch" ]; then
  branch=$(git -C "${cwd:-.}" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null || true)
fi

used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# --- Close-safety light (acp-ajudd#97, sentinel redesign acp-ajudd#157) ------
# Answers "can I close this terminal, and in what sense?" for the human. Signal
# source is a checkpoint-currency sentinel, NOT git working-tree state (git-dirty
# != "un-checkpointed" -- plugin sessions commit locally only, and lite/sessionless
# work has no git-tracked session file to be dirty at all):
#   sentinel present      -> stop  (unsaved; reasoning not yet checkpointed)
#   sentinel absent       -> safe  (checkpointed; pausable, resume later)
#   session 'completed'   -> done  (finished & validated after /session:finish)
# One glyph vocabulary, shared with the SKILL reply-footer cue (session SKILL.md,
# "The close-safety cue") and the Response Tiers Tier 4 icon (global CLAUDE.md).
# Sessionless roles (planning / capture / dispatch) have no active pointer, so no
# save-state light -- exactly the dispatch carve-out.
# Fail-open: any miss leaves the light empty and never breaks the status line.
safety=""
gitroot=$(git -C "${cwd:-.}" --no-optional-locks rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$gitroot" ]; then
  slug=$(basename "$gitroot")
  active_base=""
  active_name=""
  # active pointer: local memory tier first, then repo tier (post-migrate)
  for base in "$HOME/.claude/memory/sessions/$slug" "$gitroot/.claude/sessions"; do
    if [ -f "$base/_active" ]; then
      name=$(head -n1 "$base/_active" 2>/dev/null | tr -d '\r\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      if [ -n "$name" ]; then
        active_base="$base"
        active_name="$name"
        break
      fi
    fi
  done
  if [ -n "$active_base" ]; then
    st=""
    case "$active_name" in
      lite:*) : ;;  # lite/sessionless work -- no session file, no 'completed' state to read here
      *)
        active_file="$active_base/$active_name.md"
        if [ -f "$active_file" ]; then
          # status: frontmatter `status:` first, then the `- **Status:**` body bullet
          st=$(sed -n 's/^status:[[:space:]]*//p' "$active_file" 2>/dev/null | head -n1 | tr -d '\r' | tr '[:upper:]' '[:lower:]')
          if [ -z "$st" ]; then
            st=$(sed -n 's/.*\*\*Status:\*\*[[:space:]]*//p' "$active_file" 2>/dev/null | head -n1 | tr -d '\r' | tr '[:upper:]' '[:lower:]')
          fi
        fi
        ;;
    esac
    case "$st" in
      *completed*) safety=$'\033[93m\xf0\x9f\x8f\x86 done\033[0m' ;;   # gold trophy
      *)
        if [ -f "$active_base/_active.dirty" ]; then
          safety=$'\033[91m\xf0\x9f\x9b\x91 unsaved\033[0m'          # red stop
        else
          safety=$'\033[92m\xe2\x9c\x85 safe\033[0m'                 # green check
        fi
        ;;
    esac
  fi
fi

# Build status parts
parts=""

# user@host  dir
parts="$(whoami)@$(hostname -s)  ${dir}"

# branch
if [ -n "$branch" ] && [ "$branch" != "HEAD" ]; then
  parts="${parts}  ${branch}"
fi

# model
if [ -n "$model" ]; then
  parts="${parts}  ${model}"
fi

# context usage
if [ -n "$used" ]; then
  printf_used=$(printf "%.0f" "$used")
  parts="${parts}  ctx:${printf_used}%"
fi

# Close-safety light leads, so a human round-robining windows catches it first
if [ -n "$safety" ]; then
  printf "%s  %s" "$safety" "$parts"
else
  printf "%s" "$parts"
fi
