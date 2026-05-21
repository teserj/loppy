import json
import pytest
from pathlib import Path
from conftest import run_loppy

GOOD_FM = (
    "---\n"
    "type: concept\n"
    "title: Good Page\n"
    "created: 2026-04-17\n"
    "updated: 2026-04-17\n"
    "confidence: high\n"
    "domain: tech\n"
    "tags: [x]\n"
    "links: []\n"
    "---\n"
    "# body\n"
)

INDEX_EMPTY = (
    "---\ntype: index\ntitle: Wiki Index\nupdated: 2026-04-17\n---\n\n"
    "# Wiki Index\n\nTotal pages: 0\n\n"
    "## Concepts\n\n## Entities\n\n## Sources\n\n## Topics\n"
)


def _setup_lint_env(vault, env):
    """Seed index.md and create wiki subdirs for lint tests."""
    env["LOPPY_TODAY"] = "2026-04-17"
    wiki = vault / "wiki"
    (wiki / "concepts").mkdir(exist_ok=True)
    (wiki / "sources").mkdir(exist_ok=True)
    with open(wiki / "index.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(INDEX_EMPTY)
    return wiki


def _write_page(path: Path, frontmatter: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(frontmatter + "\n# body\n")


def test_lint_reports_missing_fields(loppy_env):
    env, vault = loppy_env
    wiki = _setup_lint_env(vault, env)
    _write_page(wiki / "concepts" / "bad.md", "---\ntype: concept\ntitle: Bad Page\n---")
    result = run_loppy("lint-frontmatter", env=env)
    assert result.returncode == 0
    findings = json.loads(result.stdout)
    bad = next(f for f in findings if f["path"].endswith("bad.md"))
    assert any(
        f["level"] == "error" and f["rule"] == "missing-field" and f["field"] == "domain"
        for f in bad["findings"]
    )


def test_lint_accepts_well_formed_page(loppy_env):
    env, vault = loppy_env
    wiki = _setup_lint_env(vault, env)
    _write_page(wiki / "concepts" / "good.md", GOOD_FM.rstrip("\n# body\n"))
    # Add good.md to index so it's not orphaned
    idx = wiki / "index.md"
    content = idx.read_text(encoding="utf-8").replace(
        "## Concepts\n",
        "## Concepts\n\n- [[wiki/concepts/good]] — Good Page (updated: 2026-04-17)\n",
    )
    with open(idx, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    result = run_loppy("lint-frontmatter", env=env)
    assert result.returncode == 0
    findings = json.loads(result.stdout)
    errors_for_good = [
        f for entry in findings if entry["path"].endswith("good.md")
        for f in entry["findings"] if f["level"] == "error"
    ]
    assert errors_for_good == []


def test_lint_flags_invalid_type_enum(loppy_env):
    env, vault = loppy_env
    wiki = _setup_lint_env(vault, env)
    fm = GOOD_FM.replace("type: concept", "type: nonsense").rstrip("\n# body\n")
    _write_page(wiki / "concepts" / "enum.md", fm)
    result = run_loppy("lint-frontmatter", env=env)
    findings = json.loads(result.stdout)
    entry = next(f for f in findings if f["path"].endswith("enum.md"))
    assert any(f["rule"] == "bad-enum" and f["field"] == "type" for f in entry["findings"])


def test_lint_flags_stale_page(loppy_env):
    env, vault = loppy_env
    wiki = _setup_lint_env(vault, env)
    fm = GOOD_FM.replace("updated: 2026-04-17", "updated: 2025-01-01") \
                .replace("created: 2026-04-17", "created: 2025-01-01") \
                .rstrip("\n# body\n")
    _write_page(wiki / "concepts" / "stale.md", fm)
    result = run_loppy("lint-frontmatter", env=env)
    findings = json.loads(result.stdout)
    entry = next(f for f in findings if f["path"].endswith("stale.md"))
    assert any(f["level"] == "warn" and f["rule"] == "stale" for f in entry["findings"])


def test_lint_no_stale_when_confidence_is_stale(loppy_env):
    env, vault = loppy_env
    wiki = _setup_lint_env(vault, env)
    fm = GOOD_FM.replace("updated: 2026-04-17", "updated: 2025-01-01") \
                .replace("created: 2026-04-17", "created: 2025-01-01") \
                .replace("confidence: high", "confidence: stale") \
                .rstrip("\n# body\n")
    _write_page(wiki / "concepts" / "okstale.md", fm)
    result = run_loppy("lint-frontmatter", env=env)
    findings = json.loads(result.stdout)
    stale_findings = [
        f for entry in findings if entry["path"].endswith("okstale.md")
        for f in entry["findings"] if f["rule"] == "stale"
    ]
    assert stale_findings == []


def test_lint_flags_orphan(loppy_env):
    env, vault = loppy_env
    wiki = _setup_lint_env(vault, env)
    _write_page(wiki / "concepts" / "orph.md", GOOD_FM.rstrip("\n# body\n"))
    result = run_loppy("lint-frontmatter", env=env)
    findings = json.loads(result.stdout)
    entry = next(f for f in findings if f["path"].endswith("orph.md"))
    assert any(f["rule"] == "orphan" for f in entry["findings"])


def test_lint_flags_broken_link(loppy_env):
    env, vault = loppy_env
    wiki = _setup_lint_env(vault, env)
    fm = GOOD_FM.replace("links: []", "links: [wiki/entities/ghost]").rstrip("\n# body\n")
    _write_page(wiki / "concepts" / "brk.md", fm)
    result = run_loppy("lint-frontmatter", env=env)
    findings = json.loads(result.stdout)
    entry = next(f for f in findings if f["path"].endswith("brk.md"))
    assert any(f["rule"] == "broken-link" for f in entry["findings"])


def test_lint_skips_index_and_log(loppy_env):
    env, vault = loppy_env
    wiki = _setup_lint_env(vault, env)
    result = run_loppy("lint-frontmatter", env=env)
    assert result.returncode == 0
    findings = json.loads(result.stdout)
    assert not any(f["path"].endswith("index.md") for f in findings)
    assert not any(f["path"].endswith("log.md") for f in findings)
