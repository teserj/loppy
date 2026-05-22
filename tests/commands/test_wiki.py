from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def test_ingest_skill_exists():
    assert (ROOT / "skills" / "ingest" / "SKILL.md").is_file()


def test_query_skill_exists():
    assert (ROOT / "skills" / "query" / "SKILL.md").is_file()


def test_lint_skill_exists():
    assert (ROOT / "skills" / "lint" / "SKILL.md").is_file()


def test_ingest_skill_references_loppy_next():
    content = (ROOT / "skills" / "ingest" / "SKILL.md").read_text(encoding="utf-8")
    assert "loppy next" in content


def test_ingest_skill_references_loppy_move():
    content = (ROOT / "skills" / "ingest" / "SKILL.md").read_text(encoding="utf-8")
    assert "loppy move" in content


def test_ingest_skill_references_loppy_log():
    content = (ROOT / "skills" / "ingest" / "SKILL.md").read_text(encoding="utf-8")
    assert "loppy log" in content


def test_lint_skill_references_lint_frontmatter():
    content = (ROOT / "skills" / "lint" / "SKILL.md").read_text(encoding="utf-8")
    assert "loppy lint-frontmatter" in content
