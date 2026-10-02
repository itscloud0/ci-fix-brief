import json
import unittest
from pathlib import Path

from ci_fix_brief.analyzer import analyze_log, render_json, render_markdown


PYTEST_LOG = """Run pytest
============================= test session starts ==============================
tests/test_api.py F

=================================== FAILURES ===================================
FAILED tests/test_api.py::test_healthcheck - AssertionError: expected 200
E   AssertionError: expected 200
=========================== 1 failed, 12 passed in 0.48s ===========================
Error: Process completed with exit code 1.
"""


class AnalyzerTests(unittest.TestCase):
    def test_detects_pytest_failure_and_exit_code(self):
        brief = analyze_log(PYTEST_LOG, source="pytest.log")

        self.assertEqual(brief.line_count, 9)
        self.assertEqual(brief.commands, ["pytest"])
        self.assertIn("1 failed, 12 passed in 0.48s", brief.test_summaries)
        self.assertGreaterEqual(len(brief.findings), 2)
        self.assertEqual(brief.findings[0].category, "test")
        self.assertIn("test_healthcheck", brief.findings[0].message)

    def test_go_assertion_fixture_preserves_tests_context_and_summary(self):
        log = (Path(__file__).resolve().parents[1] / "examples/failing-go-test.log").read_text()
        brief = analyze_log(log, source="go-test.log")
        self.assertEqual(brief.commands, ["go test ./..."])
        self.assertEqual([f.message for f in brief.findings],
                         ["TestHealthcheck", "TestHealthcheck/ready"])
        self.assertEqual([f.line for f in brief.findings], [4, 7])
        self.assertTrue(all(f.category == "test" for f in brief.findings))
        self.assertIn("expected status 200, got 503", "\n".join(brief.findings[0].context))
        self.assertIn("FAIL\texample.com/synthetic/health\t0.004s", brief.test_summaries)
        self.assertIn("focused failing test", " ".join(brief.next_steps))
        payload = json.loads(render_json(brief))
        self.assertEqual(payload["findings"][1]["message"], "TestHealthcheck/ready")
        self.assertEqual(render_json(brief), render_json(analyze_log(log, source="go-test.log")))

    def test_go_panic_fixture_keeps_runtime_error(self):
        log = (Path(__file__).resolve().parents[1] / "examples/failing-go-panic.log").read_text()
        brief = analyze_log(log, context_lines=3)
        self.assertEqual([(f.category, f.message) for f in brief.findings],
                         [("test", "TestConfig"),
                          ("runtime", "missing required configuration [recovered]")])
        self.assertIn("config_test.go:12", "\n".join(brief.findings[1].context))
        self.assertIn("missing required configuration", render_markdown(brief))

    def test_passing_go_tests_do_not_create_findings(self):
        brief = analyze_log("Run go test ./...\n--- PASS: TestHealthcheck (0.00s)\n"
                            "PASS\nok\texample.com/synthetic/health\t0.004s\n")
        self.assertEqual(brief.findings, [])
        self.assertEqual(brief.test_summaries, [])

    def test_redacts_key_value_secrets(self):
        brief = analyze_log("Run deploy\nerror: authorization=visible-value failed\n", context_lines=1)
        markdown = render_markdown(brief)

        self.assertIn("authorization=[REDACTED]", markdown)
        self.assertNotIn("visible-value", markdown)

    def test_json_output_is_structured(self):
        brief = analyze_log(PYTEST_LOG, source="pytest.log")
        payload = json.loads(render_json(brief))

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["source"], "pytest.log")
        self.assertEqual(payload["commands"], ["pytest"])
        self.assertEqual(payload["findings"][0]["severity"], "error")

    def test_no_findings_gets_next_step(self):
        brief = analyze_log("Run pytest\n12 passed in 0.21s\n")

        self.assertEqual(brief.findings, [])
        self.assertIn("No high-signal failure line", brief.next_steps[0])


if __name__ == "__main__":
    unittest.main()
