"""Cache directory management for SDD CLI."""

import hashlib
from pathlib import Path


def get_cache_base() -> Path:
    """Get the base cache directory."""
    return Path.home() / ".cache" / "sdd-cli"


def get_project_hash(project_root: Path) -> str:
    """Generate a unique hash for the project based on its absolute path."""
    abs_path = project_root.resolve().as_posix()
    return hashlib.sha256(abs_path.encode()).hexdigest()[:8]


def get_cache_dir(project_root: Path) -> Path:
    """Get the cache directory for the given project.

    Uses XDG Base Directory specification:
    ~/.cache/sdd-cli/{project-name}.{short-hash}/
    """
    cache_base = get_cache_base()
    abs_project_root = project_root.resolve()
    project_name = abs_project_root.name
    project_hash = get_project_hash(abs_project_root)
    cache_dir = cache_base / f"{project_name}.{project_hash}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir
