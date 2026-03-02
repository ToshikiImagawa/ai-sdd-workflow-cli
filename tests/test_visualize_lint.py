"""Integration tests for visualize command lint integration."""

from __future__ import annotations

import json
from pathlib import Path

from helpers import write_md

from sdd_cli.commands.visualize import _build_graph_data
from sdd_cli.linter.core import group_issues_by_file, run_lint_issues
from sdd_cli.types import DependencyGraph, GraphEdge, GraphNode, LintIssue


def _make_graph(nodes: list[GraphNode], edges: list[GraphEdge]) -> DependencyGraph:
    """Create a minimal DependencyGraph."""
    return DependencyGraph(nodes=nodes, edges=edges)


class TestBuildGraphDataLint:
    """Tests for _build_graph_data with lint issues."""

    def test_no_lint_issues(self):
        """lintIssues should be empty dict when no issues."""
        graph = _make_graph(
            nodes=[
                GraphNode(
                    id="requirement/a.md",
                    title="A",
                    file_type="requirement",
                    directory="requirement",
                    feature_id="a",
                    links=[],
                )
            ],
            edges=[],
        )
        data = json.loads(_build_graph_data(graph, "title", "subtitle"))
        assert "lintIssues" in data
        assert data["lintIssues"] == {}

    def test_with_lint_issues(self):
        """lintIssues should contain issues grouped by file_path."""
        graph = _make_graph(
            nodes=[
                GraphNode(
                    id="requirement/a.md",
                    title="A",
                    file_type="requirement",
                    directory="requirement",
                    feature_id="a",
                    links=[],
                )
            ],
            edges=[],
        )
        lint_issues = {
            "requirement/a.md": [
                LintIssue(
                    severity="error",
                    rule="broken-link",
                    file_path="requirement/a.md",
                    line=10,
                    message="Link target not found",
                    details=None,
                )
            ]
        }
        data = json.loads(_build_graph_data(graph, "title", "subtitle", lint_issues))
        assert "lintIssues" in data
        assert "requirement/a.md" in data["lintIssues"]
        issue = data["lintIssues"]["requirement/a.md"][0]
        assert issue["severity"] == "error"
        assert issue["rule"] == "broken-link"
        assert issue["message"] == "Link target not found"
        assert issue["line"] == 10

    def test_lint_issues_serializable_fields_only(self):
        """Only severity, rule, message, line are included (not file_path, details)."""
        graph = _make_graph(nodes=[], edges=[])
        lint_issues = {
            "req/a.md": [
                LintIssue(
                    severity="warning",
                    rule="missing-field",
                    file_path="req/a.md",
                    line=None,
                    message="Missing field",
                    details="some detail",
                )
            ]
        }
        data = json.loads(_build_graph_data(graph, "t", "s", lint_issues))
        issue = data["lintIssues"]["req/a.md"][0]
        assert set(issue.keys()) == {"severity", "rule", "message", "line"}
        assert issue["line"] is None


class TestVisualizeLintIntegration:
    """Integration: lint results flow into visualize JSON data."""

    def test_lint_issues_from_project(self, tmp_path: Path):
        """run_lint_issues result can be passed to _build_graph_data."""
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
                "depends-on": ["nonexistent"],
            },
            body="# Auth\n",
        )

        result = run_lint_issues(tmp_path)
        grouped = group_issues_by_file(result["issues"])

        graph = _make_graph(
            nodes=[
                GraphNode(
                    id="requirement/auth.md",
                    title="Auth",
                    file_type="requirement",
                    directory="requirement",
                    feature_id="auth",
                    links=[],
                )
            ],
            edges=[],
        )

        data = json.loads(_build_graph_data(graph, "title", "subtitle", grouped))
        assert "lintIssues" in data
        # The project has an unresolved dependency, so there should be at least 1 issue
        total_issues = sum(len(v) for v in data["lintIssues"].values())
        assert total_issues > 0
