import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def test_manifest_exists():
    assert (ROOT / ".claude-plugin" / "plugin.json").is_file()


def test_manifest_valid_json():
    data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_manifest_has_required_fields():
    data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    for field in ["name", "version", "description", "author"]:
        assert field in data, f"Missing field: {field}"


def test_manifest_no_commands_or_hooks():
    data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert "commands" not in data
    assert "slashCommands" not in data


def test_skills_ingest_exists():
    assert (ROOT / "skills" / "ingest" / "SKILL.md").is_file()


def test_skills_query_exists():
    assert (ROOT / "skills" / "query" / "SKILL.md").is_file()


def test_skills_lint_exists():
    assert (ROOT / "skills" / "lint" / "SKILL.md").is_file()


def test_skills_have_description_frontmatter():
    for name in ["ingest", "query", "lint"]:
        content = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert "description:" in content, f"skills/{name}/SKILL.md missing description:"


def test_skills_reference_loppy_commands():
    for name in ["ingest", "query", "lint"]:
        content = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert "loppy" in content, f"skills/{name}/SKILL.md doesn't reference loppy"


def test_hooks_json_exists():
    assert (ROOT / "hooks" / "hooks.json").is_file()


def test_hooks_json_valid():
    data = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_hooks_has_pretooluse_guard():
    data = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert len(data["hooks"]["PreToolUse"]) > 0


def test_hooks_guard_matches_bash():
    data = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert data["hooks"]["PreToolUse"][0]["matcher"] == "Bash"
