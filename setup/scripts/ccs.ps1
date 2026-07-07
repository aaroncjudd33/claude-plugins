# >>> ccs launcher (managed by /setup:onboarding - do not edit between markers) >>>
# `ccs` - cd into a repo and launch Claude Code in one step.
#   ccs            -> launch Claude in the current directory
#   ccs <acronym>  -> cd into the mapped repo, then launch Claude
#   ccs <prefix>   -> no exact acronym? match repo folders in the base dir by starts-with
# The repos base dir + marketplace name are baked in at install time from
# ~/.claude/plugins/user-config.json (paths.workReposDir / paths.pluginMarketplaceName).
function ccs {
    param([string]$target = "")

    $reposBase  = '__CCS_REPOS_BASE__'
    $pluginsDir = "$env:USERPROFILE\.claude\plugins\marketplaces\__CCS_MARKETPLACE__"

    if ([string]::IsNullOrEmpty($target)) { claude; return }

    $map = [ordered]@{
        'plugins' = $pluginsDir
        'bls'     = "$reposBase\bwp-lead-service"
        'cp'      = "$reposBase\commission-payments"
        'cs'      = "$reposBase\contest-service"
        'dl'      = "$reposBase\digital-library"
        'dmp'     = "$reposBase\dml-migrations-ylprd"
        'dmv'     = "$reposBase\dml-migrations-ylvoprd"
        'dr'      = "$reposBase\downline-reports"
        'e2o'     = "$reposBase\e2-open-integration"
        'glb'     = "$reposBase\gen-leadership-bonus"
        'mmc'     = "$reposBase\mass-marketing-consent"
        'ois'     = "$reposBase\openid-server"
        'pvf'     = "$reposBase\pedigree-vo-form"
        'ts'      = "$reposBase\terraform-security"
        'vo'      = "$reposBase\virtual-office"
        'voi'     = "$reposBase\virtual-office-integration"
        'vot'     = "$reposBase\virtual-office-tools"
        'voe'     = "$reposBase\vo-enrollment"
        'vpt'     = "$reposBase\vo-playwright-tests"
    }

    $dir = $null
    if ($map.Contains($target)) {
        $dir = $map[$target]
    }
    else {
        # No exact match - try starts-with against the repos in the base dir
        if ([string]::IsNullOrEmpty($reposBase) -or -not (Test-Path $reposBase)) {
            Write-Host "ccs: no repos base dir configured - set paths.workReposDir via /setup:onboarding"
            return
        }
        $hits = @(Get-ChildItem -Path $reposBase -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "$target*" })
        if ($hits.Count -eq 1) {
            $dir = $hits[0].FullName
        }
        elseif ($hits.Count -gt 1) {
            Write-Host "ccs: ambiguous match for '$target':"
            $hits | ForEach-Object { Write-Host "  $($_.Name)" }
            return
        }
        else {
            Write-Host "ccs: no match for '$target'"
            return
        }
    }

    Set-Location $dir
    claude
}
# <<< ccs launcher <<<
