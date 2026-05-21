import pytest
from conftest import run_loppy

LOG_INITIAL = (
    "---\n"
    "type: log\n"
    "title: Wiki Activity Log\n"
    "---\n"
    "\n"
    "# Wiki Log\n"
    "\n"
    "Append-only. New entries at top.\n"
    "\n"
    "---\n"
    "\n"
)

LOG_NO_SEP = (
    "---\n"
    "type: log\n"
    "title: Wiki Activity Log\n"
    "---\n"
    "\n"
    "# Wiki Log\n"
    "\n"
    "Append-only. New entries at top.\n"
)


def test_log_prepends_new_entry(loppy_env):
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    log = vault / "wiki" / "log.md"
    with open(log, "w", encoding="utf-8", newline="\n") as f:
        f.write(LOG_INITIAL)
    result = run_loppy("log", "ingest", "first batch", env=env, stdin="body line one")
    assert result.returncode == 0
    content = log.read_text(encoding="utf-8")
    assert "## [2026-04-17] ingest | first batch" in content
    assert "body line one" in content


def test_log_preserves_file_header(loppy_env):
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    log = vault / "wiki" / "log.md"
    with open(log, "w", encoding="utf-8", newline="\n") as f:
        f.write(LOG_INITIAL)
    result = run_loppy("log", "lint", "nothing found", env=env, stdin="x")
    assert result.returncode == 0
    lines = log.read_text(encoding="utf-8").splitlines()
    assert any("type: log" in l for l in lines[:6])
    assert any("# Wiki Log" in l for l in lines[:10])


def test_log_newest_entry_above_prior_entries(loppy_env):
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    log = vault / "wiki" / "log.md"
    with open(log, "w", encoding="utf-8", newline="\n") as f:
        f.write(LOG_INITIAL)
    run_loppy("log", "ingest", "entry-one", env=env, stdin="first")
    run_loppy("log", "ingest", "entry-two", env=env, stdin="second")
    content = log.read_text(encoding="utf-8")
    pos_one = content.index("entry-one")
    pos_two = content.index("entry-two")
    assert pos_two < pos_one


def test_log_requires_op_and_title(loppy_env):
    env, vault = loppy_env
    with open(vault / "wiki" / "log.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(LOG_INITIAL)
    r1 = run_loppy("log", env=env, stdin="x")
    assert r1.returncode != 0
    r2 = run_loppy("log", "ingest", env=env, stdin="x")
    assert r2.returncode != 0


def test_log_supports_multiline_body(loppy_env):
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    with open(vault / "wiki" / "log.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(LOG_INITIAL)
    result = run_loppy("log", "ingest", "multi", env=env, stdin="line 1\nline 2\nline 3")
    assert result.returncode == 0
    content = (vault / "wiki" / "log.md").read_text(encoding="utf-8")
    assert "line 1" in content
    assert "line 2" in content
    assert "line 3" in content


def test_log_creates_separator_when_missing(loppy_env):
    env, vault = loppy_env
    env["LOPPY_TODAY"] = "2026-04-17"
    with open(vault / "wiki" / "log.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(LOG_NO_SEP)
    result = run_loppy("log", "ingest", "no-sep-title", env=env, stdin="no-sep body")
    assert result.returncode == 0
    content = (vault / "wiki" / "log.md").read_text(encoding="utf-8")
    assert "## [2026-04-17] ingest | no-sep-title" in content
    assert "no-sep body" in content
    assert "---" in content


def test_log_fails_when_log_md_missing(loppy_env):
    env, vault = loppy_env
    (vault / "wiki" / "log.md").unlink()
    result = run_loppy("log", "ingest", "missing", env=env, stdin="x")
    assert result.returncode != 0
    assert "not found" in result.stderr
