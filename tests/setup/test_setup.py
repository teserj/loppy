import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SETUP_SCRIPT = REPO_ROOT / "setup.py"


def run_setup(inputs: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SETUP_SCRIPT)],
        input=inputs,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
def setup_env(tmp_path):
    env = dict(os.environ)
    if os.name == "nt":
        env["APPDATA"] = str(tmp_path / "appdata")
    else:
        env["XDG_CONFIG_HOME"] = str(tmp_path / "xdg")
    env["HOME"] = str(tmp_path)
    return env, tmp_path


def _vault_inputs(vault: Path, sources="source", wiki="wiki", git="n") -> str:
    return f"{vault}\n{sources}\n{wiki}\n{git}\n"


def test_setup_creates_config(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault), env)
    if os.name == "nt":
        cfg = tmp / "appdata" / "loppy" / "config.json"
    else:
        cfg = tmp / "xdg" / "loppy" / "config.json"
    assert cfg.exists()


def test_setup_config_has_correct_keys(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault), env)
    if os.name == "nt":
        cfg = tmp / "appdata" / "loppy" / "config.json"
    else:
        cfg = tmp / "xdg" / "loppy" / "config.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert "vault_dir" in data
    assert "sources_dir" in data
    assert "wiki_dir" in data
    assert "batch_size" in data


def test_setup_sources_dir_defaults_to_source(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault, sources=""), env)
    if os.name == "nt":
        cfg = tmp / "appdata" / "loppy" / "config.json"
    else:
        cfg = tmp / "xdg" / "loppy" / "config.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["sources_dir"] == str(vault / "source")


def test_setup_wiki_dir_defaults_to_wiki(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault, wiki=""), env)
    if os.name == "nt":
        cfg = tmp / "appdata" / "loppy" / "config.json"
    else:
        cfg = tmp / "xdg" / "loppy" / "config.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["wiki_dir"] == str(vault / "wiki")


def test_setup_batch_size_defaults_to_5(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault), env)
    if os.name == "nt":
        cfg = tmp / "appdata" / "loppy" / "config.json"
    else:
        cfg = tmp / "xdg" / "loppy" / "config.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["batch_size"] == 5


def test_setup_copies_templates(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault, wiki="wiki"), env)
    assert (vault / "wiki-schema.yaml").exists()
    assert (vault / "wiki" / "index.md").exists()
    assert (vault / "wiki" / "log.md").exists()


def test_setup_creates_subdirectories(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault, sources="sources", wiki="wiki"), env)
    assert (vault / "sources").is_dir()
    assert (vault / "wiki").is_dir()


def test_setup_initializes_git_when_requested(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault, git="y"), env)
    assert (vault / ".git").is_dir()


def test_setup_installs_binary(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault), env)
    bin_dir = tmp / ".local" / "bin"
    # On Unix: bin/loppy; on Windows: bin/loppy.cmd
    installed = list(bin_dir.glob("loppy*")) if bin_dir.exists() else []
    assert len(installed) >= 1
