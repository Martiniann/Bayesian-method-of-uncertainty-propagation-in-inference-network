# Bayesian-method-of-uncertainty-propagation-in-inference-networ
This repository contains a project for topic Expert systems.

## Daily repository activity report

This repository includes a scheduled GitHub Actions workflow at
`.github/workflows/daily-activity-report.yml`.

It runs every day at **08:00 UTC** and:

- collects recent repository activity from the last 24 hours,
- generates a Markdown report with commits, pull requests, issues, workflow runs, and releases,
- creates or updates a daily GitHub issue containing that report.

The report generator lives in `scripts/daily_activity_report.py` and uses only the Python standard library.

### Run locally

Set a GitHub token in `GITHUB_TOKEN`, then run:

```powershell
python scripts/daily_activity_report.py --repo OWNER/REPOSITORY --output daily-activity-report.md
```

### Run tests

```powershell
python -m unittest tests.test_daily_activity_report
```

