"""Tests for GraphBuilder."""

from helpers import sample_doc_record as _doc

from sdd_cli.visualizer.analyzer import DependencyAnalyzer
from sdd_cli.visualizer.graph_builder import GraphBuilder


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

    def test_task_with_prd_link_is_prd(self, tmp_path):
        """Task with a link resolving to a requirement goes to PRD graph."""
        req_file = tmp_path / "requirement" / "auth" / "index.md"
        req_file.parent.mkdir(parents=True)
        req_file.write_text("# Auth")

        docs = [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc("specification/auth_spec.md", "spec", "auth", "specification"),
            _doc(
                "task/T-1/index.md",
                "task",
                "T-1",
                "task",
                links=["../../requirement/auth/index.md"],
            ),
        ]
        builder = _make_builder(docs, tmp_path)
        prd_graph, _ = builder.build_split_dependency_graphs()
        prd_ids = {n["id"] for n in prd_graph["nodes"]}
        assert "task/T-1/index.md" in prd_ids

    def test_task_without_prd_link_is_direct(self, tmp_path):
        """Task without links to requirement/PRD spec goes to direct graph."""
        docs = [
            _doc("specification/direct_spec.md", "spec", "direct", "specification"),
            _doc("task/T-2/index.md", "task", "T-2", "task"),
        ]
        builder = _make_builder(docs, tmp_path)
        _, direct_graph = builder.build_split_dependency_graphs()
        direct_ids = {n["id"] for n in direct_graph["nodes"]}
        assert "task/T-2/index.md" in direct_ids

    def test_design_follows_prd_spec(self, tmp_path):
        """Design doc follows its spec's classification into PRD graph."""
        docs = [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc("specification/auth_spec.md", "spec", "auth", "specification"),
            _doc("specification/auth_design.md", "design", "auth", "specification"),
        ]
        builder = _make_builder(docs, tmp_path)
        prd_graph, _ = builder.build_split_dependency_graphs()
        prd_ids = {n["id"] for n in prd_graph["nodes"]}
        assert "specification/auth_design.md" in prd_ids

    def test_design_follows_direct_spec(self, tmp_path):
        """Design doc follows its spec's classification into direct graph."""
        docs = [
            _doc("specification/direct_spec.md", "spec", "direct", "specification"),
            _doc("specification/direct_design.md", "design", "direct", "specification"),
        ]
        builder = _make_builder(docs, tmp_path)
        _, direct_graph = builder.build_split_dependency_graphs()
        direct_ids = {n["id"] for n in direct_graph["nodes"]}
        assert "specification/direct_design.md" in direct_ids

    def test_design_without_spec_is_direct(self, tmp_path):
        """Design doc without any spec goes to direct graph."""
        docs = [
            _doc("specification/orphan_design.md", "design", "orphan", "specification"),
        ]
        builder = _make_builder(docs, tmp_path)
        _, direct_graph = builder.build_split_dependency_graphs()
        direct_ids = {n["id"] for n in direct_graph["nodes"]}
        assert "specification/orphan_design.md" in direct_ids

    def test_split_with_filter_dir(self, tmp_path):
        """filter_dir filters output graph but does not affect PRD classification."""
        docs = [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc("specification/auth_spec.md", "spec", "auth", "specification"),
            _doc("specification/direct_spec.md", "spec", "direct", "specification"),
        ]
        builder = _make_builder(docs, tmp_path)
        prd_graph, direct_graph = builder.build_split_dependency_graphs(filter_dir="specification")

        # requirement is excluded by filter_dir, but auth_spec is still PRD-classified
        prd_ids = {n["id"] for n in prd_graph["nodes"] if n["id"] != "CONSTITUTION.md"}
        assert "specification/auth_spec.md" in prd_ids
        assert "requirement/auth/index.md" not in prd_ids

        direct_ids = {n["id"] for n in direct_graph["nodes"] if n["id"] != "CONSTITUTION.md"}
        assert "specification/direct_spec.md" in direct_ids
