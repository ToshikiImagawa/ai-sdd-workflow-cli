"""Tests for sdd_cli.linter.formatter module."""

from __future__ import annotations

import json

from sdd_cli.linter.formatter import format_issues
from sdd_cli.types import LintIssue, LintResult


def _make_result(issues: list[LintIssue] | None = None) -> LintResult:
    issues = issues or []
    return LintResult(
        issues=issues,
        error_count=sum(1 for i in issues if i["severity"] == "error"),
        warning_count=sum(1 for i in issues if i["severity"] == "warning"),
        files_checked=5,
    )


class TestFormatIssues:
    def test_text_format_with_issues(self):
        issues: list[LintIssue] = [
            LintIssue(
                severity="error",
                rule="circular-dependency",
                file_path=".sdd/requirement/a.md",
                line=None,
                message="Circular dependency detected: a.md → b.md → a.md",
                details="a.md → b.md → a.md",
            ),
            LintIssue(
                severity="warning",
                rule="missing-required-field",
                file_path=".sdd/specification/old_design.md",
                line=None,
                message="Required field 'impl-status' is missing for document type 'design'",
                details=None,
            ),
        ]
        result = _make_result(issues)
        output = format_issues(result, json_output=False)

        assert "ERROR" in output
        assert "circular-dependency" in output
        assert "WARNING" in output
        assert "missing-required-field" in output
        assert "1 error" in output.lower() or "1 errors" in output.lower()
        assert "1 warning" in output.lower() or "1 warnings" in output.lower()

    def test_json_format(self):
        issues: list[LintIssue] = [
            LintIssue(
                severity="error",
                rule="broken-link",
                file_path=".sdd/specification/auth_spec.md",
                line=42,
                message="Link target does not exist: ../requirement/missing.md",
                details="../requirement/missing.md",
            ),
        ]
        result = _make_result(issues)
        output = format_issues(result, json_output=True)

        data = json.loads(output)
        assert data["error_count"] == 1
        assert data["warning_count"] == 0
        assert len(data["issues"]) == 1
        assert data["issues"][0]["rule"] == "broken-link"

    def test_empty_issues_text(self):
        result = _make_result([])
        output = format_issues(result, json_output=False)

        assert "0 error" in output.lower() or "0 errors" in output.lower()

    def test_empty_issues_json(self):
        result = _make_result([])
        output = format_issues(result, json_output=True)

        data = json.loads(output)
        assert data["issues"] == []
        assert data["error_count"] == 0

    def test_line_number_in_text(self):
        issues: list[LintIssue] = [
            LintIssue(
                severity="error",
                rule="broken-link",
                file_path=".sdd/specification/auth_spec.md",
                line=42,
                message="Link target does not exist",
                details=None,
            ),
        ]
        result = _make_result(issues)
        output = format_issues(result, json_output=False)

        assert ":42" in output
