"""Regression tests for the lint command across test-project fixtures."""

import json
from pathlib import Path

import pytest

from sdd_cli.commands.lint import run_lint

_TEST_PROJECTS_DIR = Path(__file__).resolve().parent.parent / "test-project"

_TEST_PROJECTS = [
    "01-default-config",
    "02-custom-dirs",
    "03-custom-root",
    "04-partial-config",
    "05-nested-features",
    "06-minimal",
    "07-multi-feature",
    "08-lint-errors",
]

_ENV_VARS = ["SDD_ROOT", "SDD_REQUIREMENT_DIR", "SDD_SPECIFICATION_DIR", "SDD_TASK_DIR"]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove SDD environment variables to ensure consistent results."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def _load_expected(project_name: str) -> dict:
    """Load lint_expected.json for a project."""
    path = _TEST_PROJECTS_DIR / project_name / "lint_expected.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("project_name", _TEST_PROJECTS)
def test_lint_regression(project_name):
    project_dir = _TEST_PROJECTS_DIR / project_name
    output, _has_errors = run_lint(project_dir, json_output=True, quiet=False)
    actual = json.loads(output)
    expected = _load_expected(project_name)

    assert actual["error_count"] == expected["error_count"], (
        f"{project_name}: error_count mismatch: got {actual['error_count']}, expected {expected['error_count']}"
    )
    assert actual["warning_count"] == expected["warning_count"], (
        f"{project_name}: warning_count mismatch: got {actual['warning_count']}, expected {expected['warning_count']}"
    )
    assert actual["files_checked"] == expected["files_checked"], (
        f"{project_name}: files_checked mismatch: got {actual['files_checked']}, expected {expected['files_checked']}"
    )
    assert len(actual["issues"]) == len(expected["issues"]), (
        f"{project_name}: issue count mismatch: got {len(actual['issues'])}, expected {len(expected['issues'])}"
    )
    for i, (act, exp) in enumerate(zip(actual["issues"], expected["issues"])):
        assert act == exp, f"{project_name}: issue #{i} mismatch at {exp.get('file_path')}"
