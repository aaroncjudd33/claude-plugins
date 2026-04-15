---
name: aws
description: AWS SSO + CodeArtifact login. Run standalone to refresh credentials.
---

# Setup: AWS

Check SSO session status and log into CodeArtifact.

## Instructions

**Step 1 — Check if SSO is already active:**
```bash
aws sts get-caller-identity 2>/dev/null
```
- Succeeds → report "SSO session active." Parse `~/.aws/sso/cache/*.json` for expiry — warn if < 2 hours.
- Fails → run `aws sso login` (blocks until browser auth finishes).

**Step 2 — CodeArtifact logins (run both in parallel):**
```bash
aws --profile devops codeartifact login --tool dotnet --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```
```bash
aws --profile devops codeartifact login --tool npm --repository youngliving --domain yl --domain-owner 534914120180 --region us-west-2
```

**Output:**
```
AWS

  SSO: Active — expires in 11h 42m
  CodeArtifact (dotnet): Logged in
  CodeArtifact (npm): Logged in
```

If any step fails, report the error clearly and continue.
