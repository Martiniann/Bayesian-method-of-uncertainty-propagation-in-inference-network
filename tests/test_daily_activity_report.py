from datetime import datetime, timezone
import unittest

from scripts.daily_activity_report import (
    classify_issue_activity,
    classify_pull_activity,
    render_markdown,
)


class DailyActivityReportTests(unittest.TestCase):
    def setUp(self):
        self.since = datetime(2026, 7, 9, 8, 0, tzinfo=timezone.utc)
        self.until = datetime(2026, 7, 10, 8, 0, tzinfo=timezone.utc)

    def test_classify_issue_activity_prefers_closed_when_closed_in_window(self):
        issue = {
            "created_at": "2026-07-01T08:00:00Z",
            "closed_at": "2026-07-09T12:00:00Z",
        }
        self.assertEqual(classify_issue_activity(issue, self.since), "closed")

    def test_classify_pull_activity_prefers_merged_when_merged_in_window(self):
        pr = {
            "created_at": "2026-07-01T08:00:00Z",
            "closed_at": "2026-07-09T13:00:00Z",
            "merged_at": "2026-07-09T12:00:00Z",
        }
        self.assertEqual(classify_pull_activity(pr, self.since), "merged")

    def test_render_markdown_contains_snapshot_and_sections(self):
        activity = {
            "repo": "octo-org/octo-repo",
            "repo_url": "https://github.com/octo-org/octo-repo",
            "default_branch": "main",
            "commits": [
                {
                    "sha": "1234567890abcdef",
                    "html_url": "https://github.com/octo-org/octo-repo/commit/1234567",
                    "commit": {
                        "message": "Add daily issue automation\n\nMore details",
                        "author": {"name": "octocat"},
                    },
                }
            ],
            "pulls": [
                {
                    "number": 12,
                    "title": "Automate the daily issue report",
                    "html_url": "https://github.com/octo-org/octo-repo/pull/12",
                    "user": {"login": "octocat"},
                    "created_at": "2026-07-09T09:00:00Z",
                    "closed_at": None,
                    "merged_at": None,
                }
            ],
            "issues": [
                {
                    "number": 34,
                    "title": "Track workflow automation",
                    "html_url": "https://github.com/octo-org/octo-repo/issues/34",
                    "user": {"login": "hubot"},
                    "created_at": "2026-07-09T10:00:00Z",
                    "closed_at": None,
                }
            ],
            "workflow_runs": [
                {
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "html_url": "https://github.com/octo-org/octo-repo/actions/runs/1",
                    "created_at": "2026-07-09T11:00:00Z",
                }
            ],
            "releases": [
                {
                    "name": "Version 1.0.0",
                    "tag_name": "v1.0.0",
                    "html_url": "https://github.com/octo-org/octo-repo/releases/tag/v1.0.0",
                }
            ],
        }

        markdown = render_markdown(activity, self.since, self.until, self.until)

        self.assertIn("# Daily repository activity report", markdown)
        self.assertIn("Commits on `main`: **1**", markdown)
        self.assertIn("`opened` PR #12", markdown)
        self.assertIn("`opened` issue #34", markdown)
        self.assertIn("`success` workflow `CI`", markdown)
        self.assertIn("release `v1.0.0` Version 1.0.0", markdown)


if __name__ == "__main__":
    unittest.main()

