# ci-fix-brief

Turn noisy CI logs into compact repair briefs for coding agents.

`ci-fix-brief` reads a failing CI log and extracts the commands, test summaries, high-signal failure lines, nearby context, and next repair steps. It runs locally, has zero runtime dependencies, and redacts common token shapes before printing output.

## Problem

Failed CI logs are often long, repetitive, and awkward to paste into a coding-agent session. The useful facts are usually scattered across commands, test summaries, stack traces, and the final exit line.

## Why This Exists

Coding agents fix CI faster when they get a small, structured failure brief instead of a raw log dump. `ci-fix-brief` gives maintainers a deterministic first pass that is safe to inspect, easy to paste, and usable in scripts.

## Installation

From this repository:

```bash
python -m pip install .
```

After publishing:

```bash
pipx install git+https://github.com/itscloud0/ci-fix-brief.git
```

## 30-Second Quickstart

```bash
python -m pip install .
ci-fix-brief examples/failing-pytest.log
```

Save a Markdown repair brief:

```bash
ci-fix-brief examples/failing-pytest.log --output ci-brief.md
```

Emit JSON for automation:

```bash
ci-fix-brief examples/failing-pytest.log --format json
```

Pipe a log from another command:

```bash
cat examples/npm-build.log | ci-fix-brief --format json
```

## Demo Output

```text
# CI Fix Brief

Source: `examples/failing-pytest.log`

## Snapshot

- Lines scanned: 13
- Findings: 2
- Commands detected: 1

## Likely Failing Commands

- `pytest`

## Test Summary

- 1 failed, 12 passed in 0.48s

## Findings

### 1. tests/test_api.py::test_healthcheck - AssertionError: expected 200

- Severity: `error`
- Category: `test`
- Line: `9`
```

## Usage Examples

Generate a brief from a GitHub Actions log saved to disk:

```bash
ci-fix-brief failed-run.log --output CI_FIX_BRIEF.md
```

Use a stricter context window:

```bash
ci-fix-brief failed-run.log --context 4 --max-findings 12
```

Make a CI job fail when the log contains high-signal failures:

```bash
ci-fix-brief failed-run.log --fail-on-findings
```

Use JSON in another script:

```bash
ci-fix-brief failed-run.log --format json | python -m json.tool
```

Summarize Go test assertion failures, subtests, and panics:

```bash
ci-fix-brief examples/failing-go-test.log
ci-fix-brief examples/failing-go-panic.log --format json
```

These synthetic fixtures show named failing tests with nearby assertion or panic
context. Detection covers plain `go test` text; `go test -json` and Go compiler
diagnostics are not parsed specially.

## Common Use Cases

- Paste a compact CI failure brief into a coding-agent repair prompt.
- Summarize failed GitHub Actions logs before opening an issue.
- Store `CI_FIX_BRIEF.md` as a lightweight artifact after a failed run.
- Convert raw test logs into JSON for internal automation.
- Reduce accidental token exposure when sharing logs by redacting common token shapes.

## Comparison And Alternatives

- Raw CI logs preserve everything, but they are noisy and expensive to review.
- `grep` is fast, but it does not group commands, context, summaries, and repair steps.
- Full observability tools are deeper, but they require services and setup. This tool is local-first and small.
- Secret scanners are stricter. `ci-fix-brief` only redacts common token shapes in rendered output.

## GitHub Action

Generate a brief from a completed failed workflow and upload `CI_FIX_BRIEF.md`
as an artifact. Copy `examples/github-actions/ci-failure-brief.yml` into the
target repository; the workflow needs `actions: read` so `gh` can read the
failed run log.

```yaml
permissions:
  actions: read
  contents: read

jobs:
  brief:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - uses: itscloud0/ci-fix-brief@main # Pin to a commit or release in production.
        with:
          run-id: ${{ github.event.workflow_run.id }}
          repository: ${{ github.event.workflow_run.repository.full_name }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

The action also accepts `log-file` when a workflow already saves or produces a
log. It runs locally from the repository source, makes no model calls, uses the
GitHub CLI only for failed-run log lookup, and uploads the generated brief with
a seven-day default retention. Pin the `uses` reference to a commit or release
when adding it to a production workflow.

## Limitations

- Detection is heuristic and focused on common CI/test log shapes.
- It does not download logs from GitHub; save or pipe logs into the CLI.
- Redaction is best-effort and not a replacement for secret scanning.
- Very large logs should be pre-trimmed to the failed job or failing step.
- Python 3.9+ is required.

## Roadmap

- Add a `gh run view` helper mode that shells out to GitHub CLI when available.
- Add pattern fixtures for Rust, Java, and Playwright failures.
- Add SARIF-like JSON output for downstream tools.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Small fixtures for real-world CI failure formats are especially useful.

## License

MIT. See [LICENSE](LICENSE).
