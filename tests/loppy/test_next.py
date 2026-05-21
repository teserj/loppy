import pytest
from conftest import run_loppy


def test_next_empty_sources_returns_empty(loppy_env):
    env, vault = loppy_env
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_next_uses_batch_size_by_default(loppy_env):
    env, vault = loppy_env
    for i in range(7):
        (vault / "sources" / f"file{i:02d}.md").write_text("x", encoding="utf-8")
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    assert len(result.stdout.strip().splitlines()) == 5


def test_next_limits_to_n(loppy_env):
    env, vault = loppy_env
    for i in range(7):
        (vault / "sources" / f"file{i:02d}.md").write_text("x", encoding="utf-8")
    result = run_loppy("next", "2", env=env)
    assert result.returncode == 0
    assert len(result.stdout.strip().splitlines()) == 2


def test_next_excludes_processed_subdir(loppy_env):
    env, vault = loppy_env
    (vault / "sources" / "keep.md").write_text("x", encoding="utf-8")
    (vault / "sources" / "processed" / "already.md").write_text("x", encoding="utf-8")
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    assert "keep.md" in result.stdout
    assert "already.md" not in result.stdout


def test_next_includes_txt_files(loppy_env):
    env, vault = loppy_env
    (vault / "sources" / "file1.md").write_text("x", encoding="utf-8")
    (vault / "sources" / "file2.txt").write_text("x", encoding="utf-8")
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    assert "file1.md" in result.stdout
    assert "file2.txt" in result.stdout


def test_next_returns_absolute_paths(loppy_env):
    env, vault = loppy_env
    (vault / "sources" / "test.md").write_text("x", encoding="utf-8")
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    line = result.stdout.strip().splitlines()[0]
    assert line.startswith("/") or (len(line) > 2 and line[1] == ":")  # Unix abs or Windows C:\...


def test_next_produces_sorted_output(loppy_env):
    env, vault = loppy_env
    for name in ["zebra.md", "apple.md", "banana.md"]:
        (vault / "sources" / name).write_text("x", encoding="utf-8")
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert "apple.md" in lines[0]
    assert "zebra.md" in lines[-1]
