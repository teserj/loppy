import json
import os
import sys
from pathlib import Path
import subprocess
import pytest

REPO_ROOT = Path(__file__).parent.parent
LOPPY_BIN = REPO_ROOT / "bin" / "loppy"


def run_loppy(*args, env, stdin=None):
    """Run bin/loppy via the current Python interpreter."""
    return subprocess.run(
        [sys.executable, str(LOPPY_BIN), *args],
        capture_output=True,
        text=True,
        input=stdin,
        env=env,
    )


@pytest.fixture
def vault(tmp_path):
    """Minimal vault directory structure."""
    sources = tmp_path / "sources"
    wiki = tmp_path / "wiki"
    (sources / "processed").mkdir(parents=True)
    wiki.mkdir()
    (wiki / "index.md").write_text(
        "---\ntype: index\ntitle: Wiki Index\nupdated: 2026-01-01\n---\n\n"
        "# Wiki Index\n\nCatalog of all wiki pages. Updated on every ingest. "
        "Read this first when answering queries.\n\nTotal pages: 0\n\n"
        "## Concepts\n\n## Entities\n\n## Sources\n\n## Topics\n",
        encoding="utf-8",
    )
    (wiki / "log.md").write_text(
        "---\ntype: log\ntitle: Wiki Activity Log\n---\n\n"
        "# Wiki Log\n\nAppend-only. New entries at top.\n\n---\n\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def loppy_env(vault, tmp_path):
    """
    Returns (env_dict, vault_path).
    env_dict overrides XDG_CONFIG_HOME/APPDATA to point at a temp config
    containing a valid config.json for the vault fixture.
    """
    if os.name == "nt":
        cfg_dir = tmp_path / "appdata" / "loppy"
    else:
        cfg_dir = tmp_path / "xdg" / "loppy"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(
        json.dumps(
            {
                "vault_dir": str(vault),
                "sources_dir": str(vault / "sources"),
                "wiki_dir": str(vault / "wiki"),
                "batch_size": 5,
            }
        ),
        encoding="utf-8",
    )
    env = dict(os.environ)
    if os.name == "nt":
        env["APPDATA"] = str(tmp_path / "appdata")
    else:
        env["XDG_CONFIG_HOME"] = str(tmp_path / "xdg")
    env["LOPPY_TODAY"] = "2026-05-21"
    return env, vault
