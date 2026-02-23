"""Tests for IndexDB."""

from sqlite3 import ProgrammingError

import pytest
from helpers import sample_doc_info, sample_parsed_data

from sdd_cli.indexer.db import IndexDB

# ---------------------------------------------------------------------------
# Table creation / context manager / clear
# ---------------------------------------------------------------------------


class TestDBSetup:
    def test_tables_created(self, index_db):
        cursor = index_db.conn.cursor()
        # FTS5 virtual table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents_fts'")
        assert cursor.fetchone() is not None

        # Metadata table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents_meta'")
        assert cursor.fetchone() is not None

    def test_context_manager(self, tmp_path):
        db_path = tmp_path / "ctx.db"
        with IndexDB(db_path) as db:
            db.index_document(sample_doc_info(), sample_parsed_data())
        # After __exit__, connection is closed
        with pytest.raises(ProgrammingError):
            db.conn.execute("SELECT 1")

    def test_clear(self, index_db):
        index_db.index_document(sample_doc_info(), sample_parsed_data())
        assert len(index_db.get_all_documents()) == 1
        index_db.clear()
        assert len(index_db.get_all_documents()) == 0

    def test_parent_dir_created(self, tmp_path):
        db_path = tmp_path / "sub" / "dir" / "index.db"
        db = IndexDB(db_path)
        assert db_path.parent.exists()
        db.close()


# ---------------------------------------------------------------------------
# index_document
# ---------------------------------------------------------------------------


class TestIndexDocument:
    def test_insert(self, index_db):
        index_db.index_document(sample_doc_info(), sample_parsed_data())
        docs = index_db.get_all_documents()
        assert len(docs) == 1
        assert docs[0]["file_path"] == "requirement/auth/index.md"
        assert docs[0]["title"] == "Auth Feature"

    def test_json_fields_stored(self, index_db):
        parsed = sample_parsed_data(tags=["a", "b"], depends_on=["x"], links=["y.md"])
        index_db.index_document(sample_doc_info(), parsed)
        docs = index_db.get_all_documents()
        assert docs[0]["tags"] == ["a", "b"]
        assert docs[0]["depends_on"] == ["x"]
        assert docs[0]["links"] == ["y.md"]

    def test_upsert_meta(self, index_db):
        doc = sample_doc_info()
        index_db.index_document(doc, sample_parsed_data(title="V1"))
        index_db.index_document(doc, sample_parsed_data(title="V2"))
        # FTS will have 2 rows (INSERT only), but meta should be upserted
        cursor = index_db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents_meta")
        assert cursor.fetchone()[0] == 1


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class TestSearch:
    @pytest.fixture(autouse=True)
    def _seed(self, index_db):
        """Seed two documents for search tests."""
        index_db.index_document(
            sample_doc_info("requirement/auth/index.md", "index", "requirement"),
            sample_parsed_data(
                title="Auth Feature",
                feature_id="auth",
                file_type="requirement",
                tags=["security", "core"],
                content="Authentication and authorization flow.",
            ),
        )
        index_db.index_document(
            sample_doc_info("specification/auth_spec.md", "auth_spec", "specification"),
            sample_parsed_data(
                title="Auth Spec",
                feature_id="auth",
                file_type="spec",
                tags=["security"],
                content="Detailed specification for auth module.",
            ),
        )

    def test_fts_query(self, index_db):
        results = index_db.search(query="authentication")
        assert len(results) >= 1
        assert any(r["feature_id"] == "auth" for r in results)

    def test_filter_feature_id(self, index_db):
        results = index_db.search(feature_id="auth")
        assert len(results) == 2

    def test_filter_tag(self, index_db):
        results = index_db.search(tag="core")
        assert len(results) == 1
        assert results[0]["title"] == "Auth Feature"

    def test_filter_directory(self, index_db):
        results = index_db.search(directory="specification")
        assert len(results) == 1
        assert results[0]["file_path"] == "specification/auth_spec.md"

    def test_combined_filters(self, index_db):
        results = index_db.search(feature_id="auth", directory="requirement")
        assert len(results) == 1

    def test_limit(self, index_db):
        results = index_db.search(limit=1)
        assert len(results) == 1

    def test_no_results(self, index_db):
        results = index_db.search(query="nonexistentterm12345")
        assert results == []


# ---------------------------------------------------------------------------
# get_all_documents
# ---------------------------------------------------------------------------


class TestGetAllDocuments:
    def test_empty_db(self, index_db):
        assert index_db.get_all_documents() == []

    def test_all_fields(self, index_db):
        index_db.index_document(
            sample_doc_info(),
            sample_parsed_data(
                parent_feature_id="root",
                tags=["t1"],
                depends_on=["d1"],
                links=["l.md"],
            ),
        )
        doc = index_db.get_all_documents()[0]
        assert doc["parent_feature_id"] == "root"
        assert doc["tags"] == ["t1"]
        assert doc["depends_on"] == ["d1"]
        assert doc["links"] == ["l.md"]

    def test_invalid_json_fallback(self, index_db):
        index_db.index_document(sample_doc_info(), sample_parsed_data())
        # Corrupt the tags JSON in metadata
        index_db.conn.execute(
            "UPDATE documents_meta SET tags='not-json' WHERE file_path=?",
            ("requirement/auth/index.md",),
        )
        index_db.conn.commit()
        doc = index_db.get_all_documents()[0]
        assert doc["tags"] == []


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestClose:
    def test_close_then_operate(self, tmp_path):
        db = IndexDB(tmp_path / "close.db")
        db.close()
        with pytest.raises(ProgrammingError):
            db.conn.execute("SELECT 1")
