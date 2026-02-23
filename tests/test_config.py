"""Tests for config module."""

import json

import pytest

from sdd_cli.config import load_config_file, resolve_config

# ---------------------------------------------------------------------------
# load_config_file
# ---------------------------------------------------------------------------


class TestLoadConfigFile:
    def test_no_file(self, tmp_path):
        assert load_config_file(tmp_path) == {}

    def test_valid_json(self, tmp_path):
        (tmp_path / ".sdd-config.json").write_text(json.dumps({"root": ".docs"}))
        result = load_config_file(tmp_path)
        assert result == {"root": ".docs"}

    def test_invalid_json(self, tmp_path):
        (tmp_path / ".sdd-config.json").write_text("{broken")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_config_file(tmp_path)

    def test_non_object_json(self, tmp_path):
        (tmp_path / ".sdd-config.json").write_text(json.dumps([1, 2, 3]))
        with pytest.raises(ValueError, match="must contain a JSON object"):
            load_config_file(tmp_path)

    def test_partial_config(self, tmp_path):
        (tmp_path / ".sdd-config.json").write_text(json.dumps({"lang": "ja"}))
        result = load_config_file(tmp_path)
        assert result == {"lang": "ja"}


# ---------------------------------------------------------------------------
# resolve_config — defaults
# ---------------------------------------------------------------------------


class TestResolveConfigDefaults:
    def test_all_defaults(self, tmp_path):
        config = resolve_config(tmp_path)
        assert config["root"] == ".sdd"
        assert config["lang"] == "en"
        assert config["directories"]["requirement"] == "requirement"
        assert config["directories"]["specification"] == "specification"
        assert config["directories"]["task"] == "task"


# ---------------------------------------------------------------------------
# resolve_config — file overrides
# ---------------------------------------------------------------------------


class TestResolveConfigFile:
    def test_file_overrides_defaults(self, tmp_path):
        cfg = {
            "root": ".docs",
            "lang": "ja",
            "directories": {
                "requirement": "reqs",
                "specification": "specs",
                "task": "todos",
            },
        }
        (tmp_path / ".sdd-config.json").write_text(json.dumps(cfg))
        config = resolve_config(tmp_path)
        assert config["root"] == ".docs"
        assert config["lang"] == "ja"
        assert config["directories"]["requirement"] == "reqs"
        assert config["directories"]["specification"] == "specs"
        assert config["directories"]["task"] == "todos"

    def test_partial_file(self, tmp_path):
        cfg = {"directories": {"requirement": "reqs"}}
        (tmp_path / ".sdd-config.json").write_text(json.dumps(cfg))
        config = resolve_config(tmp_path)
        assert config["root"] == ".sdd"
        assert config["directories"]["requirement"] == "reqs"
        assert config["directories"]["specification"] == "specification"
        assert config["directories"]["task"] == "task"

    def test_directories_not_dict(self, tmp_path):
        cfg = {"directories": "invalid"}
        (tmp_path / ".sdd-config.json").write_text(json.dumps(cfg))
        config = resolve_config(tmp_path)
        assert config["directories"]["requirement"] == "requirement"
        assert config["directories"]["specification"] == "specification"
        assert config["directories"]["task"] == "task"


# ---------------------------------------------------------------------------
# resolve_config — env overrides
# ---------------------------------------------------------------------------


class TestResolveConfigEnv:
    def test_env_overrides_file(self, tmp_path, monkeypatch):
        cfg = {
            "root": ".docs",
            "directories": {
                "requirement": "reqs",
                "specification": "specs",
                "task": "todos",
            },
        }
        (tmp_path / ".sdd-config.json").write_text(json.dumps(cfg))
        monkeypatch.setenv("SDD_ROOT", ".custom")
        monkeypatch.setenv("SDD_REQUIREMENT_DIR", "env_reqs")
        monkeypatch.setenv("SDD_SPECIFICATION_DIR", "env_specs")
        monkeypatch.setenv("SDD_TASK_DIR", "env_tasks")

        config = resolve_config(tmp_path)
        assert config["root"] == ".custom"
        assert config["directories"]["requirement"] == "env_reqs"
        assert config["directories"]["specification"] == "env_specs"
        assert config["directories"]["task"] == "env_tasks"

    def test_env_overrides_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SDD_ROOT", ".env_root")
        monkeypatch.setenv("SDD_REQUIREMENT_DIR", "env_req")
        config = resolve_config(tmp_path)
        assert config["root"] == ".env_root"
        assert config["directories"]["requirement"] == "env_req"
        assert config["directories"]["specification"] == "specification"
        assert config["directories"]["task"] == "task"
