"""Unit tests for sdd_cli.linter.core module."""

from __future__ import annotations

from pathlib import Path

from helpers import write_md

from sdd_cli.linter.core import (
    extract_cycle_edges,
    extract_unresolved_deps,
    group_issues_by_file,
    run_lint_issues,
)
from sdd_cli.types import LintIssue


class TestRunLintIssues:
    """Tests for run_lint_issues()."""

    def test_no_sdd_root(self, tmp_path: Path):
        """Returns empty result when .sdd/ does not exist."""
        result = run_lint_issues(tmp_path)
        assert result["issues"] == []
        assert result["error_count"] == 0
        assert result["warning_count"] == 0
        assert result["files_checked"] == 0

    def test_valid_project(self, tmp_path: Path):
        """Returns result with 0 issues for a valid project."""
        sdd = tmp_path / ".sdd"
        req = sdd / "requirement"
        spec = sdd / "specification"
        req.mkdir(parents=True)
        spec.mkdir(parents=True)

        write_md(
            req / "auth.md",
            frontmatter={
                "id": "prd-auth",
                "title": "Auth",
                "type": "prd",
                "status": "draft",
                "created": "2026-01-01",
                "updated": "2026-01-01",
            },
            body="# Auth\n",
        )
        write_md(
            spec / "auth_spec.md",
            frontmatter={
                "id": "spec-auth",
                "title": "Auth Spec",
                "type": "spec",
                "status": "draft",
                "created": "2026-01-01",
                "updated": "2026-01-01",
                "depends-on": ["prd-auth"],
            },
            body="# Auth Spec\n",
        )

        result = run_lint_issues(tmp_path)
        assert result["files_checked"] >= 2
        assert result["error_count"] == 0

    def test_detects_unresolved_dependency(self, tmp_path: Path):
        """Detects unresolved-dependency issues."""
        sdd = tmp_path / ".sdd"
        req = sdd / "requirement"
        req.mkdir(parents=True)

        write_md(
            req / "auth.md",
            frontmatter={
                "id": "prd-auth",
                "title": "Auth",
                "type": "prd",
                "status": "draft",
                "created": "2026-01-01",
                "updated": "2026-01-01",
                "depends-on": ["nonexistent-id"],
            },
            body="# Auth\n",
        )

        result = run_lint_issues(tmp_path)
        assert len(result["issues"]) > 0
        rules = [i["rule"] for i in result["issues"]]
        assert "unresolved-dependency" in rules


class TestGroupIssuesByFile:
    """Tests for group_issues_by_file()."""

    def test_empty_list(self):
        assert group_issues_by_file([]) == {}

    def test_groups_correctly(self):
        issues: list[LintIssue] = [
            LintIssue(
                severity="error",
                rule="broken-link",
                file_path="requirement/a.md",
                line=1,
                message="msg1",
                details=None,
            ),
            LintIssue(
                severity="warning",
                rule="missing-field",
                file_path="requirement/b.md",
                line=2,
                message="msg2",
                details=None,
            ),
            LintIssue(
                severity="error",
                rule="broken-link",
                file_path="requirement/a.md",
                line=3,
                message="msg3",
                details=None,
            ),
        ]
        grouped = group_issues_by_file(issues)
        assert len(grouped) == 2
        assert len(grouped["requirement/a.md"]) == 2
        assert len(grouped["requirement/b.md"]) == 1


class TestExtractCycleEdges:
    """Tests for extract_cycle_edges()."""

    def test_empty_list(self):
        assert extract_cycle_edges([]) == []

    def test_extracts_edges(self):
        issues: list[LintIssue] = [
            LintIssue(
                severity="error",
                rule="circular-dependency",
                file_path="requirement/a.md",
                line=None,
                message="Circular dependency detected",
                details="prd-a -> prd-b -> prd-a",
            ),
        ]
        edges = extract_cycle_edges(issues)
        assert ("prd-a", "prd-b") in edges
        assert ("prd-b", "prd-a") in edges

    def test_deduplicates_cycles(self):
        """Same cycle reported from different files should not produce duplicates."""
        issues: list[LintIssue] = [
            LintIssue(
                severity="error",
                rule="circular-dependency",
                file_path="requirement/a.md",
                line=None,
                message="Circular dependency detected",
                details="prd-a -> prd-b -> prd-a",
            ),
            LintIssue(
                severity="error",
                rule="circular-dependency",
                file_path="requirement/b.md",
                line=None,
                message="Circular dependency detected",
                details="prd-a -> prd-b -> prd-a",
            ),
        ]
        edges = extract_cycle_edges(issues)
        assert len(edges) == 2  # Only one cycle's edges


class TestExtractUnresolvedDeps:
    """Tests for extract_unresolved_deps()."""

    def test_empty_list(self):
        assert extract_unresolved_deps([]) == []

    def test_extracts_pairs(self):
        issues: list[LintIssue] = [
            LintIssue(
                severity="error",
                rule="unresolved-dependency",
                file_path="requirement/a.md",
                line=None,
                message="Unresolved depends-on reference: nonexistent-id",
                details=None,
            ),
        ]
        result = extract_unresolved_deps(issues)
        assert result == [("requirement/a.md", "nonexistent-id")]

    def test_ignores_other_rules(self):
        issues: list[LintIssue] = [
            LintIssue(
                severity="error",
                rule="broken-link",
                file_path="requirement/a.md",
                line=None,
                message="Unresolved depends-on reference: foo",
                details=None,
            ),
        ]
        result = extract_unresolved_deps(issues)
        assert result == []
