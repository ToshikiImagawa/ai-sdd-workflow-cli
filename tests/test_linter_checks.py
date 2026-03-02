"""Tests for sdd_cli.linter.checks module."""

from __future__ import annotations

from pathlib import Path

from helpers import sample_doc_record, sample_parsed_data, write_md

from sdd_cli.linter.checks import (
    check_broken_links,
    check_circular_dependencies,
    check_id_integrity,
    check_required_fields,
)

# ── check_circular_dependencies ──────────────────────────────────────


class TestCheckCircularDependencies:
    def test_no_cycles(self):
        docs = [
            sample_doc_record("requirement/a.md", doc_id="prd-a", depends_on=[]),
            sample_doc_record("specification/b_spec.md", doc_id="spec-b", depends_on=["prd-a"]),
        ]
        issues = check_circular_dependencies(docs)
        assert issues == []

    def test_simple_cycle(self):
        docs = [
            sample_doc_record("requirement/a.md", doc_id="prd-a", depends_on=["spec-b"]),
            sample_doc_record("specification/b_spec.md", doc_id="spec-b", depends_on=["prd-a"]),
        ]
        issues = check_circular_dependencies(docs)
        assert len(issues) >= 1
        assert issues[0]["severity"] == "error"
        assert issues[0]["rule"] == "circular-dependency"

    def test_self_reference(self):
        docs = [
            sample_doc_record("requirement/a.md", doc_id="prd-a", depends_on=["prd-a"]),
        ]
        issues = check_circular_dependencies(docs)
        assert len(issues) >= 1
        assert issues[0]["rule"] == "circular-dependency"

    def test_unresolved_id_skipped(self):
        docs = [
            sample_doc_record("requirement/a.md", doc_id="prd-a", depends_on=["nonexistent-x"]),
        ]
        issues = check_circular_dependencies(docs)
        assert issues == []

    def test_empty_documents(self):
        issues = check_circular_dependencies([])
        assert issues == []


# ── check_broken_links ───────────────────────────────────────────────


class TestCheckBrokenLinks:
    def test_valid_link(self, tmp_path: Path):
        sdd_root = tmp_path / ".sdd"
        req_dir = sdd_root / "requirement"
        req_dir.mkdir(parents=True)
        write_md(req_dir / "a.md", body="# A")
        write_md(req_dir / "b.md", body="# B\n\n[link](a.md)")

        docs = [
            sample_doc_record(
                "requirement/b.md",
                doc_id="prd-b",
                links=["a.md"],
                directory="requirement",
            ),
        ]
        issues = check_broken_links(docs, sdd_root)
        assert issues == []

    def test_broken_link(self, tmp_path: Path):
        sdd_root = tmp_path / ".sdd"
        req_dir = sdd_root / "requirement"
        req_dir.mkdir(parents=True)
        write_md(req_dir / "b.md", body="# B\n\n[link](missing.md)")

        docs = [
            sample_doc_record(
                "requirement/b.md",
                doc_id="prd-b",
                links=["missing.md"],
                directory="requirement",
            ),
        ]
        issues = check_broken_links(docs, sdd_root)
        assert len(issues) == 1
        assert issues[0]["severity"] == "error"
        assert issues[0]["rule"] == "broken-link"
        assert issues[0]["line"] is not None

    def test_external_url_skipped(self, tmp_path: Path):
        sdd_root = tmp_path / ".sdd"
        (sdd_root / "requirement").mkdir(parents=True)
        write_md(sdd_root / "requirement" / "a.md", body="# A")

        docs = [
            sample_doc_record(
                "requirement/a.md",
                doc_id="prd-a",
                links=["https://example.com/doc.md"],
                directory="requirement",
            ),
        ]
        issues = check_broken_links(docs, sdd_root)
        assert issues == []

    def test_path_traversal_detection(self, tmp_path: Path):
        sdd_root = tmp_path / ".sdd"
        (sdd_root / "requirement").mkdir(parents=True)
        write_md(sdd_root / "requirement" / "a.md", body="# A\n\n[link](../../etc/passwd)")

        docs = [
            sample_doc_record(
                "requirement/a.md",
                doc_id="prd-a",
                links=["../../etc/passwd"],
                directory="requirement",
            ),
        ]
        issues = check_broken_links(docs, sdd_root)
        assert len(issues) >= 1
        assert issues[0]["severity"] == "error"

    def test_empty_documents(self, tmp_path: Path):
        sdd_root = tmp_path / ".sdd"
        sdd_root.mkdir(parents=True)
        issues = check_broken_links([], sdd_root)
        assert issues == []


# ── check_required_fields ────────────────────────────────────────────


class TestCheckRequiredFields:
    def test_all_fields_present_prd(self):
        docs = [
            sample_doc_record(
                "requirement/a.md",
                doc_id="prd-a",
                doc_type="prd",
                status="draft",
                created="2026-01-01",
                updated="2026-01-01",
                title="Test PRD",
            ),
        ]
        issues = check_required_fields(docs)
        assert issues == []

    def test_missing_required_field(self):
        docs = [
            sample_doc_record(
                "requirement/a.md",
                doc_id="prd-a",
                doc_type="prd",
                status=None,
                created="2026-01-01",
                updated="2026-01-01",
                title="Test PRD",
            ),
        ]
        issues = check_required_fields(docs)
        assert len(issues) >= 1
        assert issues[0]["rule"] == "missing-required-field"
        assert issues[0]["severity"] == "warning"

    def test_invalid_status_value(self):
        docs = [
            sample_doc_record(
                "requirement/a.md",
                doc_id="prd-a",
                doc_type="prd",
                status="invalid-status",
                created="2026-01-01",
                updated="2026-01-01",
                title="Test PRD",
            ),
        ]
        issues = check_required_fields(docs)
        field_issues = [i for i in issues if i["rule"] == "invalid-field-value"]
        assert len(field_issues) >= 1
        assert field_issues[0]["severity"] == "warning"

    def test_design_missing_impl_status(self):
        docs = [
            sample_doc_record(
                "specification/a_design.md",
                doc_id="design-a",
                doc_type="design",
                status="draft",
                created="2026-01-01",
                updated="2026-01-01",
                title="Test Design",
                file_type="design",
            ),
        ]
        issues = check_required_fields(docs)
        missing = [i for i in issues if "impl-status" in i["message"]]
        assert len(missing) >= 1

    def test_empty_documents(self):
        issues = check_required_fields([])
        assert issues == []


# ── check_id_integrity ───────────────────────────────────────────────


class TestCheckIdIntegrity:
    def test_no_issues(self):
        docs = [
            sample_doc_record("requirement/a.md", doc_id="prd-a", depends_on=[]),
            sample_doc_record("specification/b_spec.md", doc_id="spec-b", depends_on=["prd-a"]),
        ]
        parsed = [
            sample_parsed_data(doc_id="prd-a", content="# Requirements"),
            sample_parsed_data(doc_id="spec-b", content="# Spec"),
        ]
        issues = check_id_integrity(docs, parsed)
        assert issues == []

    def test_duplicate_id(self):
        docs = [
            sample_doc_record("requirement/a.md", doc_id="prd-a"),
            sample_doc_record("requirement/b.md", doc_id="prd-a"),
        ]
        parsed = [
            sample_parsed_data(doc_id="prd-a", content="# A"),
            sample_parsed_data(doc_id="prd-a", content="# B"),
        ]
        issues = check_id_integrity(docs, parsed)
        dup_issues = [i for i in issues if i["rule"] == "duplicate-id"]
        assert len(dup_issues) >= 1
        assert dup_issues[0]["severity"] == "error"

    def test_unresolved_dependency(self):
        docs = [
            sample_doc_record("specification/a_spec.md", doc_id="spec-a", depends_on=["prd-nonexistent"]),
        ]
        parsed = [
            sample_parsed_data(doc_id="spec-a", content="# Spec"),
        ]
        issues = check_id_integrity(docs, parsed)
        unresolved = [i for i in issues if i["rule"] == "unresolved-dependency"]
        assert len(unresolved) >= 1
        assert unresolved[0]["severity"] == "warning"

    def test_orphan_reference(self):
        docs = [
            sample_doc_record("requirement/a.md", doc_id="prd-a", directory="requirement", file_type="requirement"),
            sample_doc_record("specification/b_spec.md", doc_id="spec-b", directory="specification", file_type="spec"),
        ]
        parsed = [
            sample_parsed_data(
                doc_id="prd-a", content="# Requirements\n\nFR-001: Login feature", file_type="requirement"
            ),
            sample_parsed_data(doc_id="spec-b", content="# Spec\n\nThis covers FR-001 and FR-099.", file_type="spec"),
        ]
        issues = check_id_integrity(docs, parsed)
        orphan = [i for i in issues if i["rule"] == "orphan-reference"]
        assert len(orphan) >= 1
        assert "FR-099" in orphan[0]["message"]

    def test_code_block_excluded(self):
        docs = [
            sample_doc_record("requirement/a.md", doc_id="prd-a", directory="requirement", file_type="requirement"),
            sample_doc_record("specification/b_spec.md", doc_id="spec-b", directory="specification", file_type="spec"),
        ]
        parsed = [
            sample_parsed_data(doc_id="prd-a", content="# Requirements\n\nFR-001: Login", file_type="requirement"),
            sample_parsed_data(
                doc_id="spec-b",
                content="# Spec\n\nThis covers FR-001.\n\n```\nFR-999 in code block\n```",
                file_type="spec",
            ),
        ]
        issues = check_id_integrity(docs, parsed)
        orphan = [i for i in issues if i["rule"] == "orphan-reference" and "FR-999" in i["message"]]
        assert len(orphan) == 0

    def test_empty_documents(self):
        issues = check_id_integrity([], [])
        assert issues == []
