import json
import pytest
from conftest import run_loppy


def test_config_prints_full_json(loppy_env):
    env, vault = loppy_env
    result = run_loppy("config", env=env)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "vault_dir" in data
    assert "batch_size" in data


def test_config_returns_scalar_value(loppy_env):
    env, vault = loppy_env
    result = run_loppy("config", "batch_size", env=env)
    assert result.returncode == 0
    assert result.stdout.strip() == "5"


def test_config_returns_string_value(loppy_env):
    env, vault = loppy_env
    result = run_loppy("config", "vault_dir", env=env)
    assert result.returncode == 0
    assert result.stdout.strip() == str(vault)


def test_config_exits_1_when_config_missing(loppy_env):
    env, vault = loppy_env
    import os
    from pathlib import Path
    if os.name != "nt":
        cfg = Path(env["XDG_CONFIG_HOME"]) / "loppy" / "config.json"
    else:
        cfg = Path(env["APPDATA"]) / "loppy" / "config.json"
    cfg.unlink()
    result = run_loppy("config", env=env)
    assert result.returncode == 1
    assert "config not found" in result.stderr


def test_config_exits_1_on_malformed_json(loppy_env):
    env, vault = loppy_env
    import os
    from pathlib import Path
    if os.name != "nt":
        cfg = Path(env["XDG_CONFIG_HOME"]) / "loppy" / "config.json"
    else:
        cfg = Path(env["APPDATA"]) / "loppy" / "config.json"
    cfg.write_text("not json {{", encoding="utf-8")
    result = run_loppy("config", env=env)
    assert result.returncode == 1


def test_config_exits_1_on_unknown_key(loppy_env):
    env, vault = loppy_env
    result = run_loppy("config", "no_such_key", env=env)
    assert result.returncode == 1
