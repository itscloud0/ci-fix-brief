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

    def test_rust_assertion_fixture_keeps_test_location_and_summary(self):
        log = (Path(__file__).resolve().parents[1] / "examples/failing-rust-test.log").read_text()
        brief = analyze_log(log, source="rust-test.log", context_lines=3)
        self.assertEqual(brief.commands, ["cargo test"])
        self.assertEqual([(f.category, f.message, f.line) for f in brief.findings],
                         [("test", "checks::status_code", 4),
                          ("runtime", "panicked at src/health.rs:24:5:", 9),
                          ("runtime", "test failed, to rerun pass `--lib`", 20)])
        self.assertIn("left: 503", "\n".join(brief.findings[1].context))
        self.assertIn("right: 200", "\n".join(brief.findings[1].context))
        self.assertEqual(brief.test_summaries, [log.splitlines()[17]])
        self.assertIn("focused failing test", " ".join(brief.next_steps))
        payload = json.loads(render_json(brief))
        self.assertEqual(payload["findings"][0]["message"], "checks::status_code")
        self.assertIn("src/health.rs:24:5", render_markdown(brief))
        self.assertEqual(render_json(brief), render_json(analyze_log(
            log, source="rust-test.log", context_lines=3)))

    def test_rust_panic_fixture_preserves_reason_and_redacts_context(self):
        log = (Path(__file__).resolve().parents[1] / "examples/failing-rust-panic.log").read_text()
        brief = analyze_log(log)
        self.assertEqual(brief.commands, ["cargo test --test configuration"])
        self.assertEqual(brief.findings[0].message, "config::requires_endpoint")
        self.assertEqual(brief.findings[1].line, 8)
        self.assertIn("missing endpoint", "\n".join(brief.findings[1].context))
        self.assertIn("tests/configuration.rs:9:5", render_markdown(brief))
        self.assertEqual(len(brief.test_summaries), 1)
        secret_log = log.replace("missing endpoint", "password=synthetic-value missing endpoint")
        self.assertNotIn("synthetic-value", render_json(analyze_log(secret_log)))
        self.assertIn("password=[REDACTED]", render_markdown(analyze_log(secret_log)))

    def test_passing_and_ignored_rust_tests_do_not_create_findings(self):
        brief = analyze_log("Run cargo test\ntest checks::healthy ... ok\n"
                            "test checks::planned ... ignored\n"
                            "test checks::expected_panic - should panic ... ok\n"
                            "test result: ok. 2 passed; 0 failed; 1 ignored; 0 measured; "
                            "0 filtered out; finished in 0.00s\n")
        self.assertEqual(brief.findings, [])
        self.assertEqual(brief.test_summaries, [])

    def test_actions_multiline_fixture_preserves_complete_script(self):
        log = (Path(__file__).resolve().parents[1] / "examples/failing-actions-multiline.log").read_text()
        script = "python -m pip install .\npython -m pytest \\\n  tests/test_health.py \\\n  --maxfail=1"
        for wrapped in (log, "".join("test\tRun tests\t" + line + "\n" for line in log.splitlines())):
            brief = analyze_log(wrapped)
            self.assertEqual(brief.commands, [script])
            self.assertNotIn("shell:", brief.commands[0])
            self.assertNotIn("MODE:", brief.commands[0])
            self.assertEqual(json.loads(render_json(brief))["commands"], [script])
            self.assertIn("```sh\n" + script + "\n```", render_markdown(brief))
            self.assertEqual(render_json(brief), render_json(analyze_log(wrapped)))

    def test_actions_script_redaction_deduplication_and_boundaries(self):
        block = "##[group]Run echo start\n\x1b[36;1mecho start\x1b[0m\nexport password=synthetic-value\npytest\nshell: bash -e {0}\nenv:\n  MODE: synthetic\n##[endgroup]\n"
        brief = analyze_log(block + "unprefixed output\n" + block + "$ echo done\n")
        self.assertEqual(brief.commands, ["echo start\nexport password=[REDACTED]\npytest", "echo done"])
        self.assertNotIn("synthetic-value", render_json(brief))
        self.assertEqual(len(analyze_log(block + "".join("$ cmd%d\n" % n for n in range(20))).commands), 12)

    def test_incomplete_actions_group_does_not_turn_output_into_script(self):
        for log in ("##[group]Run pytest\noutput line\n", "##[group]Run pytest\noutput line\n##[endgroup]\n",
                    "##[group]Run pytest\npytest\nshell: bash -e {0}\noutput line\n"):
            self.assertEqual(analyze_log(log).commands, ["pytest"])
        self.assertEqual(analyze_log("Run pytest\n$ pytest\n+ cargo test\n> go test ./...\n").commands,
                         ["pytest", "cargo test", "go test ./..."])

    def test_multiline_markdown_fence_keeps_embedded_backticks_inside_script(self):
        script = 'printf "```"\npytest'
        log = '##[group]Run printf "```"\n' + script + '\nshell: bash -e {0}\n##[endgroup]\n'
        self.assertEqual(analyze_log(log).commands, [script])
        self.assertIn("````sh\n" + script + "\n````", render_markdown(analyze_log(log)))

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
