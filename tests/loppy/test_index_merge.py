import json
import pytest
from pathlib import Path
from conftest import run_loppy

REPO_ROOT = Path(__file__).parent.parent.parent
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "index-merge"


def test_index_merge_inserts_into_empty_index(loppy_env):
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    wiki = vault / "wiki"
    (wiki / "concepts").mkdir()
    (wiki / "sources").mkdir()
    (wiki / "concepts" / "foo.md").write_text("", encoding="utf-8")
    (wiki / "sources" / "bar.md").write_text("", encoding="utf-8")
    # Seed before-fixture
    (wiki / "index.md").write_bytes((FIXTURE_DIR / "empty-before.md").read_bytes())
    payload = json.dumps([
        {"path": "wiki/concepts/foo.md", "summary": "Foo concept summary"},
        {"path": "wiki/sources/bar.md", "summary": "Bar source summary"},
    ])
    result = run_loppy("index-merge", env=env, stdin=payload)
    assert result.returncode == 0
    expected = (FIXTURE_DIR / "empty-after.md").read_text(encoding="utf-8")
    actual = (wiki / "index.md").read_text(encoding="utf-8")
    assert actual == expected


def test_index_merge_updates_existing_entry(loppy_env):
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    wiki = vault / "wiki"
    (wiki / "concepts").mkdir()
    (wiki / "concepts" / "foo.md").write_text("", encoding="utf-8")
    (wiki / "index.md").write_bytes((FIXTURE_DIR / "one-entry-before.md").read_bytes())
    payload = json.dumps([{"path": "wiki/concepts/foo.md", "summary": "New summary"}])
    result = run_loppy("index-merge", env=env, stdin=payload)
    assert result.returncode == 0
    expected = (FIXTURE_DIR / "one-entry-after.md").read_text(encoding="utf-8")
    actual = (wiki / "index.md").read_text(encoding="utf-8")
    assert actual == expected


def test_index_merge_warns_on_orphan(loppy_env):
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    wiki = vault / "wiki"
    (wiki / "concepts").mkdir()
    (wiki / "concepts" / "foo.md").write_text("", encoding="utf-8")
    (wiki / "concepts" / "orphan.md").write_text("", encoding="utf-8")
    (wiki / "index.md").write_bytes((FIXTURE_DIR / "empty-before.md").read_bytes())
    payload = json.dumps([{"path": "wiki/concepts/foo.md", "summary": "x"}])
    result = run_loppy("index-merge", env=env, stdin=payload)
    assert result.returncode == 0
    assert "orphan" in result.stderr
    assert "wiki/concepts/orphan.md" in result.stderr


def test_index_merge_ignores_index_and_log(loppy_env):
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    wiki = vault / "wiki"
    (wiki / "index.md").write_bytes((FIXTURE_DIR / "empty-before.md").read_bytes())
    result = run_loppy("index-merge", env=env, stdin="[]")
    assert result.returncode == 0
    assert "orphan: wiki/index.md" not in result.stderr
    assert "orphan: wiki/log.md" not in result.stderr


def test_index_merge_no_leftover_tmp_files(loppy_env):
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    wiki = vault / "wiki"
    (wiki / "index.md").write_bytes((FIXTURE_DIR / "empty-before.md").read_bytes())
    result = run_loppy("index-merge", env=env, stdin="[]")
    assert result.returncode == 0
    tmp_files = list(wiki.glob(".tmp*")) + list(wiki.glob("index.md.*"))
    assert tmp_files == []


def test_index_merge_invalid_json_exits_nonzero(loppy_env):
    env, vault = loppy_env
    wiki = vault / "wiki"
    (wiki / "index.md").write_bytes((FIXTURE_DIR / "empty-before.md").read_bytes())
    result = run_loppy("index-merge", env=env, stdin="not json")
    assert result.returncode != 0


def test_index_merge_non_ascii_utf8_summary(loppy_env):
    """Summaries with non-ASCII characters (e.g. CJK) must survive the stdin decode."""
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    wiki = vault / "wiki"
    (wiki / "concepts").mkdir()
    (wiki / "concepts" / "cjk.md").write_text("", encoding="utf-8")
    (wiki / "index.md").write_bytes((FIXTURE_DIR / "empty-before.md").read_bytes())
    payload = json.dumps([{"path": "wiki/concepts/cjk.md", "summary": "台灣硬體工作坊"}])
    result = run_loppy("index-merge", env=env, stdin=payload)
    assert result.returncode == 0
    content = (wiki / "index.md").read_text(encoding="utf-8")
    assert "台灣硬體工作坊" in content
