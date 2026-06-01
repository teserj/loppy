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
    if os.name == "nt":
        no_config_env["APPDATA"] = str(tmp_path / "empty_appdata")
    else:
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


# Windows CMD


def test_guard_blocks_del_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "cmd", "command": f"del {vault}\\file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_erase_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "cmd", "command": f"erase {vault}\\file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_rd_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "cmd", "command": f"rd /s /q {vault}\\subdir"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_move_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "cmd", "command": f"move {vault}\\a.md {vault}\\b.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_windows_env_var_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "cmd", "command": "del %VAULT_DIR%\\file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


# PowerShell


def test_guard_blocks_remove_item_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "powershell", "command": f"Remove-Item -Path {vault}/file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_remove_item_uppercase_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "powershell", "command": f"REMOVE-ITEM {vault}/file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_move_item_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "powershell", "command": f"Move-Item {vault}/a.md {vault}/b.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_ri_alias_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "powershell", "command": f"ri {vault}/file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_mi_alias_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "powershell", "command": f"mi {vault}/a.md {vault}/b.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_powershell_env_var_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "powershell", "command": "Remove-Item $env:VAULT_DIR/file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_allows_powershell_read_outside_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "powershell", "command": "Get-Content /tmp/file.txt"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_allows_powershell_loppy_command(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "powershell", "command": "loppy config"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


# Codex payload shape


def test_guard_codex_blocks_rm_targeting_vault(guard_env):
    env, vault = guard_env
    payload = {"tool_name": "shell_command", "tool_input": {"command": f"rm -rf {vault}/file.md"}}
    r = run_guard(payload, env)
    assert r.returncode == 0
    result = json.loads(r.stdout)
    assert result["decision"] == "block"
    assert "loppy move" in result["reason"]


def test_guard_codex_blocks_canonical_bash_tool_name(guard_env):
    env, vault = guard_env
    payload = {"tool_name": "Bash", "tool_input": {"command": f"rm -rf {vault}/file.md"}}
    r = run_guard(payload, env)
    assert r.returncode == 0
    result = json.loads(r.stdout)
    assert result["decision"] == "block"


def test_guard_codex_blocks_remove_item_targeting_vault(guard_env):
    env, vault = guard_env
    payload = {"tool_name": "shell_command", "tool_input": {"command": f"Remove-Item {vault}/file.md"}}
    r = run_guard(payload, env)
    assert r.returncode == 0
    result = json.loads(r.stdout)
    assert result["decision"] == "block"


def test_guard_codex_allows_safe_command(guard_env):
    env, vault = guard_env
    payload = {"tool_name": "shell_command", "tool_input": {"command": f"cat {vault}/wiki/page.md"}}
    r = run_guard(payload, env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_guard_codex_allows_non_shell_tool(guard_env):
    env, vault = guard_env
    payload = {"tool_name": "read_file", "tool_input": {"path": f"{vault}/wiki/page.md"}}
    r = run_guard(payload, env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_guard_codex_allows_loppy_command(guard_env):
    env, vault = guard_env
    payload = {"tool_name": "shell_command", "tool_input": {"command": "loppy config"}}
    r = run_guard(payload, env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_guard_codex_shell_tool_name_variant(guard_env):
    env, vault = guard_env
    payload = {"tool_name": "shell", "tool_input": {"command": f"rm {vault}/file.md"}}
    r = run_guard(payload, env)
    assert r.returncode == 0
    result = json.loads(r.stdout)
    assert result["decision"] == "block"
