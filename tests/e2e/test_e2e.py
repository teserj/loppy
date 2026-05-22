"""Lightweight E2E smoke test: ingest a source through the full loppy workflow."""
import json
import sys
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
LOPPY_BIN = REPO_ROOT / "bin" / "loppy"


def run_loppy(*args, env, stdin=None):
    return subprocess.run(
        [sys.executable, str(LOPPY_BIN), *args],
        capture_output=True, text=True, input=stdin, env=env,
    )


def test_full_ingest_workflow(loppy_env):
    """Smoke test: next → move → index-merge → log → lint-frontmatter."""
    env, vault = loppy_env
    wiki = vault / "wiki"
    sources = vault / "sources"

    # Plant a source file
    (sources / "article.md").write_text("# Article\nsome content", encoding="utf-8")

    # next returns the file
    r = run_loppy("next", "1", env=env)
    assert r.returncode == 0
    listed = r.stdout.strip()
    assert "article.md" in listed

    # Create wiki page
    (wiki / "concepts").mkdir(exist_ok=True)
    page = wiki / "concepts" / "article.md"
    page.write_text(
        "---\ntype: concept\ntitle: Article\ncreated: 2026-05-21\n"
        "updated: 2026-05-21\nconfidence: high\ndomain: tech\ntags: []\nlinks: []\n---\n"
        "# Article\nsome content\n",
        encoding="utf-8",
    )

    # index-merge
    payload = json.dumps([{"path": "wiki/concepts/article.md", "summary": "Article summary"}])
    r = run_loppy("index-merge", env=env, stdin=payload)
    assert r.returncode == 0
    idx_content = (wiki / "index.md").read_text(encoding="utf-8")
    assert "Article summary" in idx_content

    # move
    r = run_loppy("move", str(sources / "article.md"), env=env)
    assert r.returncode == 0
    assert not (sources / "article.md").exists()
    assert (sources / "processed" / "article.md").exists()

    # log
    r = run_loppy("log", "ingest", "article", env=env, stdin="Ingested article")
    assert r.returncode == 0
    log_content = (wiki / "log.md").read_text(encoding="utf-8")
    assert "ingest | article" in log_content

    # lint-frontmatter — expect no errors for our good page
    r = run_loppy("lint-frontmatter", env=env)
    assert r.returncode == 0
    findings = json.loads(r.stdout)
    errors = [
        f for entry in findings if entry["path"].endswith("article.md")
        for f in entry["findings"] if f["level"] == "error"
    ]
    assert errors == []
