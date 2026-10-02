# Changelog

All notable changes to this project will be documented here.

## Unreleased

- Detect named Go test failures and subtests; add synthetic assertion and panic
  fixtures with deterministic Markdown/JSON coverage and passing-log checks.

- Added a GitHub Actions wrapper that reads a failed run log and uploads
  `CI_FIX_BRIEF.md` as a retention-controlled artifact.
- Added a public CI smoke job that exercises the supplied-log Action path and
  verifies artifact generation on every workflow run.

## v0.1.0 - 2026-06-16

- Initial release of the `ci-fix-brief` CLI.
- Added Markdown and JSON output.
- Added command, finding, test-summary, and next-step extraction.
- Added best-effort redaction for common token shapes and key-value secrets.
- Added examples, tests, CI, and launch materials.
