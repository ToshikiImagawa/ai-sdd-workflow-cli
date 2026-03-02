"""Integration tests for sdd-cli lint command."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from helpers import write_md
from sdd_cli.cli import main
from sdd_cli.commands.lint import run_lint


class TestRunLint:
    def _setup_project(self, tmp_path: Path) -> Path:
        """Create a minimal valid .sdd project."""
        sdd = tmp_path / ".sdd"
        req = sdd / "requirement"
        spec = sdd / "specification"
        req.mkdir(parents=True)
        spec.mkdir(parents=True)

        write_md(
            req / "auth.md",
            frontmatter={"id": "prd-auth", "title": "Auth", "type": "prd", "status": "draft",
                         "created": "2026-01-01", "updated": "2026-01-01"},
            body="# Auth\n\nFR-001: Login feature\n",
        )
        write_md(
            spec / "auth_spec.md",
            frontmatter={"id": "spec-auth", "title": "Auth Spec", "type": "spec", "status": "draft",
                         "created": "2026-01-01", "updated": "2026-01-01",
                         "depends-on": ["prd-auth"]},
            body="# Auth Spec\n\nCovers FR-001.\n\n[auth.md](../requirement/auth.md)\n",
        )
        return tmp_path

    def test_no_issues(self, tmp_path: Path):
        root = self._setup_project(tmp_path)
        output, has_errors = run_lint(root, json_output=False, quiet=False)
        assert not has_errors
        assert "0 errors" in output

    def test_circular_dependency_detected(self, tmp_path: Path):
        sdd = tmp_path / ".sdd"
        req = sdd / "requirement"
        req.mkdir(parents=True)
        write_md(
            req / "a.md",
            frontmatter={"id": "prd-a", "title": "A", "type": "prd", "status": "draft",
                         "created": "2026-01-01", "updated": "2026-01-01",
                         "depends-on": ["prd-b"]},
            body="# A",
        )
        write_md(
            req / "b.md",
            frontmatter={"id": "prd-b", "title": "B", "type": "prd", "status": "draft",
                         "created": "2026-01-01", "updated": "2026-01-01",
                         "depends-on": ["prd-a"]},
            body="# B",
        )
        output, has_errors = run_lint(tmp_path, json_output=False, quiet=False)
        assert has_errors
        assert "circular-dependency" in output

    def test_has_errors_flag(self, tmp_path: Path):
        sdd = tmp_path / ".sdd"
        req = sdd / "requirement"
        req.mkdir(parents=True)
        write_md(
            req / "a.md",
            frontmatter={"id": "prd-a", "title": "A", "type": "prd", "status": "draft",
                         "created": "2026-01-01", "updated": "2026-01-01"},
            body="# A\n\n[missing](missing.md)\n",
        )
        output, has_errors = run_lint(tmp_path, json_output=False, quiet=False)
        assert has_errors

    def test_task_excluded(self, tmp_path: Path):
        sdd = tmp_path / ".sdd"
        req = sdd / "requirement"
        task = sdd / "task" / "TICKET-1"
        req.mkdir(parents=True)
        task.mkdir(parents=True)
        write_md(
            req / "a.md",
            frontmatter={"id": "prd-a", "title": "A", "type": "prd", "status": "draft",
                         "created": "2026-01-01", "updated": "2026-01-01"},
            body="# A",
        )
        write_md(
            task / "tasks.md",
            frontmatter={"id": "task-x", "title": "Task", "type": "task", "status": "pending",
                         "created": "2026-01-01", "updated": "2026-01-01"},
            body="# Tasks",
        )
        output, has_errors = run_lint(tmp_path, json_output=False, quiet=False)
        # task/ should not be counted in checked files
        assert "task-x" not in output

    def test_quiet_no_issues(self, tmp_path: Path):
        root = self._setup_project(tmp_path)
        output, has_errors = run_lint(root, json_output=False, quiet=True)
        assert output == ""
        assert not has_errors

    def test_json_output(self, tmp_path: Path):
        root = self._setup_project(tmp_path)
        output, has_errors = run_lint(root, json_output=True, quiet=False)
        data = json.loads(output)
        assert "issues" in data
        assert "error_count" in data

    def test_no_sdd_directory(self, tmp_path: Path):
        output, has_errors = run_lint(tmp_path, json_output=False, quiet=False)
        assert not has_errors


class TestLintCli:
    def _setup_project(self, tmp_path: Path) -> Path:
        sdd = tmp_path / ".sdd"
        req = sdd / "requirement"
        req.mkdir(parents=True)
        write_md(
            req / "a.md",
            frontmatter={"id": "prd-a", "title": "A", "type": "prd", "status": "draft",
                         "created": "2026-01-01", "updated": "2026-01-01"},
            body="# A",
        )
        return tmp_path

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["lint", "--help"])
        assert result.exit_code == 0
        assert "static analysis" in result.output.lower() or "lint" in result.output.lower()

    def test_no_issues_exit_code_0(self, tmp_path: Path):
        root = self._setup_project(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["lint", "--root", str(root)])
        assert result.exit_code == 0

    def test_error_exit_code_1(self, tmp_path: Path):
        sdd = tmp_path / ".sdd"
        req = sdd / "requirement"
        req.mkdir(parents=True)
        write_md(
            req / "a.md",
            frontmatter={"id": "prd-a", "title": "A", "type": "prd", "status": "draft",
                         "created": "2026-01-01", "updated": "2026-01-01",
                         "depends-on": ["prd-b"]},
            body="# A",
        )
        write_md(
            req / "b.md",
            frontmatter={"id": "prd-b", "title": "B", "type": "prd", "status": "draft",
                         "created": "2026-01-01", "updated": "2026-01-01",
                         "depends-on": ["prd-a"]},
            body="# B",
        )
        runner = CliRunner()
        result = runner.invoke(main, ["lint", "--root", str(tmp_path)])
        assert result.exit_code == 1

    def test_json_flag(self, tmp_path: Path):
        root = self._setup_project(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["lint", "--root", str(root), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "issues" in data

    def test_quiet_flag(self, tmp_path: Path):
        root = self._setup_project(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["lint", "--root", str(root), "--quiet"])
        assert result.exit_code == 0
        assert result.output.strip() == ""
