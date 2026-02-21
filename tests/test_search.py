"""Tests for search command implementation."""

import json

import pytest
from helpers import sample_doc_info, sample_parsed_data

from sdd_cli.commands.search import _format_text_results, search_documents
from sdd_cli.indexer.db import IndexDB

# ---------------------------------------------------------------------------
# _format_text_results
# ---------------------------------------------------------------------------


class TestFormatTextResults:
    def test_empty_results(self):
        assert _format_text_results([], None) == "No results found."

    def test_with_query(self):
        results = [{"title": "T", "file_path": "a.md", "feature_id": "f"}]
        text = _format_text_results(results, "myquery")
        assert "Query: myquery" in text

    def test_all_fields(self):
        results = [
            {
                "title": "Auth Feature",
                "file_path": "requirement/auth.md",
                "feature_id": "auth",
                "tags": ["security", "core"],
                "snippet": "auth snippet text",
            }
        ]
        text = _format_text_results(results, None)
        assert "Auth Feature" in text
        assert "requirement/auth.md" in text
        assert "auth" in text
        assert "security, core" in text
        assert "auth snippet text" in text

    def test_tags_format(self):
        results = [
            {
                "title": "T",
                "file_path": "a.md",
                "feature_id": "f",
                "tags": ["x", "y", "z"],
            }
        ]
        text = _format_text_results(results, None)
        assert "Tags: x, y, z" in text


# ---------------------------------------------------------------------------
# search_documents integration
# ---------------------------------------------------------------------------


class TestSearchDocuments:
    def test_index_not_found(self, tmp_path):
        sdd_root = tmp_path / ".sdd"
        sdd_root.mkdir()
        with pytest.raises(ValueError, match="Index not found"):
            search_documents(sdd_root, query="test")

    def test_text_format(self, tmp_path):
        # Build index first
        from sdd_cli.cache import get_cache_dir

        project_root = tmp_path
        sdd_root = tmp_path / ".sdd"
        sdd_root.mkdir()

        cache_dir = get_cache_dir(project_root)
        db_path = cache_dir / "index.db"
        with IndexDB(db_path) as db:
            db.index_document(
                sample_doc_info("requirement/auth.md", "auth", "requirement"),
                sample_parsed_data(
                    title="Auth",
                    feature_id="auth",
                    content="Authentication feature",
                ),
            )

        result = search_documents(sdd_root, feature_id="auth", output_format="text")
        assert "Auth" in result
        assert "1 result" in result

    def test_json_format(self, tmp_path):
        from sdd_cli.cache import get_cache_dir

        project_root = tmp_path
        sdd_root = tmp_path / ".sdd"
        sdd_root.mkdir()

        cache_dir = get_cache_dir(project_root)
        db_path = cache_dir / "index.db"
        with IndexDB(db_path) as db:
            db.index_document(
                sample_doc_info("requirement/auth.md", "auth", "requirement"),
                sample_parsed_data(title="Auth", feature_id="auth", content="Auth content"),
            )

        result = search_documents(sdd_root, feature_id="auth", output_format="json")
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["feature_id"] == "auth"
