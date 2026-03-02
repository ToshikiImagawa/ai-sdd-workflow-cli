"""Tests for DependencyAnalyzer."""

from helpers import sample_doc_record as _doc

from sdd_cli.visualizer.analyzer import DependencyAnalyzer

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

    def test_design_depends_on_resolves_to_spec(self, tmp_path):
        """design depends_on [auth] → auth spec (direct parent type)."""
        docs = [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc("specification/auth_spec.md", "spec", "auth", "specification"),
            _doc("specification/auth_design.md", "design", "auth", "specification"),
            _doc("specification/pay_design.md", "design", "pay", "specification", depends_on=["auth"]),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        assert ("specification/pay_design.md", "specification/auth_spec.md") in explicit

    def test_design_depends_on_skips_to_requirement(self, tmp_path):
        """design depends_on [auth] → auth requirement when no spec exists."""
        docs = [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc("specification/pay_design.md", "design", "pay", "specification", depends_on=["auth"]),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        assert ("specification/pay_design.md", "requirement/auth/index.md") in explicit

    def test_task_depends_on_resolves_to_same_level(self, tmp_path):
        """task depends_on [AUTH-001] → AUTH-001 task (fallback to first match)."""
        docs = [
            _doc("task/AUTH-001/index.md", "task", "AUTH-001", "task"),
            _doc("task/PAY-001/index.md", "task", "PAY-001", "task", depends_on=["AUTH-001"]),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        assert ("task/PAY-001/index.md", "task/AUTH-001/index.md") in explicit


# ---------------------------------------------------------------------------
# analyze(): implicit dependencies
# ---------------------------------------------------------------------------


class TestImplicitDeps:
    def test_spec_depends_on_requirement(self, tmp_path):
        docs = [
            _doc("requirement/auth/index.md", "requirement", "auth"),
            _doc("specification/auth_spec.md", "spec", "auth", "specification"),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        implicit = [(s, t) for s, t, lt in deps if lt == "implicit"]
        assert ("specification/auth_spec.md", "requirement/auth/index.md") in implicit

    def test_design_depends_on_spec(self, tmp_path):
        docs = [
            _doc("specification/auth_spec.md", "spec", "auth", "specification"),
            _doc("specification/auth_design.md", "design", "auth", "specification"),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        implicit = [(s, t) for s, t, lt in deps if lt == "implicit"]
        assert ("specification/auth_design.md", "specification/auth_spec.md") in implicit

    def test_no_implicit_design_to_task(self, tmp_path):
        """Task is excluded from implicit dependencies (connected via link edges only)."""
        docs = [
            _doc("specification/auth_design.md", "design", "auth", "specification"),
            _doc("task/TICKET-1/index.md", "task", "auth", "task"),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        implicit = [(s, t) for s, t, lt in deps if lt == "implicit"]
        assert ("specification/auth_design.md", "task/TICKET-1/index.md") not in implicit

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
        pc = [(s, t) for s, t, lt in deps if s == "requirement/auth/login.md" and t == "requirement/auth/index.md"]
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

    def test_order_independent_with_task_first(self, tmp_path):
        """Task doc listed first in documents should not affect _filter_to_leaf_targets.

        Before the 2-pass fix, if a task doc appeared before its spec/req targets
        in self.documents, _filter_to_leaf_targets would run with incomplete
        dependency data and fail to remove ancestors.
        """
        # Create files for link resolution
        req_file = tmp_path / "requirement" / "auth.md"
        req_file.parent.mkdir(parents=True)
        req_file.write_text("# Auth")
        spec_file = tmp_path / "specification" / "auth_spec.md"
        spec_file.parent.mkdir(parents=True)
        spec_file.write_text("# Auth Spec")

        # Task doc listed FIRST (before spec/requirement)
        docs = [
            _doc(
                "task/T-1/index.md",
                "task",
                "T-1",
                "task",
                links=["../../requirement/auth.md", "../../specification/auth_spec.md"],
            ),
            _doc("requirement/auth.md", "requirement", "auth"),
            _doc("specification/auth_spec.md", "spec", "auth", "specification"),
        ]
        analyzer = DependencyAnalyzer(docs, tmp_path)
        deps = analyzer.analyze()
        link_deps = [(s, t) for s, t, lt in deps if lt == "link"]

        # spec→requirement is an implicit edge, so requirement is an ancestor.
        # _filter_to_leaf_targets should keep only spec.
        assert ("task/T-1/index.md", "specification/auth_spec.md") in link_deps
        assert ("task/T-1/index.md", "requirement/auth.md") not in link_deps


# ---------------------------------------------------------------------------
# analyze(): depends-on with full document ID (prefixed)
# ---------------------------------------------------------------------------


class TestFullIdDependsOn:
    """depends-on に prd-xxx / spec-xxx 等のフルIDが記載された場合のテスト."""

    def test_spec_depends_on_prd_prefixed_id(self, tmp_path):
        """spec depends_on ["prd-auth"] → requirement/auth.md に解決される."""
        docs = [
            _doc("requirement/auth.md", "requirement", "auth", doc_id="prd-auth"),
            _doc(
                "specification/auth_spec.md",
                "spec",
                "auth",
                "specification",
                depends_on=["prd-auth"],
                doc_id="spec-auth",
            ),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        assert ("specification/auth_spec.md", "requirement/auth.md") in explicit

    def test_design_depends_on_spec_prefixed_id(self, tmp_path):
        """design depends_on ["spec-auth"] → specification/auth_spec.md に解決される."""
        docs = [
            _doc("requirement/auth.md", "requirement", "auth", doc_id="prd-auth"),
            _doc("specification/auth_spec.md", "spec", "auth", "specification", doc_id="spec-auth"),
            _doc(
                "specification/auth_design.md",
                "design",
                "auth",
                "specification",
                depends_on=["spec-auth"],
                doc_id="design-auth",
            ),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        assert ("specification/auth_design.md", "specification/auth_spec.md") in explicit

    def test_prd_depends_on_prd_prefixed_id(self, tmp_path):
        """requirement depends_on ["prd-overview"] → requirement 同士の依存."""
        docs = [
            _doc("requirement/overview.md", "requirement", "overview", doc_id="prd-overview"),
            _doc(
                "requirement/auth.md",
                "requirement",
                "auth",
                depends_on=["prd-overview"],
                doc_id="prd-auth",
            ),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        assert ("requirement/auth.md", "requirement/overview.md") in explicit

    def test_cross_feature_with_prefixed_id(self, tmp_path):
        """design depends_on ["spec-sale-state"] (cross-feature, prefixed ID)."""
        docs = [
            _doc("specification/sale-state_spec.md", "spec", "sale-state", "specification", doc_id="spec-sale-state"),
            _doc(
                "specification/sale-state-display_design.md",
                "design",
                "sale-state-display",
                "specification",
                depends_on=["spec-sale-state"],
                doc_id="design-sale-state-display",
            ),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        assert ("specification/sale-state-display_design.md", "specification/sale-state_spec.md") in explicit


# ---------------------------------------------------------------------------
# analyze(): transitive redundant edge removal for explicit edges
# ---------------------------------------------------------------------------


class TestTransitiveExplicitEdgeRemoval:
    def test_transitive_explicit_removed(self, tmp_path):
        """A→B→C chain: A depends_on [B, C] → A→C is redundant and removed."""
        docs = [
            _doc("requirement/c.md", "requirement", "c"),
            _doc("requirement/b.md", "requirement", "b", depends_on=["c"]),
            _doc("requirement/a.md", "requirement", "a", depends_on=["b", "c"]),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        assert ("requirement/a.md", "requirement/b.md") in explicit
        assert ("requirement/a.md", "requirement/c.md") not in explicit

    def test_non_transitive_explicit_preserved(self, tmp_path):
        """A→B, A→C (no B→C relation) → both preserved."""
        docs = [
            _doc("requirement/b.md", "requirement", "b"),
            _doc("requirement/c.md", "requirement", "c"),
            _doc("requirement/a.md", "requirement", "a", depends_on=["b", "c"]),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        assert ("requirement/a.md", "requirement/b.md") in explicit
        assert ("requirement/a.md", "requirement/c.md") in explicit

    def test_transitive_via_implicit_removes_explicit(self, tmp_path):
        """pay_spec→pay_req(implicit), pay_req→auth_req(explicit), pay_spec→auth_req(explicit)
        → pay_spec→auth_req is redundant (reachable via pay_req)."""
        docs = [
            _doc("requirement/auth.md", "requirement", "auth"),
            _doc("requirement/pay.md", "requirement", "pay", depends_on=["auth"]),
            _doc(
                "specification/pay_spec.md",
                "spec",
                "pay",
                "specification",
                depends_on=["auth"],
            ),
        ]
        deps = DependencyAnalyzer(docs, tmp_path).analyze()
        explicit = [(s, t) for s, t, lt in deps if lt == "explicit"]
        # pay_spec has implicit→pay_req and explicit→auth_req
        # pay_req has explicit→auth_req
        # Chain: pay_spec→pay_req→auth_req, so pay_spec→auth_req is redundant
        assert ("requirement/pay.md", "requirement/auth.md") in explicit
        assert ("specification/pay_spec.md", "requirement/auth.md") not in explicit
