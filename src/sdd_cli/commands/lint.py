"""Lint command for SDD document static analysis."""

from __future__ import annotations

from pathlib import Path

from sdd_cli.linter.core import run_lint_issues
from sdd_cli.linter.formatter import format_issues
from sdd_cli.types import LintResult


def run_lint(root: Path, json_output: bool, quiet: bool) -> tuple[str, bool]:
    """Core lint logic. Testable entry point.

    Processing flow:
    1. Delegate to run_lint_issues() for scanning, parsing, and checking
    2. Format the result with format_issues()
    3. If quiet=True and 0 issues, return empty string

    Returns:
        Tuple of (formatted output, whether error-level issues exist)
    """
    result: LintResult = run_lint_issues(root)

    if quiet and result["error_count"] == 0 and result["warning_count"] == 0:
        return ("", False)

    output = format_issues(result, json_output)
    return (output, result["error_count"] > 0)
