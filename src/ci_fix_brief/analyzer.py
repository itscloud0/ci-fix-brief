"""Core log analysis and rendering."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Iterable


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
KEY_VALUE_SECRET_RE = re.compile(
    r"(?i)\b(token|secret|password|passwd|api[_-]?key|authorization)\b"
    r"(\s*[:=]\s*)"
    r"([^\s\"']+)"
)
TOKEN_PATTERNS = [
    re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]

COMMAND_PREFIXES = ("$ ", "+ ", "> ")
TEST_SUMMARY_PATTERNS = [
    re.compile(r"=+\s*(?P<summary>.+\bfailed\b.+\bin\s+[0-9.]+s)\s*=+", re.IGNORECASE),
    re.compile(r"\b(?P<summary>\d+\s+failed,\s+.*\bin\s+[0-9.]+s)\b", re.IGNORECASE),
    re.compile(r"\b(?P<summary>Tests?:\s+.+failed.+)\b", re.IGNORECASE),
    re.compile(r"\b(?P<summary>Test Suites?:\s+.+failed.+)\b", re.IGNORECASE),
    re.compile(r"^(?P<summary>FAIL\s+.+)$"),
    re.compile(r"^(?P<summary>test result: FAILED\. .+)$"),
]

FINDING_PATTERNS = [
    (
        re.compile(r"^test\s+(?P<msg>\S+)\s+\.\.\.\s+FAILED$"),
        "test",
        "error",
    ),
    (
        re.compile(r"^thread ['\"].+['\"](?:\s+\(\d+\))?\s+(?P<msg>panicked at .+)$"),
        "runtime",
        "error",
    ),
    (
        re.compile(r"^--- FAIL:\s+(?P<msg>\S+)(?:\s+\([0-9.]+s\))?$"),
        "test",
        "error",
    ),
    (
        re.compile(r"\b(ModuleNotFoundError|ImportError):\s*(?P<msg>.+)", re.IGNORECASE),
        "dependency",
        "error",
    ),
    (
        re.compile(r"^(FAILED|FAIL)\s+(?P<msg>tests?/.*|.+::.+)", re.IGNORECASE),
        "test",
        "error",
    ),
    (
        re.compile(r"\b(AssertionError|assertion failed)\b(?P<msg>.*)", re.IGNORECASE),
        "test",
        "error",
    ),
    (
        re.compile(r"\b(TypeError|ValueError|KeyError|SyntaxError|NameError):\s*(?P<msg>.+)"),
        "runtime",
        "error",
    ),
    (
        re.compile(r"\b(npm ERR!|pnpm ERR!|yarn error)\s*(?P<msg>.+)", re.IGNORECASE),
        "package-manager",
        "error",
    ),
    (
        re.compile(r"\b(?P<msg>(?:Process completed with exit code|exit code)\s+\d+)", re.IGNORECASE),
        "command",
        "error",
    ),
    (
        re.compile(r"^\s*(fatal|panic|error):\s*(?P<msg>.+)", re.IGNORECASE),
        "runtime",
        "error",
    ),
    (
        re.compile(r"^\s*(warning):\s*(?P<msg>.+)", re.IGNORECASE),
        "warning",
        "warning",
    ),
]


@dataclass(frozen=True)
class Finding:
    """A high-signal line and its nearby context."""

    line: int
    severity: str
    category: str
    message: str
    context: list[str]


@dataclass(frozen=True)
class Brief:
    """Structured CI repair brief."""

    source: str
    line_count: int
    findings: list[Finding]
    commands: list[str]
    test_summaries: list[str]
    next_steps: list[str]
    redaction_note: str


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def redact_sensitive(text: str) -> str:
    """Mask common token shapes and key-value secrets before rendering."""

    redacted = KEY_VALUE_SECRET_RE.sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", text)
    for pattern in TOKEN_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def clean_line(line: str) -> str:
    return redact_sensitive(strip_ansi(line)).rstrip()


def analyze_log(
    text: str,
    *,
    source: str = "stdin",
    max_findings: int = 8,
    context_lines: int = 2,
) -> Brief:
    """Analyze raw CI log text and return a compact repair brief."""

    raw_lines = text.splitlines()
    lines = [clean_line(line) for line in raw_lines]

    commands = _detect_commands(lines)
    summaries = _detect_test_summaries(lines)
    findings = _detect_findings(lines, max_findings=max_findings, context_lines=context_lines)
    next_steps = _suggest_next_steps(findings)

    return Brief(
        source=source,
        line_count=len(lines),
        findings=findings,
        commands=commands,
        test_summaries=summaries,
        next_steps=next_steps,
        redaction_note="Common token and key-value secret shapes are rendered as [REDACTED].",
    )


def _detect_commands(lines: Iterable[str]) -> list[str]:
    commands: list[str] = []
    seen: set[str] = set()

    for line in lines:
        stripped = line.strip()
        command = ""
        if stripped.startswith("Run ") and len(stripped) > 4:
            command = stripped[4:].strip()
        elif stripped.startswith("##[group]Run "):
            command = stripped.removeprefix("##[group]Run ").strip()
        elif stripped.startswith(COMMAND_PREFIXES):
            command = stripped[2:].strip()

        if command and command not in seen:
            seen.add(command)
            commands.append(command)
        if len(commands) >= 12:
            break

    return commands


def _detect_test_summaries(lines: Iterable[str]) -> list[str]:
    summaries: list[str] = []
    seen: set[str] = set()

    for line in lines:
        stripped = line.strip()
        for pattern in TEST_SUMMARY_PATTERNS:
            match = pattern.search(stripped)
            if not match:
                continue
            summary = match.group("summary").strip()
            if summary not in seen:
                seen.add(summary)
                summaries.append(summary)
            break
        if len(summaries) >= 6:
            break

    return summaries


def _detect_findings(lines: list[str], *, max_findings: int, context_lines: int) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[str] = set()

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        for pattern, category, severity in FINDING_PATTERNS:
            match = pattern.search(stripped)
            if not match:
                continue
            if _is_pytest_detail_duplicate(stripped, category, findings, index + 1, context_lines):
                break
            raw_message = match.groupdict().get("msg") or stripped
            message = _compact_message(raw_message or stripped)
            fingerprint = f"{category}:{message.lower()}"
            if fingerprint in seen:
                break
            seen.add(fingerprint)
            findings.append(
                Finding(
                    line=index + 1,
                    severity=severity,
                    category=category,
                    message=message,
                    context=_context(lines, index, context_lines),
                )
            )
            break

        if len(findings) >= max_findings:
            break

    return findings


def _is_pytest_detail_duplicate(
    line: str,
    category: str,
    findings: list[Finding],
    current_line: int,
    context_lines: int,
) -> bool:
    if category != "test" or not findings:
        return False
    previous = findings[-1]
    nearby = previous.category == "test" and current_line <= previous.line + context_lines + 2
    detail_line = line.startswith(("E   AssertionError", ">   AssertionError"))
    return nearby and detail_line


def _context(lines: list[str], index: int, context_lines: int) -> list[str]:
    start = max(0, index - context_lines)
    end = min(len(lines), index + context_lines + 1)
    return [f"{line_number + 1}: {lines[line_number]}" for line_number in range(start, end)]


def _compact_message(message: str, *, limit: int = 180) -> str:
    compact = re.sub(r"\s+", " ", message).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _suggest_next_steps(findings: list[Finding]) -> list[str]:
    if not findings:
        return [
            "No high-signal failure line was detected. Re-run with a less-truncated log or increase CI log retention.",
            "Check the final failing command and compare local environment versions with CI.",
        ]

    categories = {finding.category for finding in findings}
    steps = ["Start from the first finding; it is usually closest to the root failure."]

    if "dependency" in categories:
        steps.append("Verify dependency installation and lockfile state before the failing test command.")
    if "test" in categories:
        steps.append("Run the focused failing test locally, then widen to the full suite after the fix.")
    if "package-manager" in categories:
        steps.append("Re-run the package manager command with the same lockfile and runtime version as CI.")
    if "runtime" in categories:
        steps.append("Inspect the stack or exception context around the first runtime error.")
    if "command" in categories:
        steps.append("Re-run the failing command exactly as CI invoked it.")
    if "warning" in categories and len(categories) == 1:
        steps.append("Warnings were detected but no hard failure line was found; inspect later log lines for the exit point.")

    return steps


def render_json(brief: Brief) -> str:
    payload = {
        "schema_version": "1.0",
        "source": brief.source,
        "line_count": brief.line_count,
        "finding_count": len(brief.findings),
        "commands": brief.commands,
        "test_summaries": brief.test_summaries,
        "findings": [asdict(finding) for finding in brief.findings],
        "next_steps": brief.next_steps,
        "redaction_note": brief.redaction_note,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_markdown(brief: Brief) -> str:
    lines = [
        "# CI Fix Brief",
        "",
        f"Source: `{brief.source}`",
        "",
        "## Snapshot",
        "",
        f"- Lines scanned: {brief.line_count}",
        f"- Findings: {len(brief.findings)}",
        f"- Commands detected: {len(brief.commands)}",
        f"- Redaction: {brief.redaction_note}",
        "",
    ]

    lines.extend(_render_commands(brief.commands))
    lines.extend(_render_summaries(brief.test_summaries))
    lines.extend(_render_findings(brief.findings))
    lines.extend(_render_next_steps(brief.next_steps))

    return "\n".join(lines).rstrip() + "\n"


def _render_commands(commands: list[str]) -> list[str]:
    lines = ["## Likely Failing Commands", ""]
    if not commands:
        lines.extend(["No shell command lines were detected.", ""])
        return lines

    for command in commands:
        lines.append(f"- `{command}`")
    lines.append("")
    return lines


def _render_summaries(summaries: list[str]) -> list[str]:
    lines = ["## Test Summary", ""]
    if not summaries:
        lines.extend(["No test summary line was detected.", ""])
        return lines

    for summary in summaries:
        lines.append(f"- {summary}")
    lines.append("")
    return lines


def _render_findings(findings: list[Finding]) -> list[str]:
    lines = ["## Findings", ""]
    if not findings:
        lines.extend(["No high-signal failure lines were detected.", ""])
        return lines

    for number, finding in enumerate(findings, start=1):
        lines.extend(
            [
                f"### {number}. {finding.message}",
                "",
                f"- Severity: `{finding.severity}`",
                f"- Category: `{finding.category}`",
                f"- Line: `{finding.line}`",
                "",
                "```text",
                *finding.context,
                "```",
                "",
            ]
        )

    return lines


def _render_next_steps(next_steps: list[str]) -> list[str]:
    lines = ["## Suggested Next Steps", ""]
    for step in next_steps:
        lines.append(f"- {step}")
    lines.append("")
    return lines
