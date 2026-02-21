"""Tests for DocumentScanner."""

from pathlib import Path

from sdd_cli.indexer.scanner import DocumentScanner
from sdd_cli.types import SDDDirectories

# ---------------------------------------------------------------------------
# Directory name defaults / env override
# ---------------------------------------------------------------------------


class TestDirectoryNames:
    def test_default_directories(self, sdd_root):
        scanner = DocumentScanner(sdd_root)
        assert scanner.requirement_dir == sdd_root / "requirement"
        assert scanner.specification_dir == sdd_root / "specification"
        assert scanner.task_dir == sdd_root / "task"

    def test_env_override(self, sdd_root, monkeypatch):
        monkeypatch.setenv("SDD_REQUIREMENT_DIR", "reqs")
        monkeypatch.setenv("SDD_SPECIFICATION_DIR", "specs")
        monkeypatch.setenv("SDD_TASK_DIR", "tasks")
        # Create override dirs
        for d in ("reqs", "specs", "tasks"):
            (sdd_root / d).mkdir(exist_ok=True)
        scanner = DocumentScanner(sdd_root)
        assert scanner.requirement_dir == sdd_root / "reqs"
        assert scanner.specification_dir == sdd_root / "specs"
        assert scanner.task_dir == sdd_root / "tasks"


# ---------------------------------------------------------------------------
# scan_all
# ---------------------------------------------------------------------------


class TestScanAll:
    def test_empty_dirs(self, sdd_root):
        scanner = DocumentScanner(sdd_root)
        assert scanner.scan_all() == []

    def test_finds_requirement(self, sdd_root):
        (sdd_root / "requirement" / "auth.md").write_text("# Auth")
        docs = DocumentScanner(sdd_root).scan_all()
        assert len(docs) == 1
        assert docs[0]["directory"] == "requirement"
        assert docs[0]["file_name"] == "auth"

    def test_finds_specification(self, sdd_root):
        (sdd_root / "specification" / "auth_spec.md").write_text("# Spec")
        docs = DocumentScanner(sdd_root).scan_all()
        assert len(docs) == 1
        assert docs[0]["directory"] == "specification"

    def test_task_only_managed_files(self, sdd_root):
        task_dir = sdd_root / "task" / "TICKET-1"
        task_dir.mkdir(parents=True)
        (task_dir / "index.md").write_text("# Task")
        (task_dir / "tasks.md").write_text("# Tasks")
        (task_dir / "notes.md").write_text("# Notes")  # should be ignored
        docs = DocumentScanner(sdd_root).scan_all()
        names = {d["file_name"] for d in docs}
        assert names == {"index", "tasks"}

    def test_hidden_file_excluded(self, sdd_root):
        (sdd_root / "requirement" / ".hidden.md").write_text("# Hidden")
        assert DocumentScanner(sdd_root).scan_all() == []

    def test_recursive(self, sdd_root):
        nested = sdd_root / "requirement" / "auth" / "login"
        nested.mkdir(parents=True)
        (nested / "index.md").write_text("# Login")
        docs = DocumentScanner(sdd_root).scan_all()
        assert len(docs) == 1
        assert "auth/login/index.md" in docs[0]["file_path"]

    def test_metadata_fields(self, sdd_root):
        (sdd_root / "requirement" / "auth.md").write_text("# Auth")
        doc = DocumentScanner(sdd_root).scan_all()[0]
        assert "file_path" in doc
        assert "file_name" in doc
        assert "directory" in doc
        assert "full_path" in doc
        assert isinstance(doc["full_path"], Path)


# ---------------------------------------------------------------------------
# scan_directory
# ---------------------------------------------------------------------------


class TestScanDirectory:
    def test_specific_directory(self, sdd_root):
        (sdd_root / "requirement" / "a.md").write_text("# A")
        (sdd_root / "specification" / "b.md").write_text("# B")
        docs = DocumentScanner(sdd_root).scan_directory("requirement")
        assert len(docs) == 1
        assert docs[0]["directory"] == "requirement"

    def test_nonexistent_directory(self, sdd_root):
        assert DocumentScanner(sdd_root).scan_directory("nonexistent") == []

    def test_task_filtering_in_scan_directory(self, sdd_root):
        task_dir = sdd_root / "task" / "T-1"
        task_dir.mkdir(parents=True)
        (task_dir / "index.md").write_text("# I")
        (task_dir / "other.md").write_text("# O")
        docs = DocumentScanner(sdd_root).scan_directory("task")
        assert len(docs) == 1
        assert docs[0]["file_name"] == "index"

    def test_empty_directory(self, sdd_root):
        docs = DocumentScanner(sdd_root).scan_directory("requirement")
        assert docs == []


# ---------------------------------------------------------------------------
# Relative path
# ---------------------------------------------------------------------------


class TestRelativePath:
    def test_file_path_is_relative_to_root(self, sdd_root):
        (sdd_root / "requirement" / "auth.md").write_text("# Auth")
        doc = DocumentScanner(sdd_root).scan_all()[0]
        # Should NOT contain the sdd_root prefix
        assert not doc["file_path"].startswith(str(sdd_root))
        assert doc["file_path"] == "requirement/auth.md"


# ---------------------------------------------------------------------------
# directories argument (config integration)
# ---------------------------------------------------------------------------


class TestDirectoriesArgument:
    def test_custom_directories(self, tmp_path):
        sdd = tmp_path / ".sdd"
        for d in ("reqs", "specs", "todos"):
            (sdd / d).mkdir(parents=True)
        (sdd / "reqs" / "auth.md").write_text("# Auth")

        dirs: SDDDirectories = {"requirement": "reqs", "specification": "specs", "task": "todos"}
        scanner = DocumentScanner(sdd, directories=dirs)
        assert scanner.requirement_dir == sdd / "reqs"
        assert scanner.specification_dir == sdd / "specs"
        assert scanner.task_dir == sdd / "todos"

        docs = scanner.scan_all()
        assert len(docs) == 1
        assert docs[0]["directory"] == "requirement"

    def test_directories_none_uses_config(self, sdd_root):
        """directories=None should fall back to resolve_config (defaults)."""
        (sdd_root / "requirement" / "a.md").write_text("# A")
        scanner = DocumentScanner(sdd_root)
        assert scanner.requirement_dir == sdd_root / "requirement"
        docs = scanner.scan_all()
        assert len(docs) == 1
