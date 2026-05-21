import pytest
from conftest import run_loppy


def test_move_relocates_file(loppy_env):
    env, vault = loppy_env
    src = vault / "sources" / "note.md"
    src.write_text("hello", encoding="utf-8")
    result = run_loppy("move", str(src), env=env)
    assert result.returncode == 0
    assert not src.exists()
    dest = vault / "sources" / "processed" / "note.md"
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "hello"


def test_move_creates_processed_dir_if_missing(loppy_env):
    env, vault = loppy_env
    processed = vault / "sources" / "processed"
    for p in processed.iterdir():
        pass  # just ensure it's accessible; remove dir:
    import shutil
    shutil.rmtree(processed)
    assert not processed.exists()
    src = vault / "sources" / "new.md"
    src.write_text("data", encoding="utf-8")
    result = run_loppy("move", str(src), env=env)
    assert result.returncode == 0
    assert processed.is_dir()
    assert (processed / "new.md").exists()


def test_move_refuses_if_dest_exists(loppy_env):
    env, vault = loppy_env
    src = vault / "sources" / "note.md"
    src.write_text("original", encoding="utf-8")
    (vault / "sources" / "processed" / "note.md").write_text("existing", encoding="utf-8")
    result = run_loppy("move", str(src), env=env)
    assert result.returncode != 0
    assert "destination exists" in result.stderr
    assert src.exists()


def test_move_fails_if_source_missing(loppy_env):
    env, vault = loppy_env
    result = run_loppy("move", str(vault / "sources" / "nonexistent.md"), env=env)
    assert result.returncode != 0
    assert "source not found" in result.stderr


def test_move_requires_argument(loppy_env):
    env, vault = loppy_env
    result = run_loppy("move", env=env)
    assert result.returncode != 0
    assert "source path required" in result.stderr


def test_move_uses_git_mv_in_git_vault(loppy_env):
    import subprocess as sp
    env, vault = loppy_env
    # Init git repo in vault
    sp.run(["git", "-C", str(vault), "init", "-q"], check=True)
    sp.run(["git", "-C", str(vault), "config", "user.email", "t@t.com"], check=True)
    sp.run(["git", "-C", str(vault), "config", "user.name", "Test"], check=True)
    src = vault / "sources" / "tracked.md"
    src.write_text("content", encoding="utf-8")
    sp.run(["git", "-C", str(vault), "add", str(src)], check=True)
    sp.run(["git", "-C", str(vault), "commit", "-q", "-m", "add tracked"], check=True)
    result = run_loppy("move", str(src), env=env)
    assert result.returncode == 0
    assert not src.exists()
    assert (vault / "sources" / "processed" / "tracked.md").exists()
    status = sp.run(
        ["git", "-C", str(vault), "status", "--short"],
        capture_output=True, text=True
    )
    assert "R" in status.stdout
