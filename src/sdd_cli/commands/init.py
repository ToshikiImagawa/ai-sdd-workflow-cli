"""Init command implementation."""

import json
import os
from pathlib import Path

import click

from sdd_cli.config import CONFIG_FILE_NAME, resolve_config
from sdd_cli.types import SDDConfig


def _build_env_lines(config: SDDConfig) -> list[str]:
    """Build export statements for SDD environment variables."""
    root = config["root"]
    dirs = config["directories"]
    return [
        f'export SDD_ROOT="{root}"',
        f'export SDD_REQUIREMENT_DIR="{dirs["requirement"]}"',
        f'export SDD_SPECIFICATION_DIR="{dirs["specification"]}"',
        f'export SDD_TASK_DIR="{dirs["task"]}"',
        f'export SDD_REQUIREMENT_PATH="{root}/{dirs["requirement"]}"',
        f'export SDD_SPECIFICATION_PATH="{root}/{dirs["specification"]}"',
        f'export SDD_TASK_PATH="{root}/{dirs["task"]}"',
        f'export SDD_LANG="{config["lang"]}"',
    ]


def _write_to_claude_env_file(env_file: Path, lines: list[str]) -> None:
    """Write env vars to CLAUDE_ENV_FILE, removing existing SDD_* lines first."""
    if env_file.exists():
        existing = env_file.read_text(encoding="utf-8")
        filtered = [line for line in existing.splitlines() if not line.startswith("export SDD_")]
        env_file.write_text("\n".join(filtered) + ("\n" if filtered else ""), encoding="utf-8")

    with open(env_file, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def initialize_project(root: Path, env: bool = False) -> None:
    """Initialize the SDD project.

    Creates .sdd-config.json under the project root.
    Environment variables (SDD_ROOT, SDD_REQUIREMENT_DIR, etc.) are reflected
    in the config file.

    Args:
        root: Project root directory
        env: If True, output export statements for environment variables.
             When CLAUDE_ENV_FILE is set, writes to that file.
             Otherwise outputs to stdout (init messages go to stderr).
    """
    config_path = root / CONFIG_FILE_NAME

    # Check if config already exists
    if config_path.exists():
        click.echo(f"Config already exists: {config_path}", err=env)
    else:
        # Resolve config (env > defaults) and write to file
        config = resolve_config(root)
        config_path.write_text(json.dumps(dict(config), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        click.echo(f"Created: {config_path}", err=env)

    if env:
        resolved = resolve_config(root)
        lines = _build_env_lines(resolved)

        claude_env_file = os.environ.get("CLAUDE_ENV_FILE")
        if claude_env_file:
            _write_to_claude_env_file(Path(claude_env_file), lines)
        else:
            for line in lines:
                click.echo(line)
