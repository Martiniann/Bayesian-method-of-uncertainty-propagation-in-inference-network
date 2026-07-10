from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

API_ROOT = "https://api.github.com"
MAX_SECTION_ITEMS = 20


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def to_github_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(repo: str, suffix: str = "") -> str:
    if "/" not in repo:
        raise ValueError("Repository must use the format 'owner/name'.")
    owner, name = repo.split("/", 1)
    return f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(name)}{suffix}"


def github_get_json(path: str, token: Optional[str] = None, params: Optional[dict] = None) -> Any:
    url = f"{API_ROOT}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "daily-activity-report-script",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed: {exc.code} {exc.reason}\n{body}") from exc


def fetch_activity(repo: str, token: Optional[str], since: datetime) -> Dict[str, Any]:
    repo_data = github_get_json(repo_path(repo), token=token)
    since_text = to_github_timestamp(since)

    commits = github_get_json(
        repo_path(repo, "/commits"),
        token=token,
        params={"since": since_text, "per_page": 100},
    )
    pulls = github_get_json(
        repo_path(repo, "/pulls"),
        token=token,
        params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 100},
    )
    issues = github_get_json(
        repo_path(repo, "/issues"),
        token=token,
        params={"state": "all", "since": since_text, "sort": "updated", "direction": "desc", "per_page": 100},
    )
    releases = github_get_json(
        repo_path(repo, "/releases"),
        token=token,
        params={"per_page": 20},
    )
    workflow_runs_data = github_get_json(
        repo_path(repo, "/actions/runs"),
        token=token,
        params={"per_page": 50},
    )

    pulls = [pr for pr in pulls if parse_timestamp(pr["updated_at"]) >= since]
    issues = [issue for issue in issues if "pull_request" not in issue]
    releases = [
        release
        for release in releases
        if parse_timestamp(release.get("published_at") or release.get("created_at")) >= since
    ]
    workflow_runs = [
        run
        for run in workflow_runs_data.get("workflow_runs", [])
        if parse_timestamp(run["created_at"]) >= since
    ]

    return {
        "repo": repo,
        "repo_url": repo_data["html_url"],
        "default_branch": repo_data.get("default_branch", "default branch"),
        "commits": commits,
        "pulls": pulls,
        "issues": issues,
        "releases": releases,
        "workflow_runs": workflow_runs,
    }


def classify_issue_activity(issue: Dict[str, Any], since: datetime) -> str:
    created_at = parse_timestamp(issue["created_at"])
    closed_at = parse_timestamp(issue["closed_at"]) if issue.get("closed_at") else None
    if closed_at and closed_at >= since:
        return "closed"
    if created_at >= since:
        return "opened"
    return "updated"


def classify_pull_activity(pr: Dict[str, Any], since: datetime) -> str:
    created_at = parse_timestamp(pr["created_at"])
    merged_at = parse_timestamp(pr["merged_at"]) if pr.get("merged_at") else None
    closed_at = parse_timestamp(pr["closed_at"]) if pr.get("closed_at") else None
    if merged_at and merged_at >= since:
        return "merged"
    if closed_at and closed_at >= since:
        return "closed"
    if created_at >= since:
        return "opened"
    return "updated"


def truncate(text: str, limit: int = 100) -> str:
    text = " ".join(text.strip().split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def capped(items: List[Dict[str, Any]], limit: int = MAX_SECTION_ITEMS) -> tuple[List[Dict[str, Any]], int]:
    if len(items) <= limit:
        return items, 0
    return items[:limit], len(items) - limit


def render_commits(commits: List[Dict[str, Any]]) -> List[str]:
    visible, hidden = capped(commits)
    lines = []
    for commit in visible:
        sha = commit["sha"][:7]
        message = truncate(commit["commit"]["message"].splitlines()[0])
        author = commit["commit"].get("author", {}).get("name") or "unknown"
        lines.append(f"- `{sha}` {message} - {author} ([view commit]({commit['html_url']}))")
    if hidden:
        lines.append(f"- _{hidden} additional commit(s) omitted for brevity._")
    return lines


def render_pulls(pulls: List[Dict[str, Any]], since: datetime) -> List[str]:
    visible, hidden = capped(pulls)
    lines = []
    for pr in visible:
        action = classify_pull_activity(pr, since)
        title = truncate(pr["title"])
        author = pr["user"]["login"]
        lines.append(f"- `{action}` PR #{pr['number']} {title} - @{author} ([view PR]({pr['html_url']}))")
    if hidden:
        lines.append(f"- _{hidden} additional pull request(s) omitted for brevity._")
    return lines


def render_issues(issues: List[Dict[str, Any]], since: datetime) -> List[str]:
    visible, hidden = capped(issues)
    lines = []
    for issue in visible:
        action = classify_issue_activity(issue, since)
        title = truncate(issue["title"])
        author = issue["user"]["login"]
        lines.append(f"- `{action}` issue #{issue['number']} {title} - @{author} ([view issue]({issue['html_url']}))")
    if hidden:
        lines.append(f"- _{hidden} additional issue(s) omitted for brevity._")
    return lines


def render_workflow_runs(runs: List[Dict[str, Any]]) -> List[str]:
    visible, hidden = capped(runs)
    lines = []
    for run in visible:
        name = truncate(run.get("name") or "Unnamed workflow")
        status = run.get("conclusion") or run.get("status") or "unknown"
        event = run.get("event") or "unknown"
        lines.append(f"- `{status}` workflow `{name}` on event `{event}` ([view run]({run['html_url']}))")
    if hidden:
        lines.append(f"- _{hidden} additional workflow run(s) omitted for brevity._")
    return lines


def render_releases(releases: List[Dict[str, Any]]) -> List[str]:
    visible, hidden = capped(releases)
    lines = []
    for release in visible:
        name = truncate(release.get("name") or release.get("tag_name") or "Unnamed release")
        tag = release.get("tag_name") or "no-tag"
        lines.append(f"- release `{tag}` {name} ([view release]({release['html_url']}))")
    if hidden:
        lines.append(f"- _{hidden} additional release(s) omitted for brevity._")
    return lines


def section(title: str, lines: Iterable[str], empty_message: str) -> List[str]:
    rendered = list(lines)
    output = [f"## {title}", ""]
    if rendered:
        output.extend(rendered)
    else:
        output.append(f"- _{empty_message}_")
    output.append("")
    return output


def render_markdown(activity: Dict[str, Any], since: datetime, until: datetime, generated_at: datetime) -> str:
    commits = activity["commits"]
    pulls = activity["pulls"]
    issues = activity["issues"]
    releases = activity["releases"]
    workflow_runs = activity["workflow_runs"]

    lines = [
        "# Daily repository activity report",
        "",
        f"Repository: [{activity['repo']}]({activity['repo_url']})",
        f"Reporting window: **{to_github_timestamp(since)}** -> **{to_github_timestamp(until)}**",
        f"Generated at: **{to_github_timestamp(generated_at)}**",
        "",
        "## Snapshot",
        "",
        f"- Commits on `{activity['default_branch']}`: **{len(commits)}**",
        f"- Pull requests touched: **{len(pulls)}**",
        f"- Issues touched: **{len(issues)}**",
        f"- Workflow runs started: **{len(workflow_runs)}**",
        f"- Releases published: **{len(releases)}**",
        "",
        "> This report covers the previous 24 hours by default. Counts are based on GitHub REST API results available at generation time.",
        "",
    ]

    lines.extend(section("Commits", render_commits(commits), "No commits were pushed to the default branch in this window."))
    lines.extend(section("Pull requests", render_pulls(pulls, since), "No pull requests were opened, updated, merged, or closed in this window."))
    lines.extend(section("Issues", render_issues(issues, since), "No issues were opened, updated, or closed in this window."))
    lines.extend(section("Workflow runs", render_workflow_runs(workflow_runs), "No workflow runs started in this window."))
    lines.extend(section("Releases", render_releases(releases), "No releases were published in this window."))

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a daily GitHub repository activity report in Markdown.")
    parser.add_argument("--repo", required=True, help="Repository in owner/name format.")
    parser.add_argument("--output", default="daily-activity-report.md", help="Path to the Markdown report to write.")
    parser.add_argument("--since-hours", type=int, default=24, help="How many hours back to include. Default: 24.")
    parser.add_argument("--since", help="Explicit UTC timestamp override, e.g. 2026-07-09T08:00:00Z.")
    parser.add_argument("--token-env", default="GITHUB_TOKEN", help="Environment variable that contains the GitHub token.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated_at = utc_now()
    since = parse_timestamp(args.since) if args.since else generated_at - timedelta(hours=args.since_hours)
    token = os.environ.get(args.token_env)

    activity = fetch_activity(args.repo, token=token, since=since)
    markdown = render_markdown(activity, since=since, until=generated_at, generated_at=generated_at)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"Wrote {output_path} for {args.repo}")
    print(f"Commits: {len(activity['commits'])}")
    print(f"Pull requests: {len(activity['pulls'])}")
    print(f"Issues: {len(activity['issues'])}")
    print(f"Workflow runs: {len(activity['workflow_runs'])}")
    print(f"Releases: {len(activity['releases'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())



