"""Configuration loading for SDD CLI.

Resolves settings with priority: environment variables > .sdd-config.json > defaults.
"""

import json
import os
from pathlib import Path

from sdd_cli.types import SDDConfig, SDDDirectories

CONFIG_FILE_NAME = ".sdd-config.json"

_DEFAULTS: SDDConfig = {
    "root": ".sdd",
    "lang": "en",
    "directories": {
        "requirement": "requirement",
        "specification": "specification",
        "task": "task",
    },
}


def load_config_file(project_root: Path) -> dict:
    """Load .sdd-config.json from the project root.

    Args:
        project_root: Project root directory containing .sdd-config.json

    Returns:
        Parsed JSON as dict, or empty dict if a file does not exist.

    Raises:
        ValueError: If a file exists but contains invalid JSON or is not an object.
    """
    config_path = project_root / CONFIG_FILE_NAME
    if not config_path.exists():
        return {}

    text = config_path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {config_path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"{config_path} must contain a JSON object, got {type(data).__name__}")

    return data


def resolve_config(project_root: Path) -> SDDConfig:
    """Resolve SDD configuration with priority: env > file > defaults.

    Args:
        project_root: Project root directory

    Returns:
        Resolved SDDConfig.
    """
    file_config = load_config_file(project_root)

    # Resolve directories from a file (only if it's a dict)
    file_dirs = file_config.get("directories", {})
    if not isinstance(file_dirs, dict):
        file_dirs = {}

    directories: SDDDirectories = {
        "requirement": os.environ.get(
            "SDD_REQUIREMENT_DIR",
            file_dirs.get("requirement", _DEFAULTS["directories"]["requirement"]),
        ),
        "specification": os.environ.get(
            "SDD_SPECIFICATION_DIR",
            file_dirs.get("specification", _DEFAULTS["directories"]["specification"]),
        ),
        "task": os.environ.get(
            "SDD_TASK_DIR",
            file_dirs.get("task", _DEFAULTS["directories"]["task"]),
        ),
    }

    root = os.environ.get("SDD_ROOT", file_config.get("root", _DEFAULTS["root"]))
    lang = file_config.get("lang", _DEFAULTS["lang"])

    return SDDConfig(root=root, lang=lang, directories=directories)


def resolve_sdd_root(project_root: Path) -> Path:
    """Resolve SDD root directory from project root using config."""
    config = resolve_config(project_root)
    return project_root / config["root"]
