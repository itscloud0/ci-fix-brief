# Changelog

All notable changes to this project will be documented here.

## Unreleased

- Added a GitHub Actions wrapper that reads a failed run log and uploads
  `CI_FIX_BRIEF.md` as a retention-controlled artifact.

## v0.1.0 - 2026-06-16

- Initial release of the `ci-fix-brief` CLI.
- Added Markdown and JSON output.
- Added command, finding, test-summary, and next-step extraction.
- Added best-effort redaction for common token shapes and key-value secrets.
- Added examples, tests, CI, and launch materials.
