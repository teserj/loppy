"""Lightweight E2E smoke test: ingest a source through the full loppy workflow."""
import json
from conftest import run_loppy


def test_full_ingest_workflow(loppy_env):
    """Smoke test: next → index-merge → move → log → lint-frontmatter."""
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
        "---\ntype: concepts\ntitle: Article\ncreated: 2026-05-21\n"
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

    # lint-frontmatter — clean page must produce no findings at all
    r = run_loppy("lint-frontmatter", env=env)
    assert r.returncode == 0
    findings = json.loads(r.stdout)
    assert findings == [], f"Expected no lint findings, got: {findings}"
