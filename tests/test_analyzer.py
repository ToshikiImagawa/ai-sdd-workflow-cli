"""Tests for DependencyAnalyzer."""

from pathlib import Path
from typing import Optional

from sdd_cli.types import DocumentRecord
from sdd_cli.visualizer.analyzer import DependencyAnalyzer


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
    """Helper to build a document dict for analyzer tests."""
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


# ---------------------------------------------------------------------------
# analyze(): explicit dependencies
# ---------------------------------------------------------------------------


class TestExplicitDeps:
    def test_explicit_dep_resolved(self, tmp_path):
        docs = [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc("specification/auth_spec.md", "spec", "auth", "specification", depends_on=["auth"]),
        ]
        analyzer = DependencyAnalyzer(docs, tmp_path)
        deps = analyzer.analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        assert ("specification/auth_spec.md", "requirement/auth/index.md") in explicit

    def test_unresolved_explicit_dep_ignored(self, tmp_path):
        docs = [_doc("requirement/a.md", depends_on=["nonexistent"])]
        analyzer = DependencyAnalyzer(docs, tmp_path)
        deps = analyzer.analyze()
        explicit = [d for d in deps if d[2] == "explicit"]
        assert explicit == []


# ---------------------------------------------------------------------------
# analyze(): implicit dependencies
# ---------------------------------------------------------------------------


class TestImplicitDeps:
    def test_requirement_to_spec(self, tmp_path):
        docs = [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc("specification/auth_spec.md", "spec", "auth", "specification"),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        implicit = [(s, t) for s, t, lt in deps if lt == "implicit"]
        assert ("requirement/auth/index.md", "specification/auth_spec.md") in implicit

    def test_spec_to_design(self, tmp_path):
        docs = [
            _doc("specification/auth_spec.md", "spec", "auth", "specification"),
            _doc("specification/auth_design.md", "design", "auth", "specification"),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        implicit = [(s, t) for s, t, lt in deps if lt == "implicit"]
        assert ("specification/auth_spec.md", "specification/auth_design.md") in implicit

    def test_design_to_task(self, tmp_path):
        docs = [
            _doc("specification/auth_design.md", "design", "auth", "specification"),
            _doc("task/TICKET-1/index.md", "task", "auth", "task"),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        implicit = [(s, t) for s, t, lt in deps if lt == "implicit"]
        assert ("specification/auth_design.md", "task/TICKET-1/index.md") in implicit

    def test_no_implicit_for_unknown(self, tmp_path):
        docs = [_doc("other/x.md", "unknown", "x", "other")]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        implicit = [d for d in deps if d[2] == "implicit"]
        assert implicit == []


# ---------------------------------------------------------------------------
# analyze(): parent-child
# ---------------------------------------------------------------------------


class TestParentChild:
    def test_parent_child_edge(self, tmp_path):
        docs = [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc("requirement/auth/login.md", "requirement", "login", parent_feature_id="auth"),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        pc = [(s, t) for s, t, lt in deps if s == "requirement/auth/index.md" and t == "requirement/auth/login.md"]
        assert len(pc) == 1

    def test_no_parent_no_edge(self, tmp_path):
        docs = [_doc("requirement/auth/index.md", "requirement", "auth")]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        assert all(d[2] != "parent-child" for d in deps if d[0] == "requirement/auth/index.md")

    def test_parent_not_found(self, tmp_path):
        docs = [_doc("requirement/auth/login.md", "requirement", "login", parent_feature_id="missing")]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        # No parent-child implicit edges should be added
        pc = [(s, t, lt) for s, t, lt in deps if lt == "implicit" and t == "requirement/auth/login.md"]
        assert pc == []


# ---------------------------------------------------------------------------
# analyze(): link dependencies (task only)
# ---------------------------------------------------------------------------


class TestLinkDeps:
    def test_task_link_resolved(self, tmp_path):
        # Create actual files for resolution
        req_file = tmp_path / "requirement" / "auth" / "index.md"
        req_file.parent.mkdir(parents=True)
        req_file.write_text("# Auth")

        docs = [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc(
                "task/T-1/index.md",
                "task",
                "T-1",
                "task",
                links=["../../requirement/auth/index.md"],
            ),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        link_deps = [(s, t) for s, t, lt in deps if lt == "link"]
        assert ("task/T-1/index.md", "requirement/auth/index.md") in link_deps

    def test_non_task_links_ignored(self, tmp_path):
        docs = [
            _doc("requirement/a.md", "requirement", "a", links=["../b.md"]),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        link_deps = [d for d in deps if d[2] == "link"]
        assert link_deps == []

    def test_unresolvable_link_ignored(self, tmp_path):
        docs = [
            _doc("task/T-1/index.md", "task", "T-1", "task", links=["../../nonexistent.md"]),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        link_deps = [d for d in deps if d[2] == "link"]
        assert link_deps == []


# ---------------------------------------------------------------------------
# _filter_to_leaf_targets
# ---------------------------------------------------------------------------


class TestFilterToLeafTargets:
    def test_single_target(self, tmp_path):
        analyzer = DependencyAnalyzer([], tmp_path)
        assert analyzer._filter_to_leaf_targets(["a"]) == ["a"]

    def test_empty(self, tmp_path):
        analyzer = DependencyAnalyzer([], tmp_path)
        assert analyzer._filter_to_leaf_targets([]) == []

    def test_filters_ancestor(self, tmp_path):
        # Setup: A→B implicit, both in targets → only B should remain
        docs = [
            _doc("requirement/a.md", "requirement", "feat"),
            _doc("specification/a_spec.md", "spec", "feat", "specification"),
        ]
        analyzer = DependencyAnalyzer(docs, tmp_path)
        analyzer.analyze()  # populates self.dependencies
        result = analyzer._filter_to_leaf_targets(
            [
                "requirement/a.md",
                "specification/a_spec.md",
            ]
        )
        assert "specification/a_spec.md" in result
        assert "requirement/a.md" not in result


# ---------------------------------------------------------------------------
# get_dependency_graph
# ---------------------------------------------------------------------------


class TestGetDependencyGraph:
    def test_constitution_node(self, tmp_path):
        docs = [_doc("requirement/a.md", "requirement", "a")]
        analyzer = DependencyAnalyzer(docs, tmp_path)
        analyzer.analyze()
        graph = analyzer.get_dependency_graph()
        node_ids = [n["id"] for n in graph["nodes"]]
        assert "CONSTITUTION.md" in node_ids

    def test_filter_dir(self, tmp_path):
        docs = [
            _doc("requirement/a.md", "requirement", "a"),
            _doc("specification/a_spec.md", "spec", "a", "specification"),
        ]
        analyzer = DependencyAnalyzer(docs, tmp_path)
        analyzer.analyze()
        graph = analyzer.get_dependency_graph(filter_dir="requirement")
        doc_nodes = [n for n in graph["nodes"] if n["id"] != "CONSTITUTION.md"]
        assert all(n["directory"] == "requirement" for n in doc_nodes)

    def test_filter_feature_id(self, tmp_path):
        docs = [
            _doc("requirement/a.md", "requirement", "a"),
            _doc("requirement/b.md", "requirement", "b"),
        ]
        analyzer = DependencyAnalyzer(docs, tmp_path)
        analyzer.analyze()
        graph = analyzer.get_dependency_graph(feature_id="a")
        doc_nodes = [n for n in graph["nodes"] if n["id"] != "CONSTITUTION.md"]
        assert len(doc_nodes) == 1
        assert doc_nodes[0]["feature_id"] == "a"


# ---------------------------------------------------------------------------
# get_split_dependency_graphs
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
        analyzer = DependencyAnalyzer(docs, tmp_path)
        analyzer.analyze()
        prd_graph, _ = analyzer.get_split_dependency_graphs()
        prd_ids = {n["id"] for n in prd_graph["nodes"]}
        assert "requirement/auth/index.md" in prd_ids

    def test_direct_contains_no_requirement(self, tmp_path):
        docs = self._make_docs()
        analyzer = DependencyAnalyzer(docs, tmp_path)
        analyzer.analyze()
        _, direct_graph = analyzer.get_split_dependency_graphs()
        direct_ids = {n["id"] for n in direct_graph["nodes"]}
        assert "requirement/auth/index.md" not in direct_ids

    def test_spec_with_requirement_is_prd(self, tmp_path):
        docs = self._make_docs()
        analyzer = DependencyAnalyzer(docs, tmp_path)
        analyzer.analyze()
        prd_graph, _ = analyzer.get_split_dependency_graphs()
        prd_ids = {n["id"] for n in prd_graph["nodes"]}
        assert "specification/auth_spec.md" in prd_ids

    def test_spec_without_requirement_is_direct(self, tmp_path):
        docs = self._make_docs()
        analyzer = DependencyAnalyzer(docs, tmp_path)
        analyzer.analyze()
        _, direct_graph = analyzer.get_split_dependency_graphs()
        direct_ids = {n["id"] for n in direct_graph["nodes"]}
        assert "specification/direct_spec.md" in direct_ids
