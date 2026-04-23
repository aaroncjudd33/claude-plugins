# Jira Workflow Rules

## Ready For Test — Clear the Assignee

When transitioning a story to "Ready For Test", clear the assignee (set to null). Do not re-assign to the developer or anyone else.

**Why:** QA picks up unassigned stories from the Ready For Test column. An assigned story implies ownership and can cause QA to skip it or wait.

**How:** After any transition to Ready For Test, do not follow up by setting an assignee. If the transition itself clears the assignee, that is the correct behavior — don't "fix" it by re-assigning.
