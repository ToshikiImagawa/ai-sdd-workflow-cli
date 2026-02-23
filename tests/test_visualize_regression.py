"""Regression tests for the visualize pipeline (Scanner -> Parser -> IndexDB -> Analyzer -> GraphBuilder)."""

import json
from pathlib import Path

import pytest

from sdd_cli.config import resolve_config
from sdd_cli.indexer.db import IndexDB
from sdd_cli.indexer.parser import DocumentParser
from sdd_cli.indexer.scanner import DocumentScanner
from sdd_cli.visualizer.analyzer import DependencyAnalyzer
from sdd_cli.visualizer.graph_builder import GraphBuilder

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


def _build_graphs(project_name: str, sdd_root_name: str, tmp_path: Path) -> dict:
    """Run full visualize pipeline and return all three graphs."""
    project_dir = _TEST_PROJECTS_DIR / project_name
    sdd_root = project_dir / sdd_root_name

    config = resolve_config(project_dir)
    scanner = DocumentScanner(sdd_root, directories=config["directories"])
    scan_results = scanner.scan_all()

    db_path = tmp_path / "index.db"
    with IndexDB(db_path) as db:
        for doc_info in scan_results:
            parsed_data = DocumentParser.parse(
                doc_info["full_path"],
                directory=doc_info["directory"],
                rel_path=doc_info["file_path"],
            )
            db.index_document(doc_info, parsed_data)
        documents = db.get_all_documents()

    analyzer = DependencyAnalyzer(documents, sdd_root)
    deps = analyzer.analyze()
    builder = GraphBuilder(documents, deps, analyzer)

    dependency_graph = builder.build_dependency_graph()
    prd_based_graph, direct_graph = builder.build_split_dependency_graphs()

    return {
        "dependency_graph": _normalize_graph(dependency_graph),
        "prd_based_graph": _normalize_graph(prd_based_graph),
        "direct_graph": _normalize_graph(direct_graph),
    }


def _normalize_graph(graph: dict) -> dict:
    """Sort nodes and edges for stable comparison."""
    return {
        "nodes": sorted(graph["nodes"], key=lambda n: n["id"]),
        "edges": sorted(graph["edges"], key=lambda e: (e["source"], e["target"], e["type"])),
    }


def _load_expected(project_name: str) -> dict:
    """Load visualize_expected.json for a project."""
    path = _TEST_PROJECTS_DIR / project_name / "visualize_expected.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("project_name,sdd_root_name", _TEST_PROJECTS)
def test_visualize_regression(project_name, sdd_root_name, tmp_path):
    actual = _build_graphs(project_name, sdd_root_name, tmp_path)
    expected = _load_expected(project_name)

    for graph_key in ("dependency_graph", "prd_based_graph", "direct_graph"):
        actual_graph = actual[graph_key]
        expected_graph = expected[graph_key]

        assert len(actual_graph["nodes"]) == len(expected_graph["nodes"]), (
            f"{project_name}/{graph_key}: node count mismatch: "
            f"got {len(actual_graph['nodes'])}, expected {len(expected_graph['nodes'])}"
        )

        for i, (act, exp) in enumerate(zip(actual_graph["nodes"], expected_graph["nodes"])):
            assert act == exp, f"{project_name}/{graph_key}: node #{i} mismatch at id={exp.get('id')}"

        assert len(actual_graph["edges"]) == len(expected_graph["edges"]), (
            f"{project_name}/{graph_key}: edge count mismatch: "
            f"got {len(actual_graph['edges'])}, expected {len(expected_graph['edges'])}"
        )

        for i, (act, exp) in enumerate(zip(actual_graph["edges"], expected_graph["edges"])):
            assert act == exp, (
                f"{project_name}/{graph_key}: edge #{i} mismatch: "
                f"got {act}, expected {exp}"
            )
