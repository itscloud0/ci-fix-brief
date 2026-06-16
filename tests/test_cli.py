import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_cli_json_output_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "ci.log"
            log_path.write_text("Run pytest\nFAILED tests/test_demo.py::test_demo\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "ci_fix_brief",
                    str(log_path),
                    "--format",
                    "json",
                ],
                check=True,
                text=True,
                capture_output=True,
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["finding_count"], 1)
        self.assertEqual(payload["commands"], ["pytest"])

    def test_cli_writes_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "ci.log"
            out_path = Path(tmp) / "brief.md"
            log_path.write_text("Run npm test\nError: Process completed with exit code 1.\n", encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "ci_fix_brief",
                    str(log_path),
                    "--output",
                    str(out_path),
                ],
                check=True,
                text=True,
                capture_output=True,
            )

            self.assertIn("# CI Fix Brief", out_path.read_text(encoding="utf-8"))

    def test_cli_missing_file_is_user_facing_error(self):
        result = subprocess.run(
            [sys.executable, "-m", "ci_fix_brief", "missing.log"],
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("log file not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
