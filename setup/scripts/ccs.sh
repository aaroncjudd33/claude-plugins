# >>> ccs launcher (managed by /setup:onboarding - do not edit between markers) >>>
# `ccs` - cd into a repo and launch Claude Code in one step.
#   ccs            -> launch Claude in the current directory
#   ccs <acronym>  -> cd into the mapped repo, then launch Claude
#   ccs <prefix>   -> no exact acronym? match repo folders in the base dir by starts-with
# The repos base dir + marketplace name are baked in at install time from
# ~/.claude/plugins/user-config.json (paths.workReposDir / paths.pluginMarketplaceName).
ccs() {
  local repos_base="__CCS_REPOS_BASE__"
  local plugins_dir="$HOME/.claude/plugins/marketplaces/__CCS_MARKETPLACE__"
  local arg="${1:-}"
  local target=""

  # No argument - launch in the current directory
  if [[ -z "$arg" ]]; then
    claude
    return
  fi

  # Exact acronyms / aliases (folder names are joined to the base dir)
  case "$arg" in
    plugins) target="$plugins_dir" ;;
    bls)     target="$repos_base/bwp-lead-service" ;;
    cp)      target="$repos_base/commission-payments" ;;
    cs)      target="$repos_base/contest-service" ;;
    dl)      target="$repos_base/digital-library" ;;
    dmp)     target="$repos_base/dml-migrations-ylprd" ;;
    dmv)     target="$repos_base/dml-migrations-ylvoprd" ;;
    dr)      target="$repos_base/downline-reports" ;;
    e2o)     target="$repos_base/e2-open-integration" ;;
    glb)     target="$repos_base/gen-leadership-bonus" ;;
    mmc)     target="$repos_base/mass-marketing-consent" ;;
    ois)     target="$repos_base/openid-server" ;;
    pvf)     target="$repos_base/pedigree-vo-form" ;;
    ts)      target="$repos_base/terraform-security" ;;
    vo)      target="$repos_base/virtual-office" ;;
    voi)     target="$repos_base/virtual-office-integration" ;;
    vot)     target="$repos_base/virtual-office-tools" ;;
    voe)     target="$repos_base/vo-enrollment" ;;
    vpt)     target="$repos_base/vo-playwright-tests" ;;
  esac

  # No exact match - try starts-with against the repos in the base dir
  if [[ -z "$target" ]]; then
    if [[ -z "$repos_base" || ! -d "$repos_base" ]]; then
      echo "ccs: no repos base dir configured - set paths.workReposDir via /setup:onboarding"
      return 1
    fi
    local matches=()
    for dir in "$repos_base"/*/; do
      local name
      name=$(basename "$dir")
      if [[ "$name" == "$arg"* ]]; then
        matches+=("$dir")
      fi
    done

    if [[ ${#matches[@]} -eq 1 ]]; then
      target="${matches[0]}"
    elif [[ ${#matches[@]} -gt 1 ]]; then
      echo "ccs: ambiguous match for '$arg':"
      for m in "${matches[@]}"; do
        echo "  $(basename "$m")"
      done
      return 1
    else
      echo "ccs: no match for '$arg'"
      return 1
    fi
  fi

  cd "$target" && claude
}
# <<< ccs launcher <<<
