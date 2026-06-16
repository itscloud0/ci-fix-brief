# ci-fix-brief v0.1.0

Initial release of `ci-fix-brief`, a local CLI that turns noisy CI logs into compact repair briefs for coding agents and maintainers.

Includes:

- Markdown and JSON output.
- Detection for common failing commands, test summaries, runtime errors, assertion failures, and exit codes.
- Nearby log context for each finding.
- Best-effort redaction of common token and key-value secret shapes.
- Example logs, tests, and GitHub Actions CI.

Known limits:

- Detection is heuristic.
- Logs must be provided as a file or stdin.
- Redaction is not a replacement for a dedicated secret scanner.
