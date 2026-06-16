"""Command-line interface for ci-fix-brief."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__
from .analyzer import analyze_log, render_json, render_markdown


class CliError(Exception):
    """Expected user-facing CLI error."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci-fix-brief",
        description="Turn noisy CI logs into compact repair briefs for coding agents.",
    )
    parser.add_argument(
        "logfile",
        nargs="?",
        default="-",
        help="CI log file to analyze. Use '-' or pipe logs on stdin.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Default: markdown.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write output to a file instead of stdout.",
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=8,
        help="Maximum findings to include. Default: 8.",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=2,
        help="Context lines before and after each finding. Default: 2.",
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit with status 1 when any finding is detected.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        _validate_args(args)
        text, source = _read_input(args.logfile)
        brief = analyze_log(
            text,
            source=source,
            max_findings=args.max_findings,
            context_lines=args.context,
        )
        output = render_json(brief) if args.format == "json" else render_markdown(brief)
        _write_output(output, args.output)
    except CliError as error:
        parser.exit(2, f"ci-fix-brief: error: {error}\n")

    if args.fail_on_findings and brief.findings:
        return 1
    return 0


def _validate_args(args: argparse.Namespace) -> None:
    if args.max_findings < 1:
        raise CliError("--max-findings must be at least 1")
    if args.context < 0:
        raise CliError("--context must be 0 or greater")


def _read_input(logfile: str) -> tuple[str, str]:
    if logfile == "-":
        if sys.stdin.isatty():
            raise CliError("pass a log file path or pipe CI logs on stdin")
        return sys.stdin.read(), "stdin"

    path = Path(logfile)
    if not path.exists():
        raise CliError(f"log file not found: {path}")
    if path.is_dir():
        raise CliError(f"expected a log file, got a directory: {path}")
    return path.read_text(encoding="utf-8", errors="replace"), str(path)


def _write_output(output: str, target: str | None) -> None:
    if target:
        Path(target).write_text(output, encoding="utf-8")
        return
    sys.stdout.write(output)
