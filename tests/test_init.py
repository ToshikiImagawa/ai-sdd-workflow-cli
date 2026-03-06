"""Test package initialization."""

from pathlib import Path

from sdd_cli import __version__
from sdd_cli.cache import get_cache_dir, get_project_hash


def test_version():
    """Package version is set."""
    assert __version__ == "1.1.0"


def test_get_project_hash():
    """get_project_hash returns 8-char hex string."""
    result = get_project_hash(Path("/tmp/test-project"))
    assert len(result) == 8
    assert all(c in "0123456789abcdef" for c in result)


def test_get_project_hash_deterministic():
    """Same path produces same hash."""
    path = Path("/tmp/test-project")
    assert get_project_hash(path) == get_project_hash(path)


def test_get_project_hash_different_paths():
    """Different paths produce different hashes."""
    hash1 = get_project_hash(Path("/tmp/project-a"))
    hash2 = get_project_hash(Path("/tmp/project-b"))
    assert hash1 != hash2


def test_get_cache_dir(tmp_path):
    """get_cache_dir returns expected path structure."""
    cache_dir = get_cache_dir(tmp_path)
    assert cache_dir.parent.name == "sdd-cli"
    assert tmp_path.name in cache_dir.name
    assert cache_dir.exists()
