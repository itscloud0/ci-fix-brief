import json
import unittest

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
