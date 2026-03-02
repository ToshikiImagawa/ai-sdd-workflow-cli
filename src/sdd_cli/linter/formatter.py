"""Output formatter for lint results."""

from __future__ import annotations

import json

from sdd_cli.types import LintResult


def format_issues(
    result: LintResult,
    json_output: bool,
) -> str:
    """Format LintResult as text or JSON string."""
    if json_output:
        return _format_json(result)
    return _format_text(result)


def _format_text(result: LintResult) -> str:
    """Format LintResult as human-readable text."""
    lines: list[str] = []

    for issue in result["issues"]:
        severity = issue["severity"].upper()
        rule = issue["rule"]
        file_path = issue["file_path"]
        line = issue.get("line")
        message = issue["message"]

        location = f"{file_path}:{line}" if line else file_path
        lines.append(f"{severity} {rule} {location}")
        lines.append(f"  {message}")
        lines.append("")

    error_count = result["error_count"]
    warning_count = result["warning_count"]
    files_checked = result["files_checked"]
    lines.append(f"Found {error_count} errors, {warning_count} warnings in {files_checked} files")

    return "\n".join(lines)


def _format_json(result: LintResult) -> str:
    """Format LintResult as JSON string."""
    return json.dumps(dict(result), indent=2, ensure_ascii=False)
