"""Regression tests for the init command (resolve_config + env output)."""

import json
import shutil
from pathlib import Path

import pytest

from sdd_cli.commands.init import _build_env_lines, initialize_project
from sdd_cli.config import CONFIG_FILE_NAME, resolve_config

_TEST_PROJECTS_DIR = Path(__file__).resolve().parent.parent / "test-project"

_TEST_PROJECTS = [
    "01-default-config",
    "02-custom-dirs",
    "03-custom-root",
    "04-partial-config",
    "05-nested-features",
    "06-minimal",
    "07-multi-feature",
]

_ENV_VARS = ["SDD_ROOT", "SDD_REQUIREMENT_DIR", "SDD_SPECIFICATION_DIR", "SDD_TASK_DIR"]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove SDD environment variables to ensure consistent results."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def _load_expected(project_name: str) -> dict:
    """Load init_expected.json for a project."""
    path = _TEST_PROJECTS_DIR / project_name / "init_expected.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("project_name", _TEST_PROJECTS)
class TestInitRegression:
    """Regression tests: resolve_config and env output match expected values."""

    def test_resolve_config(self, project_name):
        """resolve_config returns expected config for each test project."""
        project_dir = _TEST_PROJECTS_DIR / project_name
        expected = _load_expected(project_name)

        actual = dict(resolve_config(project_dir))

        assert actual == expected["config"], f"{project_name}: config mismatch"

    def test_env_lines(self, project_name):
        """_build_env_lines produces expected export statements."""
        project_dir = _TEST_PROJECTS_DIR / project_name
        expected = _load_expected(project_name)

        config = resolve_config(project_dir)
        actual = _build_env_lines(config)

        assert actual == expected["env_lines"], f"{project_name}: env_lines mismatch"

    def test_init_generates_correct_config(self, project_name, tmp_path):
        """initialize_project generates config matching expected when no config exists."""
        expected = _load_expected(project_name)
        project_dir = _TEST_PROJECTS_DIR / project_name
        source_config = project_dir / CONFIG_FILE_NAME

        # Copy to tmp_path: config file only if it exists (to test partial config scenarios)
        if source_config.exists():
            shutil.copy2(source_config, tmp_path / CONFIG_FILE_NAME)
            # Config already exists, init should skip
            initialize_project(tmp_path)
            actual = json.loads((tmp_path / CONFIG_FILE_NAME).read_text(encoding="utf-8"))
            # Original file should be preserved
            original = json.loads(source_config.read_text(encoding="utf-8"))
            assert actual == original, f"{project_name}: existing config should not be overwritten"
        else:
            # No config, init should generate defaults
            initialize_project(tmp_path)
            actual = json.loads((tmp_path / CONFIG_FILE_NAME).read_text(encoding="utf-8"))
            assert actual == expected["config"], f"{project_name}: generated config mismatch"

    def test_init_env_to_claude_env_file(self, project_name, tmp_path, monkeypatch):
        """initialize_project with env=True writes correct lines to CLAUDE_ENV_FILE."""
        expected = _load_expected(project_name)
        project_dir = _TEST_PROJECTS_DIR / project_name
        source_config = project_dir / CONFIG_FILE_NAME

        # Set up project in tmp_path
        if source_config.exists():
            shutil.copy2(source_config, tmp_path / CONFIG_FILE_NAME)

        env_file = tmp_path / "claude_env"
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))

        initialize_project(tmp_path, env=True)

        content = env_file.read_text(encoding="utf-8")
        actual_lines = [line for line in content.splitlines() if line.startswith("export SDD_")]
        assert actual_lines == expected["env_lines"], f"{project_name}: CLAUDE_ENV_FILE content mismatch"
