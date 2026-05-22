from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def test_claude_md_exists():
    assert (ROOT / "CLAUDE.md").is_file()


def test_readme_md_exists():
    assert (ROOT / "README.md").is_file()


def test_claude_md_has_scope_section():
    assert "## Scope" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")


def test_claude_md_has_design_section():
    assert "## Design" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")


def test_readme_has_architecture_section():
    assert "## Architecture" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_commands_documented_in_claude_md():
    content = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    for cmd in ["config", "next", "move", "index-merge", "log", "lint-frontmatter"]:
        assert cmd in content, f"CLAUDE.md missing documentation for: {cmd}"


def test_commands_documented_in_readme():
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    for cmd in ["config", "next", "move", "index-merge", "log", "lint-frontmatter"]:
        assert cmd in content, f"README.md missing documentation for: {cmd}"
