"""Regression tests for the search pipeline (Scanner -> Parser -> IndexDB -> search)."""

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


def _build_index(project_name: str, sdd_root_name: str, tmp_path: Path) -> IndexDB:
    """Run Scanner -> Parser -> IndexDB pipeline and return open IndexDB."""
    project_dir = _TEST_PROJECTS_DIR / project_name
    sdd_root = project_dir / sdd_root_name

    config = resolve_config(project_dir)
    scanner = DocumentScanner(sdd_root, directories=config["directories"])
    scan_results = scanner.scan_all()

    db_path = tmp_path / "index.db"
    db = IndexDB(db_path)
    for doc_info in scan_results:
        parsed_data = DocumentParser.parse(doc_info["full_path"])
        db.index_document(doc_info, parsed_data)
    return db


def _load_search_expected(project_name: str) -> list[dict]:
    """Load search_expected.json for a project."""
    path = _TEST_PROJECTS_DIR / project_name / "search_expected.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _strip_snippet(result: dict) -> dict:
    """Remove snippet and rank fields from a search result for comparison."""
    return {k: v for k, v in result.items() if k not in ("snippet", "rank")}


@pytest.mark.parametrize("project_name,sdd_root_name", _TEST_PROJECTS)
def test_search_regression(project_name, sdd_root_name, tmp_path):
    db = _build_index(project_name, sdd_root_name, tmp_path)
    try:
        scenarios = _load_search_expected(project_name)

        for scenario in scenarios:
            name = scenario["name"]
            params = scenario["params"]
            expected_results = scenario["results"]

            actual_raw = db.search(**params)
            actual = [_strip_snippet(dict(r)) for r in actual_raw]

            assert len(actual) == len(expected_results), (
                f"{project_name}/{name}: result count mismatch: got {len(actual)}, expected {len(expected_results)}"
            )

            for i, (act, exp) in enumerate(zip(actual, expected_results)):
                assert act == exp, f"{project_name}/{name}: result #{i} mismatch at file_path={exp.get('file_path')}"

            # snippet が存在することを検証 (query ありの場合は snippet が返るはず)
            if params.get("query"):
                for r in actual_raw:
                    assert r.get("snippet") is not None, (
                        f"{project_name}/{name}: snippet should exist for query results"
                    )
    finally:
        db.close()
