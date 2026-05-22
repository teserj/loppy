from pathlib import Path
import pytest

ROOT = Path(__file__).parent.parent.parent
TMPL = ROOT / "templates"


def test_wiki_schema_yaml_exists():
    assert (TMPL / "wiki-schema.yaml").is_file()


def test_index_md_exists():
    assert (TMPL / "index.md").is_file()


def test_log_md_exists():
    assert (TMPL / "log.md").is_file()


def test_index_md_has_frontmatter():
    content = (TMPL / "index.md").read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "type: index" in content


def test_log_md_has_frontmatter():
    content = (TMPL / "log.md").read_text(encoding="utf-8")
    assert content.startswith("---")


def test_wiki_schema_yaml_is_valid_yaml():
    try:
        import yaml
        yaml.safe_load((TMPL / "wiki-schema.yaml").read_text(encoding="utf-8"))
    except ImportError:
        pytest.skip("pyyaml not installed")
    except Exception as e:
        pytest.fail(f"wiki-schema.yaml is not valid YAML: {e}")
