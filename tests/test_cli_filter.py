"""CLI integration tests for --filter / --or / --parent options (TASK-011)."""

import json

import pytest
from click.testing import CliRunner
from helpers import sample_doc_info, sample_parsed_data

from sdd_cli.cli import main as cli
from sdd_cli.indexer.db import IndexDB


@pytest.fixture
def project_with_index(tmp_path):
    """Create a project with a pre-built index containing test documents."""
    from sdd_cli.cache import get_cache_dir

    root = tmp_path / "project"
    root.mkdir()

    cache_dir = get_cache_dir(root)
    db_path = cache_dir / "index.db"

    with IndexDB(db_path) as db:
        db.index_document(
            sample_doc_info("requirement/auth/index.md", "index", "requirement"),
            sample_parsed_data(
                title="Auth Feature",
                feature_id="auth",
                doc_type="prd",
                status="approved",
                category="feature",
                tags=["security"],
                content="Authentication feature.",
            ),
        )
        db.index_document(
            sample_doc_info("specification/auth_spec.md", "auth_spec", "specification"),
            sample_parsed_data(
                title="Auth Spec",
                feature_id="auth",
                file_type="spec",
                doc_type="spec",
                status="draft",
                category="feature",
                tags=["security"],
                content="Auth specification.",
            ),
        )
        db.index_document(
            sample_doc_info("requirement/search/index.md", "index", "requirement"),
            sample_parsed_data(
                title="Search Feature",
                feature_id="search",
                file_type="requirement",
                doc_type="prd",
                status="approved",
                category="feature",
                tags=["fts5"],
                content="Search feature.",
            ),
        )
        db.index_document(
            sample_doc_info("requirement/child.md", "child", "requirement"),
            sample_parsed_data(
                title="Auth Child",
                feature_id="auth-child",
                parent_feature_id="auth",
                file_type="requirement",
                doc_type="prd",
                status="draft",
                content="Child of auth.",
            ),
        )

    return root


# ---------------------------------------------------------------------------
# TASK-011: CLI --filter / --or / --parent 統合テスト
# ---------------------------------------------------------------------------


class TestSearchFilterCLI:
    def test_filter_exact_match(self, project_with_index):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["search", "--root", str(project_with_index), "--filter", "status:exact:approved"],
        )
        assert result.exit_code == 0
        assert "Found" in result.output

    def test_filter_no_match(self, project_with_index):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["search", "--root", str(project_with_index), "--filter", "status:exact:nonexistent"],
        )
        assert result.exit_code == 0
        assert "No results found." in result.output

    def test_filter_or_flag(self, project_with_index):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "search",
                "--root",
                str(project_with_index),
                "--filter",
                "type:exact:prd",
                "--filter",
                "type:exact:spec",
                "--or",
            ],
        )
        assert result.exit_code == 0
        assert "Found" in result.output

    def test_parent_flag(self, project_with_index):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["search", "--root", str(project_with_index), "--parent", "auth"],
        )
        assert result.exit_code == 0
        # auth-child should be in results
        assert "auth-child" in result.output or "Auth Child" in result.output

    def test_filter_regex(self, project_with_index):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["search", "--root", str(project_with_index), "--filter", "feature_id:regex:^auth"],
        )
        assert result.exit_code == 0
        assert "Found" in result.output

    def test_filter_invalid_format(self, project_with_index):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["search", "--root", str(project_with_index), "--filter", "bad-format"],
        )
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_filter_invalid_field(self, project_with_index):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["search", "--root", str(project_with_index), "--filter", "invalid_field:exact:x"],
        )
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_filter_json_output(self, project_with_index):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "search",
                "--root",
                str(project_with_index),
                "--filter",
                "status:exact:approved",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert all(d["status"] == "approved" for d in data)

    def test_search_help_shows_new_options(self, project_with_index):
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "--filter" in result.output
        assert "--or" in result.output
        assert "--parent" in result.output
