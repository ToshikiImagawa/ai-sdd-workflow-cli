"""Tests for GraphBuilder."""

from pathlib import Path
from typing import Optional

from sdd_cli.types import DocumentRecord
from sdd_cli.visualizer.analyzer import DependencyAnalyzer
from sdd_cli.visualizer.graph_builder import GraphBuilder


def _doc(
    file_path: str,
    file_type: str = "requirement",
    feature_id: str = "feat",
    directory: str = "requirement",
    depends_on: Optional[list[str]] = None,
    links: Optional[list[str]] = None,
    parent_feature_id: Optional[str] = None,
    title: Optional[str] = None,
    file_name: Optional[str] = None,
) -> DocumentRecord:
    """Helper to build a document dict for graph builder tests."""
    return DocumentRecord(
        file_path=file_path,
        file_name=file_name or Path(file_path).stem,
        directory=directory,
        file_type=file_type,
        feature_id=feature_id,
        title=title or Path(file_path).stem,
        depends_on=depends_on or [],
        links=links or [],
        parent_feature_id=parent_feature_id,
        tags=[],
    )


def _make_builder(docs, tmp_path):
    """Helper to create analyzer + builder pair."""
    analyzer = DependencyAnalyzer(docs, tmp_path)
    deps = analyzer.analyze()
    return GraphBuilder(docs, deps, analyzer)


# ---------------------------------------------------------------------------
# build_dependency_graph
# ---------------------------------------------------------------------------


class TestBuildDependencyGraph:
    def test_constitution_node(self, tmp_path):
        docs = [_doc("requirement/a.md", "requirement", "a")]
        builder = _make_builder(docs, tmp_path)
        graph = builder.build_dependency_graph()
        node_ids = [n["id"] for n in graph["nodes"]]
        assert "CONSTITUTION.md" in node_ids

    def test_filter_dir(self, tmp_path):
        docs = [
            _doc("requirement/a.md", "requirement", "a"),
            _doc("specification/a_spec.md", "spec", "a", "specification"),
        ]
        builder = _make_builder(docs, tmp_path)
        graph = builder.build_dependency_graph(filter_dir="requirement")
        doc_nodes = [n for n in graph["nodes"] if n["id"] != "CONSTITUTION.md"]
        assert all(n["directory"] == "requirement" for n in doc_nodes)

    def test_filter_feature_id(self, tmp_path):
        docs = [
            _doc("requirement/a.md", "requirement", "a"),
            _doc("requirement/b.md", "requirement", "b"),
        ]
        builder = _make_builder(docs, tmp_path)
        graph = builder.build_dependency_graph(feature_id="a")
        doc_nodes = [n for n in graph["nodes"] if n["id"] != "CONSTITUTION.md"]
        assert len(doc_nodes) == 1
        assert doc_nodes[0]["feature_id"] == "a"


# ---------------------------------------------------------------------------
# build_split_dependency_graphs
# ---------------------------------------------------------------------------


class TestSplitDependencyGraphs:
    def _make_docs(self):
        return [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc("specification/auth_spec.md", "spec", "auth", "specification"),
            _doc("specification/direct_spec.md", "spec", "direct", "specification"),
        ]

    def test_prd_based_contains_requirement(self, tmp_path):
        docs = self._make_docs()
        builder = _make_builder(docs, tmp_path)
        prd_graph, _ = builder.build_split_dependency_graphs()
        prd_ids = {n["id"] for n in prd_graph["nodes"]}
        assert "requirement/auth/index.md" in prd_ids

    def test_direct_contains_no_requirement(self, tmp_path):
        docs = self._make_docs()
        builder = _make_builder(docs, tmp_path)
        _, direct_graph = builder.build_split_dependency_graphs()
        direct_ids = {n["id"] for n in direct_graph["nodes"]}
        assert "requirement/auth/index.md" not in direct_ids

    def test_spec_with_requirement_is_prd(self, tmp_path):
        docs = self._make_docs()
        builder = _make_builder(docs, tmp_path)
        prd_graph, _ = builder.build_split_dependency_graphs()
        prd_ids = {n["id"] for n in prd_graph["nodes"]}
        assert "specification/auth_spec.md" in prd_ids

    def test_spec_without_requirement_is_direct(self, tmp_path):
        docs = self._make_docs()
        builder = _make_builder(docs, tmp_path)
        _, direct_graph = builder.build_split_dependency_graphs()
        direct_ids = {n["id"] for n in direct_graph["nodes"]}
        assert "specification/direct_spec.md" in direct_ids
