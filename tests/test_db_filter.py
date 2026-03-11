"""Tests for IndexDB filter DSL, REGEXP UDF, and get_descendants() (FR-014~018)."""

import pytest
from helpers import sample_doc_info, sample_parsed_data

from sdd_cli.indexer.db import IndexDB
from sdd_cli.types import FilterCondition

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db(tmp_path):
    """IndexDB backed by a temp SQLite file with seeded documents."""
    db_path = tmp_path / "filter_test.db"
    d = IndexDB(db_path)
    yield d
    d.close()


@pytest.fixture(autouse=False)
def seeded_db(db):
    """Seed 4 documents for filter tests."""
    db.index_document(
        sample_doc_info("requirement/auth/index.md", "index", "requirement"),
        sample_parsed_data(
            title="Auth Feature",
            feature_id="auth",
            file_type="requirement",
            tags=["security", "core"],
            doc_type="prd",
            status="approved",
            category="feature",
            content="Authentication and authorization flow.",
        ),
    )
    db.index_document(
        sample_doc_info("specification/auth_spec.md", "auth_spec", "specification"),
        sample_parsed_data(
            title="Auth Spec",
            feature_id="auth",
            file_type="spec",
            tags=["security"],
            doc_type="spec",
            status="draft",
            category="feature",
            content="Detailed specification for auth module.",
        ),
    )
    db.index_document(
        sample_doc_info("specification/auth_design.md", "auth_design", "specification"),
        sample_parsed_data(
            title="Auth Design",
            feature_id="auth",
            file_type="design",
            tags=["security", "design"],
            doc_type="design",
            status="draft",
            category="feature",
            content="Technical design for auth module.",
        ),
    )
    db.index_document(
        sample_doc_info("requirement/search/index.md", "index", "requirement"),
        sample_parsed_data(
            title="Search Feature",
            feature_id="search",
            file_type="requirement",
            tags=["search", "fts5"],
            doc_type="prd",
            status="approved",
            category="feature",
            content="Full text search feature.",
        ),
    )
    return db


# ---------------------------------------------------------------------------
# TASK-007: FilterCondition / MatchOp 型定義テスト
# ---------------------------------------------------------------------------


class TestFilterConditionType:
    def test_create_filter_condition(self):
        cond: FilterCondition = FilterCondition(field="status", op="exact", value="draft")
        assert cond["field"] == "status"
        assert cond["op"] == "exact"
        assert cond["value"] == "draft"

    def test_all_match_ops(self):
        for op in ("exact", "contains", "regex"):
            cond = FilterCondition(field="type", op=op, value="spec")
            assert cond["op"] == op


# ---------------------------------------------------------------------------
# TASK-008: get_descendants() テスト
# ---------------------------------------------------------------------------


class TestGetDescendants:
    @pytest.fixture(autouse=True)
    def _seed_hierarchy(self, db):
        """Seed a 3-level hierarchy: root -> child1, child2 -> grandchild."""
        db.index_document(
            sample_doc_info("requirement/root.md", "root", "requirement"),
            sample_parsed_data(feature_id="root", parent_feature_id=None),
        )
        db.index_document(
            sample_doc_info("requirement/child1.md", "child1", "requirement"),
            sample_parsed_data(feature_id="child1", parent_feature_id="root"),
        )
        db.index_document(
            sample_doc_info("requirement/child2.md", "child2", "requirement"),
            sample_parsed_data(feature_id="child2", parent_feature_id="root"),
        )
        db.index_document(
            sample_doc_info("requirement/grandchild.md", "grandchild", "requirement"),
            sample_parsed_data(feature_id="grandchild", parent_feature_id="child1"),
        )

    def test_nonexistent_feature_id_returns_empty(self, db):
        result = db.get_descendants("nonexistent")
        assert result == set()

    def test_single_child(self, db):
        result = db.get_descendants("child1")
        assert result == {"grandchild"}

    def test_all_descendants(self, db):
        result = db.get_descendants("root")
        assert result == {"child1", "child2", "grandchild"}

    def test_self_not_in_result(self, db):
        result = db.get_descendants("root")
        assert "root" not in result

    def test_leaf_node_returns_empty(self, db):
        result = db.get_descendants("grandchild")
        assert result == set()


# ---------------------------------------------------------------------------
# TASK-009: フィルタ DSL テスト (op=exact / contains, AND / OR)
# ---------------------------------------------------------------------------


class TestFilterDSL:
    def test_exact_match(self, seeded_db):
        cond = FilterCondition(field="status", op="exact", value="approved")
        results = seeded_db.search(filters=[cond])
        assert len(results) == 2
        assert all(r["status"] == "approved" for r in results)

    def test_exact_no_match(self, seeded_db):
        cond = FilterCondition(field="status", op="exact", value="nonexistent")
        results = seeded_db.search(filters=[cond])
        assert results == []

    def test_contains_match(self, seeded_db):
        cond = FilterCondition(field="type", op="contains", value="spec")
        results = seeded_db.search(filters=[cond])
        # "spec" and "design" don't contain "spec" in design
        # type values: prd, spec, design -> only "spec" contains "spec"
        assert len(results) >= 1
        assert all("spec" in (r.get("type") or "") for r in results)

    def test_and_multiple_filters(self, seeded_db):
        conds = [
            FilterCondition(field="status", op="exact", value="draft"),
            FilterCondition(field="type", op="exact", value="spec"),
        ]
        results = seeded_db.search(filters=conds)
        assert len(results) == 1
        assert results[0]["title"] == "Auth Spec"

    def test_or_multiple_filters(self, seeded_db):
        conds = [
            FilterCondition(field="type", op="exact", value="prd"),
            FilterCondition(field="type", op="exact", value="spec"),
        ]
        results = seeded_db.search(filters=conds, or_operator=True)
        types = {r.get("type") for r in results}
        assert "prd" in types
        assert "spec" in types
        assert "design" not in types

    def test_or_different_fields(self, seeded_db):
        conds = [
            FilterCondition(field="type", op="exact", value="design"),
            FilterCondition(field="status", op="exact", value="approved"),
        ]
        results = seeded_db.search(filters=conds, or_operator=True)
        # design(draft) OR approved(prd)
        assert len(results) >= 2

    def test_invalid_field_raises(self, seeded_db):
        cond = FilterCondition(field="invalid_field_xyz", op="exact", value="x")
        with pytest.raises(ValueError, match="Invalid filter field"):
            seeded_db.search(filters=[cond])

    def test_no_filters_unchanged_behavior(self, seeded_db):
        results = seeded_db.search(filters=None)
        assert len(results) == 4


# ---------------------------------------------------------------------------
# TASK-010: REGEXP UDF テスト
# ---------------------------------------------------------------------------


class TestRegexpUDF:
    def test_regex_match(self, seeded_db):
        cond = FilterCondition(field="feature_id", op="regex", value="^auth$")
        results = seeded_db.search(filters=[cond])
        assert len(results) == 3
        assert all(r["feature_id"] == "auth" for r in results)

    def test_regex_no_match(self, seeded_db):
        cond = FilterCondition(field="feature_id", op="regex", value="^nonexistent")
        results = seeded_db.search(filters=[cond])
        assert results == []

    def test_regex_prefix_anchor(self, seeded_db):
        cond = FilterCondition(field="feature_id", op="regex", value="^auth")
        results = seeded_db.search(filters=[cond])
        assert all(r["feature_id"].startswith("auth") for r in results)

    def test_invalid_regex_raises(self, seeded_db):
        cond = FilterCondition(field="feature_id", op="regex", value="[invalid")
        with pytest.raises(ValueError, match=r"[Ii]nvalid regex"):
            seeded_db.search(filters=[cond])

    def test_regex_with_none_value(self, seeded_db):
        # parent_feature_id may be None; should not crash
        cond = FilterCondition(field="status", op="regex", value="appro.*")
        results = seeded_db.search(filters=[cond])
        assert len(results) >= 1


# ---------------------------------------------------------------------------
# TASK-008 (additional): --parent flag integration with search()
# ---------------------------------------------------------------------------


class TestParentFilter:
    @pytest.fixture(autouse=True)
    def _seed_hierarchy(self, db):
        db.index_document(
            sample_doc_info("requirement/parent.md", "parent", "requirement"),
            sample_parsed_data(feature_id="parent-feature", parent_feature_id=None),
        )
        db.index_document(
            sample_doc_info("requirement/child.md", "child", "requirement"),
            sample_parsed_data(feature_id="child-feature", parent_feature_id="parent-feature"),
        )
        db.index_document(
            sample_doc_info("specification/child_spec.md", "child_spec", "specification"),
            sample_parsed_data(
                feature_id="child-feature",
                parent_feature_id="parent-feature",
                file_type="spec",
            ),
        )

    def test_parent_returns_descendants(self, db):
        results = db.search(parent="parent-feature")
        feature_ids = {r["feature_id"] for r in results}
        assert "child-feature" in feature_ids

    def test_parent_excludes_self(self, db):
        results = db.search(parent="parent-feature")
        feature_ids = {r["feature_id"] for r in results}
        assert "parent-feature" not in feature_ids

    def test_parent_nonexistent_returns_empty(self, db):
        results = db.search(parent="nonexistent-feature")
        assert results == []
