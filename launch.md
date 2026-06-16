# Launch Plan: ci-fix-brief

## Suggested GitHub Repository Name

ci-fix-brief

## GitHub Description

Turn noisy CI logs into compact repair briefs for coding agents.

## GitHub Topics

- developer-tools
- ci
- github-actions
- coding-agents
- ai-engineering
- log-analysis
- testing
- devex
- python
- automation

## README Hero Tagline

Turn noisy CI logs into compact repair briefs for coding agents.

## X/Twitter Launch Post

Built `ci-fix-brief`: a small Python CLI that turns failing CI logs into compact repair briefs for coding agents.

It extracts commands, test summaries, failure lines, context, and next repair steps. Local-only, zero runtime deps, Markdown or JSON output.

## LinkedIn Launch Post

I built `ci-fix-brief`, a local-first CLI for turning noisy CI logs into compact repair briefs.

It is meant for maintainers and coding-agent users who do not want to paste a full failed GitHub Actions log into a repair prompt. The tool extracts likely failing commands, test summaries, high-signal errors, nearby context, and next steps. It emits Markdown for humans or JSON for automation, has zero runtime dependencies, and redacts common token shapes before rendering.

The goal is narrow: make CI repair loops easier to hand to a person or agent without losing the useful failure context.

## Hacker News Title

Show HN: ci-fix-brief - compact CI failure briefs for coding agents

## Reddit Post

Subreddit: r/devops or r/github

Title: I built a small CLI that summarizes failing CI logs for coding-agent repair loops

Post:

I built `ci-fix-brief`, a local Python CLI that turns raw CI logs into compact Markdown or JSON repair briefs. It extracts likely failing commands, test summaries, failure lines, context, and suggested next steps.

I made it because failed CI logs are often too noisy to paste directly into a coding-agent session. The CLI uses no network calls, no API keys, and has zero runtime dependencies. Feedback on useful log patterns is welcome.

## Demo Captions

1. Turn a failed pytest log into a pasteable repair brief.
2. Extract failing commands and exit codes from GitHub Actions logs.
3. Emit JSON when another tool needs structured failure context.
4. Keep the first repair prompt focused on the actual failure.
5. Redact common token shapes before sharing brief output.

## Good First Issue Ideas

1. Add fixtures for common Go test failure output.
2. Add fixtures for Rust `cargo test` failure output.
3. Improve command detection for multi-line GitHub Actions `run` blocks.

## Roadmap Issues

1. Add an optional `gh run view` helper that shells out to GitHub CLI.
2. Add a GitHub Action wrapper that uploads `CI_FIX_BRIEF.md` on failure.
3. Add SARIF-like JSON fields for downstream CI dashboards.

## Suggested First Release Title

ci-fix-brief v0.1.0 - compact CI repair briefs for coding agents

## Short First Release Notes

Initial release with Markdown and JSON output, command detection, test-summary extraction, failure context, best-effort redaction, examples, tests, and CI.

## What Not To Claim

- Do not claim it fully understands every CI provider.
- Do not claim it replaces secret scanning.
- Do not claim suggested next steps are authoritative.
- Do not claim it downloads CI logs automatically in v0.1.

## Known Limitations

- Log analysis is heuristic.
- Logs must be passed as a file or stdin.
- Redaction is best-effort.
- Very large logs should be trimmed to the failed job first.
