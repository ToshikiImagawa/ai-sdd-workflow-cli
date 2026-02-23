"""Tests for the init command."""

import json

from click.testing import CliRunner

from sdd_cli.cli import main as cli
from sdd_cli.commands.init import _build_env_lines, _write_to_claude_env_file, initialize_project
from sdd_cli.config import _DEFAULTS, CONFIG_FILE_NAME


class TestInitCommand:
    """CLI integration tests for the init command."""

    def test_init_help(self):
        """init --help exits successfully."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "--root" in result.output
        assert "--env" in result.output

    def test_init_creates_config(self, tmp_path):
        """init creates .sdd-config.json."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--root", str(tmp_path)])
        assert result.exit_code == 0

        config_path = tmp_path / CONFIG_FILE_NAME
        assert config_path.exists()
        assert f"Created: {config_path}" in result.output

    def test_init_skips_existing_config(self, tmp_path):
        """init skips if .sdd-config.json already exists."""
        config_path = tmp_path / CONFIG_FILE_NAME
        config_path.write_text("{}", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--root", str(tmp_path)])
        assert result.exit_code == 0
        assert "Config already exists" in result.output

        # Config file not overwritten
        assert config_path.read_text(encoding="utf-8") == "{}"

    def test_init_env_outputs_export_statements(self, tmp_path):
        """--env outputs export statements with all SDD variables."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--root", str(tmp_path), "--env"])
        assert result.exit_code == 0
        assert 'export SDD_ROOT=".sdd"' in result.output
        assert 'export SDD_REQUIREMENT_DIR="requirement"' in result.output
        assert 'export SDD_SPECIFICATION_DIR="specification"' in result.output
        assert 'export SDD_TASK_DIR="task"' in result.output
        assert 'export SDD_REQUIREMENT_PATH=".sdd/requirement"' in result.output
        assert 'export SDD_SPECIFICATION_PATH=".sdd/specification"' in result.output
        assert 'export SDD_TASK_PATH=".sdd/task"' in result.output
        assert 'export SDD_LANG="en"' in result.output

    def test_init_env_with_existing_config(self, tmp_path):
        """--env outputs export statements even when config already exists."""
        config_data = {
            "root": "docs",
            "lang": "ja",
            "directories": {"requirement": "reqs", "specification": "specs", "task": "tasks"},
        }
        (tmp_path / CONFIG_FILE_NAME).write_text(json.dumps(config_data), encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--root", str(tmp_path), "--env"])
        assert result.exit_code == 0
        assert 'export SDD_ROOT="docs"' in result.output
        assert 'export SDD_REQUIREMENT_DIR="reqs"' in result.output
        assert 'export SDD_LANG="ja"' in result.output


class TestInitializeProject:
    """Unit tests for initialize_project function."""

    def test_creates_config(self, tmp_path):
        """Creates .sdd-config.json."""
        initialize_project(tmp_path)

        config_path = tmp_path / CONFIG_FILE_NAME
        assert config_path.exists()

    def test_config_json_is_valid(self, tmp_path):
        """Generated config is valid JSON matching defaults."""
        initialize_project(tmp_path)

        config_path = tmp_path / CONFIG_FILE_NAME
        data = json.loads(config_path.read_text(encoding="utf-8"))
        assert data == _DEFAULTS

    def test_skips_when_config_exists(self, tmp_path):
        """Does not overwrite existing config."""
        config_path = tmp_path / CONFIG_FILE_NAME
        original = '{"custom": true}'
        config_path.write_text(original, encoding="utf-8")

        initialize_project(tmp_path)

        assert config_path.read_text(encoding="utf-8") == original

    def test_idempotent(self, tmp_path):
        """Running twice does not fail (config skip on second run)."""
        initialize_project(tmp_path)
        # Second run should not raise (config already exists)
        initialize_project(tmp_path)
        assert (tmp_path / CONFIG_FILE_NAME).exists()

    def test_env_sdd_root(self, tmp_path, monkeypatch):
        """SDD_ROOT env var is reflected in config."""
        monkeypatch.setenv("SDD_ROOT", "docs")
        initialize_project(tmp_path)

        config = json.loads((tmp_path / CONFIG_FILE_NAME).read_text(encoding="utf-8"))
        assert config["root"] == "docs"

    def test_env_custom_directories(self, tmp_path, monkeypatch):
        """SDD_*_DIR env vars are reflected in config."""
        monkeypatch.setenv("SDD_REQUIREMENT_DIR", "reqs")
        monkeypatch.setenv("SDD_SPECIFICATION_DIR", "specs")
        monkeypatch.setenv("SDD_TASK_DIR", "tasks")
        initialize_project(tmp_path)

        config = json.loads((tmp_path / CONFIG_FILE_NAME).read_text(encoding="utf-8"))
        assert config["directories"]["requirement"] == "reqs"
        assert config["directories"]["specification"] == "specs"
        assert config["directories"]["task"] == "tasks"

    def test_env_writes_to_claude_env_file(self, tmp_path, monkeypatch):
        """When CLAUDE_ENV_FILE is set, env vars are written to that file."""
        env_file = tmp_path / "env_out"
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
        initialize_project(tmp_path, env=True)

        content = env_file.read_text(encoding="utf-8")
        assert 'export SDD_ROOT=".sdd"' in content
        assert 'export SDD_LANG="en"' in content

    def test_env_claude_env_file_removes_duplicates(self, tmp_path, monkeypatch):
        """Writing to CLAUDE_ENV_FILE removes existing SDD_* lines first."""
        env_file = tmp_path / "env_out"
        env_file.write_text(
            'export OTHER_VAR="keep"\nexport SDD_ROOT="old"\nexport SDD_LANG="old"\n',
            encoding="utf-8",
        )
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
        initialize_project(tmp_path, env=True)

        content = env_file.read_text(encoding="utf-8")
        assert 'export OTHER_VAR="keep"' in content
        assert 'export SDD_ROOT="old"' not in content
        assert 'export SDD_ROOT=".sdd"' in content
        # Only one SDD_ROOT line
        assert content.count("export SDD_ROOT=") == 1


class TestBuildEnvLines:
    """Unit tests for _build_env_lines."""

    def test_default_config(self):
        """Produces all 8 export lines from default config."""
        lines = _build_env_lines(_DEFAULTS)
        assert len(lines) == 8
        assert 'export SDD_ROOT=".sdd"' in lines
        assert 'export SDD_REQUIREMENT_PATH=".sdd/requirement"' in lines

    def test_custom_config(self):
        """Produces correct export lines from custom config."""
        config = {
            "root": "docs",
            "lang": "ja",
            "directories": {"requirement": "reqs", "specification": "specs", "task": "tasks"},
        }
        lines = _build_env_lines(config)
        assert 'export SDD_ROOT="docs"' in lines
        assert 'export SDD_REQUIREMENT_DIR="reqs"' in lines
        assert 'export SDD_REQUIREMENT_PATH="docs/reqs"' in lines
        assert 'export SDD_LANG="ja"' in lines


class TestWriteToClaudeEnvFile:
    """Unit tests for _write_to_claude_env_file."""

    def test_creates_new_file(self, tmp_path):
        """Creates file when it doesn't exist."""
        env_file = tmp_path / "env_out"
        _write_to_claude_env_file(env_file, ['export SDD_ROOT=".sdd"'])

        content = env_file.read_text(encoding="utf-8")
        assert 'export SDD_ROOT=".sdd"' in content

    def test_preserves_non_sdd_lines(self, tmp_path):
        """Keeps non-SDD_* lines when removing duplicates."""
        env_file = tmp_path / "env_out"
        env_file.write_text('export FOO="bar"\nexport SDD_ROOT="old"\n', encoding="utf-8")

        _write_to_claude_env_file(env_file, ['export SDD_ROOT=".sdd"'])

        content = env_file.read_text(encoding="utf-8")
        assert 'export FOO="bar"' in content
        assert 'export SDD_ROOT=".sdd"' in content
        assert 'export SDD_ROOT="old"' not in content

    def test_appends_multiple_lines(self, tmp_path):
        """Appends all provided lines."""
        env_file = tmp_path / "env_out"
        lines = ['export SDD_ROOT=".sdd"', 'export SDD_LANG="en"']
        _write_to_claude_env_file(env_file, lines)

        content = env_file.read_text(encoding="utf-8")
        assert 'export SDD_ROOT=".sdd"' in content
        assert 'export SDD_LANG="en"' in content
