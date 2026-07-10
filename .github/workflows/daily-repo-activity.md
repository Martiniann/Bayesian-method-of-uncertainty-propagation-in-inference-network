---
emoji: 📊
name: Daily Repository Activity Report
description: Generates a daily digest of repository activity (commits, PRs, issues, releases) and posts it as a GitHub issue.
on:
  schedule: "0 8 * * *"
  workflow_dispatch:
permissions:
  contents: read
  issues: read
  pull-requests: read
strict: true
tools:
  github:
    mode: gh-proxy
    toolsets: [default]
safe-outputs:
  mentions: false
  allowed-github-references: []
  max-bot-mentions: 1
  create-issue:
    title-prefix: "Daily Activity:"
    labels: [report]
    close-older-issues: true
    expires: 7
---

# Daily Repository Activity Report

## Context

- Repository: `${{ github.repository }}`
- Workflow run: `${{ github.run_id }}`
- Report window: **last 24 full hours ending at workflow start (UTC)**

## Task

You are an activity digest agent. Generate a structured daily report of all repository activity in the last 24 hours and deliver it as a GitHub issue.

### Step 1 — Determine the reporting window

Calculate the exact start and end timestamps (UTC ISO 8601) for the last 24 full hours ending at the current workflow start time. Use these timestamps consistently throughout all queries.

### Step 2 — Collect activity data

Use `gh` commands to query the last 24 hours of activity. Collect all of the following:

1. **Commits** pushed to the default branch (`gh api /repos/{owner}/{repo}/commits?since=<start>&until=<end>`)
2. **Pull requests** created or updated (`gh pr list --state all --json number,title,state,author,createdAt,updatedAt,url`)
3. **Issues** created or updated (`gh issue list --state all --json number,title,state,author,createdAt,updatedAt,url`)
4. **Releases** published (`gh release list --json tagName,name,createdAt,url`)
5. **Workflow runs** started (`gh run list --json databaseId,name,status,conclusion,createdAt,url --limit 50`)

Filter each list to only include items whose `createdAt` or `updatedAt` falls within the 24-hour window.

### Step 3 — Evaluate and report

If **all five categories** are empty (zero events in the window), call `noop` with the message:
`"No repository activity in the last 24 hours (<window_start_utc> to <window_end_utc>)"`

Otherwise, format and post the report as an issue.

### Step 4 — Format the issue body

Structure the report as follows. Use GitHub-flavored markdown. Do **not** use `#` or `##` headings — start at `###`.

```
### Overview

One or two sentences summarising the day's activity (highlight the most notable changes).

> [!NOTE]
> Reporting window: <window_start_utc> → <window_end_utc>

### Commits (<count>)

- `<short_sha>` <commit message> — @<author> ([view](https://github.com/…))
- _No commits in window._ (when count is 0)

### Pull Requests (<count>)

- `opened` #<N> <title> — @<author> ([view](…))
- `closed` #<N> <title> — @<author> ([view](…))
- _No pull request activity in window._ (when count is 0)

### Issues (<count>)

- `opened` #<N> <title> — @<author> ([view](…))
- `closed` #<N> <title> — @<author> ([view](…))
- _No issue activity in window._ (when count is 0)

### Workflow Runs (<count>)

- `<status>` <name> — <conclusion> ([view](…))
- _No workflow runs in window._ (when count is 0)

### Releases (<count>)

- `<tag>` <name> ([view](…))
- _No releases in window._ (when count is 0)

**Workflow run:** [§<run_id>](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})
```

Rules:
- Use `> [!WARNING]` if any workflow run concluded with `failure`.
- Use `> [!CAUTION]` if more than 5 issues were opened in one day (unusual spike).
- Wrap the full per-item lists in `<details><summary>View all …</summary>` blocks when a category has more than 10 items.
- Do not include `@mentions` for usernames — format authors as plain text (e.g. `author: alice`).
- Do not include closing-keyword phrases such as `fixes #N` or `closes #N`.
- Minimum body length: 20 characters. Maximum: 65000 characters.
