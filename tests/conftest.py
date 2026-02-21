"""Shared fixtures for SDD CLI tests."""

from pathlib import Path

import pytest

from sdd_cli.indexer.db import IndexDB


@pytest.fixture
def sdd_root(tmp_path: Path) -> Path:
    """Create a minimal .sdd directory structure."""
    sdd = tmp_path / ".sdd"
    for sub in ("requirement", "specification", "task"):
        (sdd / sub).mkdir(parents=True)
    return sdd


@pytest.fixture
def index_db(tmp_path: Path) -> IndexDB:
    """Create an IndexDB backed by a temp-dir SQLite file."""
    db_path = tmp_path / "test_index.db"
    db = IndexDB(db_path)
    yield db
    db.close()
