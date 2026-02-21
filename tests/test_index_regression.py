"""Regression tests for the index command pipeline (Scanner -> Parser -> IndexDB)."""

import json
from pathlib import Path

import pytest

from sdd_cli.config import resolve_config
from sdd_cli.indexer.db import IndexDB
from sdd_cli.indexer.parser import DocumentParser
from sdd_cli.indexer.scanner import DocumentScanner

_TEST_PROJECTS_DIR = Path(__file__).resolve().parent.parent / "test-project"

# (project_name, sdd_root_name)
_TEST_PROJECTS = [
    ("01-default-config", ".sdd"),
    ("02-custom-dirs", ".sdd"),
    ("03-custom-root", "docs"),
    ("04-partial-config", ".sdd"),
    ("05-nested-features", ".sdd"),
    ("06-minimal", ".sdd"),
    ("07-multi-feature", ".sdd"),
]

_ENV_VARS = ["SDD_ROOT", "SDD_REQUIREMENT_DIR", "SDD_SPECIFICATION_DIR", "SDD_TASK_DIR"]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove SDD environment variables to ensure consistent results."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def _build_and_get_documents(project_name: str, sdd_root_name: str, tmp_path: Path) -> list[dict]:
    """Run Scanner -> Parser -> IndexDB pipeline and return all documents."""
    project_dir = _TEST_PROJECTS_DIR / project_name
    sdd_root = project_dir / sdd_root_name

    config = resolve_config(project_dir)
    scanner = DocumentScanner(sdd_root, directories=config["directories"])
    scan_results = scanner.scan_all()

    db_path = tmp_path / "index.db"
    with IndexDB(db_path) as db:
        for doc_info in scan_results:
            parsed_data = DocumentParser.parse(doc_info["full_path"])
            db.index_document(doc_info, parsed_data)
        return [dict(doc) for doc in db.get_all_documents()]


def _load_expected(project_name: str) -> list[dict]:
    """Load expected.json for a project."""
    path = _TEST_PROJECTS_DIR / project_name / "expected.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("project_name,sdd_root_name", _TEST_PROJECTS)
def test_index_regression(project_name, sdd_root_name, tmp_path):
    actual = _build_and_get_documents(project_name, sdd_root_name, tmp_path)
    expected = _load_expected(project_name)

    assert len(actual) == len(expected), (
        f"{project_name}: document count mismatch: got {len(actual)}, expected {len(expected)}"
    )

    for i, (act, exp) in enumerate(zip(actual, expected)):
        assert act == exp, f"{project_name}: document #{i} mismatch at file_path={exp.get('file_path')}"
