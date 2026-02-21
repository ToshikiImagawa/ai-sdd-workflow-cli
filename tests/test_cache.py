"""Tests for cache command implementation."""

import json
from pathlib import Path

import pytest

from sdd_cli.cache import get_cache_base
from sdd_cli.commands import cache as commands_cache_mod
from sdd_cli.commands.cache import (
    clean_cache,
    format_cache_list,
    list_cache_projects,
)

# ---------------------------------------------------------------------------
# get_cache_base
# ---------------------------------------------------------------------------


class TestGetCacheBase:
    def test_returns_expected_path(self):
        base = get_cache_base()
        assert base == Path.home() / ".cache" / "sdd-cli"


# ---------------------------------------------------------------------------
# list_cache_projects
# ---------------------------------------------------------------------------


class TestListCacheProjects:
    @pytest.fixture(autouse=True)
    def _patch_base(self, tmp_path, monkeypatch):
        self.cache_base = tmp_path / "cache"
        monkeypatch.setattr(commands_cache_mod, "get_cache_base", lambda: self.cache_base)

    def test_empty_no_dir(self):
        assert list_cache_projects() == []

    def test_normal_project(self):
        proj = self.cache_base / "myproject.abcd1234"
        proj.mkdir(parents=True)
        (proj / "index.db").write_text("data")
        projects = list_cache_projects()
        assert len(projects) == 1
        assert projects[0]["name"] == "myproject"
        assert projects[0]["hash"] == "abcd1234"

    def test_metadata_json(self):
        proj = self.cache_base / "proj.1234abcd"
        proj.mkdir(parents=True)
        meta = {"document_count": 42, "indexed_at": "2024-01-01", "root": "/tmp/proj"}
        (proj / "metadata.json").write_text(json.dumps(meta))
        projects = list_cache_projects()
        assert projects[0]["document_count"] == 42
        assert projects[0]["project_root"] == "/tmp/proj"

    def test_non_directory_skipped(self):
        self.cache_base.mkdir(parents=True)
        (self.cache_base / "not-a-dir.txt").write_text("hi")
        assert list_cache_projects() == []


# ---------------------------------------------------------------------------
# format_cache_list
# ---------------------------------------------------------------------------


class TestFormatCacheList:
    def test_empty(self):
        assert format_cache_list([]) == "No cached projects found."

    def test_single_project(self):
        projects = [
            {
                "name": "proj",
                "hash": "abc",
                "size_bytes": 1024,
                "size_mb": 0.0,
                "document_count": 5,
                "last_modified": "2024-01-01T00:00:00",
                "project_root": "/tmp/proj",
            }
        ]
        text = format_cache_list(projects)
        assert "1 cached project" in text
        assert "proj.abc" in text

    def test_total_size(self):
        projects = [
            {
                "name": "a",
                "hash": "1",
                "size_bytes": 1024 * 1024,
                "size_mb": 1.0,
                "document_count": 1,
                "last_modified": "2024-01-01T00:00:00",
                "project_root": "",
            },
            {
                "name": "b",
                "hash": "2",
                "size_bytes": 2 * 1024 * 1024,
                "size_mb": 2.0,
                "document_count": 2,
                "last_modified": "2024-01-01T00:00:00",
                "project_root": "",
            },
        ]
        text = format_cache_list(projects)
        assert "3.0 MB" in text


# ---------------------------------------------------------------------------
# clean_cache
# ---------------------------------------------------------------------------


class TestCleanCache:
    @pytest.fixture(autouse=True)
    def _patch_base(self, tmp_path, monkeypatch):
        self.cache_base = tmp_path / "cache"
        monkeypatch.setattr(commands_cache_mod, "get_cache_base", lambda: self.cache_base)

    def test_no_cache_dir(self):
        result = clean_cache(all_projects=True)
        assert "No cache directory" in result

    def test_all_delete(self):
        proj = self.cache_base / "proj.1234abcd"
        proj.mkdir(parents=True)
        (proj / "index.db").write_text("data")
        result = clean_cache(all_projects=True)
        assert "Deleted 1 project" in result
        assert not proj.exists()

    def test_pattern_match(self):
        (self.cache_base / "alpha.1111").mkdir(parents=True)
        (self.cache_base / "alpha.1111" / "f.db").write_text("x")
        (self.cache_base / "beta.2222").mkdir(parents=True)
        (self.cache_base / "beta.2222" / "f.db").write_text("x")
        result = clean_cache(project_pattern="alpha")
        assert "Deleted 1 project" in result
        assert not (self.cache_base / "alpha.1111").exists()
        assert (self.cache_base / "beta.2222").exists()

    def test_dry_run(self):
        proj = self.cache_base / "proj.abcd"
        proj.mkdir(parents=True)
        (proj / "f.db").write_text("x")
        result = clean_cache(all_projects=True, dry_run=True)
        assert "DRY RUN" in result
        assert proj.exists()  # not actually deleted

    def test_no_pattern_no_all(self):
        self.cache_base.mkdir(parents=True)
        (self.cache_base / "x.1234").mkdir()
        (self.cache_base / "x.1234" / "f.db").write_text("")
        result = clean_cache()
        assert "specify" in result.lower() or "Please" in result

    def test_no_match(self):
        (self.cache_base / "alpha.1111").mkdir(parents=True)
        (self.cache_base / "alpha.1111" / "f.db").write_text("x")
        result = clean_cache(project_pattern="zzz")
        assert "No projects matching" in result
