"""Basic CLI tests."""

from click.testing import CliRunner

from sdd_cli.cli import main as cli


def test_cli_help():
    """CLI --help exits successfully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "SDD CLI" in result.output


def test_cli_version():
    """CLI --version shows version."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_index_help():
    """index --help exits successfully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["index", "--help"])
    assert result.exit_code == 0
    assert "--root" in result.output


def test_search_help():
    """search --help exits successfully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "--help"])
    assert result.exit_code == 0
    assert "--feature-id" in result.output


def test_visualize_help():
    """visualize --help exits successfully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["visualize", "--help"])
    assert result.exit_code == 0
    assert "--filter-dir" in result.output


def test_cache_list_help():
    """cache list --help exits successfully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["cache", "list", "--help"])
    assert result.exit_code == 0
    assert "--format" in result.output


def test_cache_clean_help():
    """cache clean --help exits successfully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["cache", "clean", "--help"])
    assert result.exit_code == 0
    assert "--all" in result.output
