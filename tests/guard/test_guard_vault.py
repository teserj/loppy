import json
import os
import sys
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
GUARD_SCRIPT = REPO_ROOT / "hooks" / "guard_vault.py"


def run_guard(payload: dict, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GUARD_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
def guard_env(loppy_env):
    env, vault = loppy_env
    return env, vault


def test_guard_allows_loppy_command(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": "loppy config"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_blocks_rm_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": f"rm -rf {vault}/file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_mv_within_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": f"mv {vault}/a.md {vault}/b.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_shred_in_wiki(guard_env):
    env, vault = guard_env
    wiki = str(vault / "wiki")
    r = run_guard({"tool": "bash", "command": f"shred -vfz {wiki}/page.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_allows_find_in_vault(guard_env):
    env, vault = guard_env
    sources = str(vault / "sources")
    r = run_guard({"tool": "bash", "command": f'find {sources} -name "*.md"'}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_allows_git_mv(guard_env):
    env, vault = guard_env
    sources = str(vault / "sources")
    r = run_guard({"tool": "bash", "command": f"git mv {sources}/a.md {sources}/b.md"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_allows_git_rm(guard_env):
    env, vault = guard_env
    wiki = str(vault / "wiki")
    r = run_guard({"tool": "bash", "command": f"git rm {wiki}/page.md"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_blocks_rmdir_in_vault(guard_env):
    env, vault = guard_env
    wiki = str(vault / "wiki")
    r = run_guard({"tool": "bash", "command": f"rmdir {wiki}/subdir"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_dd_in_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": f"dd if=/dev/zero of={vault}/file.txt"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_unlink_in_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": f"unlink {vault}/file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_allows_non_bash_tool(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "read", "file_path": "/some/file.txt"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_allows_write_tool(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "write", "file_path": "/some/file.txt", "content": "test"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_fails_open_when_config_missing(guard_env, tmp_path):
    env, vault = guard_env
    no_config_env = dict(env)
    no_config_env["XDG_CONFIG_HOME"] = str(tmp_path / "empty_xdg")
    r = run_guard({"tool": "bash", "command": f"rm -rf {vault}/file.md"}, no_config_env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_allows_rm_outside_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": "rm -rf /tmp/unrelated/file.txt"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_passes_on_empty_command(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": ""}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_passes_on_malformed_json(guard_env):
    env, vault = guard_env
    result = subprocess.run(
        [sys.executable, str(GUARD_SCRIPT)],
        input="not valid json",
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "PASS"


def test_guard_blocks_var_reference_to_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": "rm -rf $VAULT_DIR/sensitive.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_rm_with_sources_path(guard_env):
    env, vault = guard_env
    sources = str(vault / "sources")
    r = run_guard({"tool": "bash", "command": f"rm {sources}/file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout
