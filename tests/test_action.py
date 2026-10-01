import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.action = (ROOT / "action.yml").read_text(encoding="utf-8")
        self.example = (ROOT / "examples/github-actions/ci-failure-brief.yml").read_text(
            encoding="utf-8"
        )

    def test_action_supports_supplied_logs_and_failed_run_lookup(self):
        self.assertIn("log-file:", self.action)
        self.assertIn('cp "$CI_FIX_BRIEF_LOG_FILE" "$log_path"', self.action)
        self.assertIn('gh run view "$run_id" --repo "$repository" --log-failed', self.action)
        self.assertIn("GH_TOKEN:", self.action)

    def test_action_generates_and_uploads_the_brief(self):
        self.assertIn('python -m ci_fix_brief "$RUNNER_TEMP/ci-fix-brief.log"', self.action)
        self.assertIn(
            "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
            self.action,
        )
        self.assertIn("if-no-files-found: error", self.action)

    def test_example_waits_for_failed_workflow_and_grants_log_read(self):
        self.assertIn("workflow_run:", self.example)
        self.assertIn("conclusion == 'failure'", self.example)
        self.assertIn("actions: read", self.example)
        self.assertIn("github.event.workflow_run.id", self.example)


if __name__ == "__main__":
    unittest.main()
