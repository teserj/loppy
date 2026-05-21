# Cross-Platform Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every bash script in Loppy with Python 3 so the plugin runs natively on Windows, Linux, and macOS using `uv` as the executor.

**Architecture:** `bin/loppy` becomes a Python 3 script (same filename, no `.py` extension) with a uv shebang; a companion `bin/loppy.cmd` wraps it for Windows. All six subcommands are ported 1:1 using only the stdlib. Bats tests are replaced with pytest tests that call the CLI via `subprocess.run([sys.executable, bin/loppy, ...])`.

**Tech Stack:** Python 3.10+, uv, pytest, stdlib only (pathlib, json, re, shutil, tempfile, subprocess, datetime, sys, os)

---

## File Map

| Action | Path |
|--------|------|
| Rewrite | `bin/loppy` (bash → Python) |
| Create | `bin/loppy.cmd` |
| Create | `tests/conftest.py` |
| Create | `tests/loppy/test_config.py` |
| Create | `tests/loppy/test_next.py` |
| Create | `tests/loppy/test_move.py` |
| Create | `tests/loppy/test_index_merge.py` |
| Create | `tests/loppy/test_log.py` |
| Create | `tests/loppy/test_lint_frontmatter.py` |
| Rewrite | `hooks/guard_vault.py` (replaces `guard-vault.sh`) |
| Update | `hooks/hooks.json` |
| Create | `tests/guard/test_guard_vault.py` |
| Rewrite | `setup.py` (replaces `setup.sh`) |
| Create | `tests/setup/test_setup.py` |
| Rewrite | `scripts/validate.py` (replaces `validate.sh`) |
| Create | `tests/manifest/test_manifest.py` |
| Create | `tests/docs/test_docs.py` |
| Create | `tests/templates/test_templates.py` |
| Create | `tests/commands/test_wiki.py` |
| Create | `tests/ci/test_ci.py` |
| Create | `tests/e2e/test_e2e.py` |
| Update | `.github/workflows/ci.yml` |
| Delete | `bin/loppy` (bash), `setup.sh`, `hooks/guard-vault.sh`, `scripts/validate.sh`, `tests/**/*.bats`, `tests/helpers/setup.bash` |

---

## Task 0: Project Scaffolding

**Files:**
- Create: `tests/conftest.py`
- Create: `bin/loppy.cmd`
- Rewrite: `bin/loppy` (skeleton only — functions stubbed)

- [ ] **Step 1: Write `tests/conftest.py`**

```python
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
```

- [ ] **Step 2: Write skeleton `bin/loppy`**

Replace entire file content:

```python
#!/usr/bin/env -S uv run python3
# /// script
# requires-python = ">=3.10"
# ///
import json
import os
import re
import shutil
import sys
import tempfile
import subprocess
from datetime import date, timedelta
from pathlib import Path


def config_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "loppy" / "config.json"


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        print("loppy: config not found. Run setup.py first.", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"loppy: malformed config JSON at {path}", file=sys.stderr)
        sys.exit(1)


def cmd_config(args): pass
def cmd_next(args): pass
def cmd_move(args): pass
def cmd_index_merge(args): pass
def cmd_log(args): pass
def cmd_lint_frontmatter(args): pass


def usage():
    print("""\
loppy — mechanics helper for the Loppy plugin.

Usage:
  loppy config [key]              Print config JSON or a single value.
  loppy next [N]                  List up to N unprocessed source files.
  loppy move <file>               Move a source into processed/.
  loppy index-merge               Merge stdin JSON [{path, summary}...] into wiki/index.md.
  loppy log <op> <title>          Prepend a new log entry (body on stdin).
  loppy lint-frontmatter          Emit JSON findings for every wiki page.
""")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        usage()
        return
    sub, rest = args[0], args[1:]
    dispatch = {
        "config": cmd_config,
        "next": cmd_next,
        "move": cmd_move,
        "index-merge": cmd_index_merge,
        "log": cmd_log,
        "lint-frontmatter": cmd_lint_frontmatter,
    }
    if sub not in dispatch:
        print(f"loppy: unknown subcommand: {sub}", file=sys.stderr)
        usage()
        sys.exit(1)
    dispatch[sub](rest)


if __name__ == "__main__":
    main()
```

On Unix, make it executable:
```bash
chmod +x bin/loppy
```

- [ ] **Step 3: Write `bin/loppy.cmd`**

```bat
@echo off
uv run "%~dp0loppy" %*
```

- [ ] **Step 4: Verify Python executes the skeleton**

```bash
python bin/loppy --help
```

Expected output contains `loppy — mechanics helper`.

- [ ] **Step 5: Commit scaffolding**

```bash
git add tests/conftest.py bin/loppy bin/loppy.cmd
git commit -m "chore: add Python skeleton and test conftest for cross-platform port"
```

---

## Task 1: `cmd_config`

**Files:**
- Create: `tests/loppy/test_config.py`
- Modify: `bin/loppy` (implement `cmd_config`)

- [ ] **Step 1: Write `tests/loppy/test_config.py`**

```python
import json
import pytest
from conftest import run_loppy


def test_config_prints_full_json(loppy_env):
    env, vault = loppy_env
    result = run_loppy("config", env=env)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "vault_dir" in data
    assert "batch_size" in data


def test_config_returns_scalar_value(loppy_env):
    env, vault = loppy_env
    result = run_loppy("config", "batch_size", env=env)
    assert result.returncode == 0
    assert result.stdout.strip() == "5"


def test_config_returns_string_value(loppy_env):
    env, vault = loppy_env
    result = run_loppy("config", "vault_dir", env=env)
    assert result.returncode == 0
    assert result.stdout.strip() == str(vault)


def test_config_exits_1_when_config_missing(loppy_env, tmp_path):
    env, vault = loppy_env
    # Remove config file
    import os
    cfg = (tmp_path / "xdg" / "loppy" / "config.json") if os.name != "nt" \
        else (tmp_path / "appdata" / "loppy" / "config.json")
    cfg.unlink()
    result = run_loppy("config", env=env)
    assert result.returncode == 1
    assert "config not found" in result.stderr


def test_config_exits_1_on_malformed_json(loppy_env, tmp_path):
    env, vault = loppy_env
    import os
    cfg = (tmp_path / "xdg" / "loppy" / "config.json") if os.name != "nt" \
        else (tmp_path / "appdata" / "loppy" / "config.json")
    cfg.write_text("not json {{", encoding="utf-8")
    result = run_loppy("config", env=env)
    assert result.returncode == 1


def test_config_exits_1_on_unknown_key(loppy_env):
    env, vault = loppy_env
    result = run_loppy("config", "no_such_key", env=env)
    assert result.returncode == 1
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/loppy/test_config.py -v
```

Expected: all 6 tests FAIL (cmd_config does nothing, returns None).

- [ ] **Step 3: Implement `cmd_config` in `bin/loppy`**

Replace the `cmd_config` stub:

```python
def cmd_config(args):
    cfg = load_config()
    if not args:
        print(json.dumps(cfg, indent=2))
        return
    key = args[0]
    if key not in cfg:
        print(f"loppy: config key not found: {key}", file=sys.stderr)
        sys.exit(1)
    print(cfg[key])
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/loppy/test_config.py -v
```

Expected: all 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add bin/loppy tests/loppy/test_config.py
git commit -m "feat: port cmd_config to Python with pytest coverage"
```

---

## Task 2: `cmd_next`

**Files:**
- Create: `tests/loppy/test_next.py`
- Modify: `bin/loppy` (implement `cmd_next`)

- [ ] **Step 1: Write `tests/loppy/test_next.py`**

```python
import pytest
from conftest import run_loppy


def test_next_empty_sources_returns_empty(loppy_env):
    env, vault = loppy_env
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_next_uses_batch_size_by_default(loppy_env):
    env, vault = loppy_env
    for i in range(7):
        (vault / "sources" / f"file{i:02d}.md").write_text("x", encoding="utf-8")
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    assert len(result.stdout.strip().splitlines()) == 5


def test_next_limits_to_n(loppy_env):
    env, vault = loppy_env
    for i in range(7):
        (vault / "sources" / f"file{i:02d}.md").write_text("x", encoding="utf-8")
    result = run_loppy("next", "2", env=env)
    assert result.returncode == 0
    assert len(result.stdout.strip().splitlines()) == 2


def test_next_excludes_processed_subdir(loppy_env):
    env, vault = loppy_env
    (vault / "sources" / "keep.md").write_text("x", encoding="utf-8")
    (vault / "sources" / "processed" / "already.md").write_text("x", encoding="utf-8")
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    assert "keep.md" in result.stdout
    assert "already.md" not in result.stdout


def test_next_includes_txt_files(loppy_env):
    env, vault = loppy_env
    (vault / "sources" / "file1.md").write_text("x", encoding="utf-8")
    (vault / "sources" / "file2.txt").write_text("x", encoding="utf-8")
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    assert "file1.md" in result.stdout
    assert "file2.txt" in result.stdout


def test_next_returns_absolute_paths(loppy_env):
    env, vault = loppy_env
    (vault / "sources" / "test.md").write_text("x", encoding="utf-8")
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    line = result.stdout.strip().splitlines()[0]
    assert line.startswith("/") or (len(line) > 2 and line[1] == ":")  # Unix abs or Windows C:\...


def test_next_produces_sorted_output(loppy_env):
    env, vault = loppy_env
    for name in ["zebra.md", "apple.md", "banana.md"]:
        (vault / "sources" / name).write_text("x", encoding="utf-8")
    result = run_loppy("next", env=env)
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert "apple.md" in lines[0]
    assert "zebra.md" in lines[-1]
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/loppy/test_next.py -v
```

Expected: all 7 tests FAIL.

- [ ] **Step 3: Implement `cmd_next` in `bin/loppy`**

Replace the `cmd_next` stub:

```python
def cmd_next(args):
    cfg = load_config()
    n = int(args[0]) if args else int(cfg.get("batch_size", 5))
    sources_dir = Path(cfg["sources_dir"])
    files = sorted(
        [f for f in sources_dir.glob("*.md") if f.is_file()]
        + [f for f in sources_dir.glob("*.txt") if f.is_file()],
        key=lambda f: str(f),
    )
    for f in files[:n]:
        print(str(f))
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/loppy/test_next.py -v
```

Expected: all 7 PASS.

- [ ] **Step 5: Commit**

```bash
git add bin/loppy tests/loppy/test_next.py
git commit -m "feat: port cmd_next to Python with pytest coverage"
```

---

## Task 3: `cmd_move`

**Files:**
- Create: `tests/loppy/test_move.py`
- Modify: `bin/loppy` (implement `cmd_move`)

- [ ] **Step 1: Write `tests/loppy/test_move.py`**

```python
import pytest
from conftest import run_loppy


def test_move_relocates_file(loppy_env):
    env, vault = loppy_env
    src = vault / "sources" / "note.md"
    src.write_text("hello", encoding="utf-8")
    result = run_loppy("move", str(src), env=env)
    assert result.returncode == 0
    assert not src.exists()
    dest = vault / "sources" / "processed" / "note.md"
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "hello"


def test_move_creates_processed_dir_if_missing(loppy_env):
    env, vault = loppy_env
    processed = vault / "sources" / "processed"
    for p in processed.iterdir():
        pass  # just ensure it's accessible; remove dir:
    import shutil
    shutil.rmtree(processed)
    assert not processed.exists()
    src = vault / "sources" / "new.md"
    src.write_text("data", encoding="utf-8")
    result = run_loppy("move", str(src), env=env)
    assert result.returncode == 0
    assert processed.is_dir()
    assert (processed / "new.md").exists()


def test_move_refuses_if_dest_exists(loppy_env):
    env, vault = loppy_env
    src = vault / "sources" / "note.md"
    src.write_text("original", encoding="utf-8")
    (vault / "sources" / "processed" / "note.md").write_text("existing", encoding="utf-8")
    result = run_loppy("move", str(src), env=env)
    assert result.returncode != 0
    assert "destination exists" in result.stderr
    assert src.exists()


def test_move_fails_if_source_missing(loppy_env):
    env, vault = loppy_env
    result = run_loppy("move", str(vault / "sources" / "nonexistent.md"), env=env)
    assert result.returncode != 0
    assert "source not found" in result.stderr


def test_move_requires_argument(loppy_env):
    env, vault = loppy_env
    result = run_loppy("move", env=env)
    assert result.returncode != 0
    assert "source path required" in result.stderr


def test_move_uses_git_mv_in_git_vault(loppy_env):
    import subprocess as sp
    env, vault = loppy_env
    # Init git repo in vault
    sp.run(["git", "-C", str(vault), "init", "-q"], check=True)
    sp.run(["git", "-C", str(vault), "config", "user.email", "t@t.com"], check=True)
    sp.run(["git", "-C", str(vault), "config", "user.name", "Test"], check=True)
    src = vault / "sources" / "tracked.md"
    src.write_text("content", encoding="utf-8")
    sp.run(["git", "-C", str(vault), "add", str(src)], check=True)
    sp.run(["git", "-C", str(vault), "commit", "-q", "-m", "add tracked"], check=True)
    result = run_loppy("move", str(src), env=env)
    assert result.returncode == 0
    assert not src.exists()
    assert (vault / "sources" / "processed" / "tracked.md").exists()
    status = sp.run(
        ["git", "-C", str(vault), "status", "--short"],
        capture_output=True, text=True
    )
    assert "R" in status.stdout
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/loppy/test_move.py -v
```

Expected: all 6 tests FAIL.

- [ ] **Step 3: Implement `cmd_move` in `bin/loppy`**

Replace the `cmd_move` stub:

```python
def cmd_move(args):
    if not args:
        print("loppy move: source path required", file=sys.stderr)
        sys.exit(1)
    src = Path(args[0])
    if not src.exists():
        print(f"loppy move: source not found: {src}", file=sys.stderr)
        sys.exit(1)
    cfg = load_config()
    sources_dir = Path(cfg["sources_dir"])
    vault_dir = Path(cfg["vault_dir"])
    processed = sources_dir / "processed"
    dest = processed / src.name
    if dest.exists():
        print(f"loppy move: destination exists: {dest}", file=sys.stderr)
        sys.exit(1)
    processed.mkdir(parents=True, exist_ok=True)
    # Use git mv if the file is tracked
    try:
        r = subprocess.run(
            ["git", "-C", str(vault_dir), "ls-files", "--error-unmatch", "--", str(src)],
            capture_output=True,
        )
        if r.returncode == 0:
            subprocess.run(
                ["git", "-C", str(vault_dir), "mv", str(src), str(dest)],
                check=True,
            )
            return
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    shutil.move(str(src), str(dest))
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/loppy/test_move.py -v
```

Expected: all 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add bin/loppy tests/loppy/test_move.py
git commit -m "feat: port cmd_move to Python with pytest coverage"
```

---

## Task 4: `cmd_index_merge`

**Files:**
- Create: `tests/loppy/test_index_merge.py`
- Modify: `bin/loppy` (implement `_index_sections`, `cmd_index_merge`)

- [ ] **Step 1: Write `tests/loppy/test_index_merge.py`**

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/loppy/test_index_merge.py -v
```

Expected: all 6 FAIL.

- [ ] **Step 3: Implement `_index_sections` and `cmd_index_merge` in `bin/loppy`**

Replace the `cmd_index_merge` stub (add `_index_sections` above it):

```python
def _index_sections():
    return [
        ("concepts", "## Concepts"),
        ("entities", "## Entities"),
        ("sources", "## Sources"),
        ("topics", "## Topics"),
    ]


def cmd_index_merge(args):
    cfg = load_config()
    wiki_dir = Path(cfg["wiki_dir"])
    idx = wiki_dir / "index.md"
    if not idx.exists():
        print(f"loppy index-merge: {idx} not found", file=sys.stderr)
        sys.exit(1)

    today = os.environ.get("LOPPY_TODAY", date.today().isoformat())

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("loppy index-merge: stdin is not valid JSON", file=sys.stderr)
        sys.exit(1)

    # Parse existing entries: "- [[wiki/ns/slug]] — summary (updated: date)"
    existing: dict[str, str] = {}
    pattern = re.compile(
        r"^- \[\[wiki/([^\]]+)\]\]\s*—\s*(.*?)\s*\(updated:[^)]+\)\s*$"
    )
    for line in idx.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            existing[f"wiki/{m.group(1)}.md"] = m.group(2)

    # Upsert payload entries
    for entry in payload:
        existing[entry["path"]] = entry["summary"]

    # Orphan detection: .md files on disk not in merged map
    on_disk = {
        "wiki/" + f.relative_to(wiki_dir).as_posix()
        for f in wiki_dir.rglob("*.md")
        if f.name not in ("index.md", "log.md")
    }
    for p in sorted(on_disk):
        if p not in existing:
            print(f"loppy index-merge: orphan: {p}", file=sys.stderr)

    total = len(existing)

    lines = [
        "---",
        "type: index",
        "title: Wiki Index",
        f"updated: {today}",
        "---",
        "",
        "# Wiki Index",
        "",
        "Catalog of all wiki pages. Updated on every ingest. Read this first when answering queries.",
        "",
        f"Total pages: {total}",
    ]

    for ns, heading in _index_sections():
        lines.append("")
        lines.append(heading)
        section = sorted(
            [(p, s) for p, s in existing.items() if p.startswith(f"wiki/{ns}/")],
            key=lambda x: x[0],
        )
        if section:
            lines.append("")
            for path, summary in section:
                slug = path[: -len(".md")]
                lines.append(f"- [[{slug}]] — {summary} (updated: {today})")

    content = "\n".join(lines) + "\n"

    tmp = wiki_dir / f".tmp_index_{os.getpid()}"
    try:
        tmp.write_text(content, encoding="utf-8", newline="\n" if hasattr(tmp, "open") else None)
        # Use open() for newline control on Windows
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        tmp.replace(idx)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
```

> **Note:** The double-write above is redundant. Use only the `open()` form:

```python
    tmp = wiki_dir / f".tmp_index_{os.getpid()}"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        tmp.replace(idx)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/loppy/test_index_merge.py -v
```

Expected: all 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add bin/loppy tests/loppy/test_index_merge.py
git commit -m "feat: port cmd_index_merge to Python with pytest coverage"
```

---

## Task 5: `cmd_log`

**Files:**
- Create: `tests/loppy/test_log.py`
- Modify: `bin/loppy` (implement `cmd_log`)

- [ ] **Step 1: Write `tests/loppy/test_log.py`**

```python
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
    log.write_text(LOG_INITIAL, encoding="utf-8", newline="\n") if hasattr(log, "open") else \
        open(log, "w", encoding="utf-8", newline="\n").write(LOG_INITIAL)
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/loppy/test_log.py -v
```

Expected: all 7 FAIL.

- [ ] **Step 3: Implement `cmd_log` in `bin/loppy`**

Replace the `cmd_log` stub:

```python
def cmd_log(args):
    if len(args) < 2:
        print("loppy log: usage: loppy log <op> <title>   (body from stdin)", file=sys.stderr)
        sys.exit(1)
    op, title = args[0], args[1]
    cfg = load_config()
    wiki_dir = Path(cfg["wiki_dir"])
    logf = wiki_dir / "log.md"
    if not logf.exists():
        print(f"loppy log: {logf} not found", file=sys.stderr)
        sys.exit(1)
    today = os.environ.get("LOPPY_TODAY", date.today().isoformat())
    body = sys.stdin.read().rstrip("\n")

    lines = logf.read_text(encoding="utf-8").splitlines()

    # Find first "---" that appears after first "# " line
    sep_line = None
    found_h1 = False
    for i, line in enumerate(lines):
        if line.startswith("# "):
            found_h1 = True
        elif found_h1 and line == "---":
            sep_line = i
            break

    new_entry = f"\n## [{today}] {op} | {title}\n\n{body}\n"

    if sep_line is None:
        new_content = "\n".join(lines) + "\n" + f"\n---\n{new_entry}"
    else:
        header = "\n".join(lines[: sep_line + 1]) + "\n"
        rest_lines = lines[sep_line + 1 :]
        rest = "\n".join(rest_lines)
        if rest:
            rest += "\n"
        new_content = header + new_entry + rest

    tmp = wiki_dir / f".tmp_log_{os.getpid()}"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content)
        tmp.replace(logf)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/loppy/test_log.py -v
```

Expected: all 7 PASS.

- [ ] **Step 5: Commit**

```bash
git add bin/loppy tests/loppy/test_log.py
git commit -m "feat: port cmd_log to Python with pytest coverage"
```

---

## Task 6: Frontmatter Parser + Date Helper

**Files:**
- Modify: `bin/loppy` (add `_parse_frontmatter`, `_days_since`, enum constants)

These are building blocks for Task 7. No standalone test file — they're exercised via `test_lint_frontmatter.py`.

- [ ] **Step 1: Add constants and helpers to `bin/loppy`**

Add these definitions above the `cmd_lint_frontmatter` stub:

```python
_ALLOWED_TYPES = frozenset(
    "entity concept source project thought todo worklog".split()
)
_ALLOWED_DOMAINS = frozenset(
    "tech finance business work career hobbies family parenting relationships self".split()
)
_ALLOWED_CONFIDENCE = frozenset("high medium low stale".split())
_REQUIRED_FIELDS = "type title created updated confidence domain tags links".split()


def _parse_frontmatter(file: Path) -> dict:
    """Parse YAML-subset frontmatter into a dict.
    Supports: scalar values and inline arrays  key: [a, b, c].
    Does NOT support block sequences (- item).
    """
    text = file.read_text(encoding="utf-8")
    fm: dict = {}
    inside = False
    started = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---":
            if not started:
                inside = True
                started = True
                continue
            else:
                break
        if not inside:
            continue
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                fm[key] = []
            else:
                fm[key] = [x.strip().strip('"') for x in inner.split(",")]
        else:
            fm[key] = val
    return fm


def _days_since(d: str) -> int | None:
    today_str = os.environ.get("LOPPY_TODAY", date.today().isoformat())
    try:
        return (date.fromisoformat(today_str) - date.fromisoformat(d)).days
    except ValueError:
        return None
```

- [ ] **Step 2: Verify syntax only (no test yet)**

```bash
python -c "import importlib.util, pathlib; \
  s=importlib.util.spec_from_file_location('loppy','bin/loppy'); \
  m=importlib.util.module_from_spec(s); s.loader.exec_module(m); \
  print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add bin/loppy
git commit -m "feat: add _parse_frontmatter and _days_since helpers for lint command"
```

---

## Task 7: `cmd_lint_frontmatter`

**Files:**
- Create: `tests/loppy/test_lint_frontmatter.py`
- Modify: `bin/loppy` (implement `cmd_lint_frontmatter`)

- [ ] **Step 1: Write `tests/loppy/test_lint_frontmatter.py`**

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/loppy/test_lint_frontmatter.py -v
```

Expected: all 8 FAIL.

- [ ] **Step 3: Implement `cmd_lint_frontmatter` in `bin/loppy`**

Replace the `cmd_lint_frontmatter` stub:

```python
def cmd_lint_frontmatter(args):
    cfg = load_config()
    wiki_dir = Path(cfg["wiki_dir"])

    existing = {
        f.relative_to(wiki_dir).as_posix()[: -len(".md")]
        for f in wiki_dir.rglob("*.md")
        if f.name not in ("index.md", "log.md")
    }

    index_paths: set[str] = set()
    index_file = wiki_dir / "index.md"
    if index_file.exists():
        for m in re.finditer(r"\[\[wiki/([^\]]+)\]\]", index_file.read_text(encoding="utf-8")):
            index_paths.add(m.group(1))

    results = []

    for rel in sorted(existing):
        file = wiki_dir / (rel + ".md")
        fm = _parse_frontmatter(file)
        findings = []

        for field in _REQUIRED_FIELDS:
            if field not in fm:
                findings.append({"level": "error", "rule": "missing-field", "field": field})

        for field, allowed in [
            ("type", _ALLOWED_TYPES),
            ("domain", _ALLOWED_DOMAINS),
            ("confidence", _ALLOWED_CONFIDENCE),
        ]:
            val = fm.get(field, "")
            if val and val not in allowed:
                findings.append({"level": "error", "rule": "bad-enum", "field": field, "value": val})

        upd = fm.get("updated", "")
        conf = fm.get("confidence", "")
        if upd and conf != "stale":
            age = _days_since(upd)
            if age is not None and age > 90:
                findings.append({"level": "warn", "rule": "stale", "age_days": age})

        if rel not in index_paths:
            findings.append({"level": "warn", "rule": "orphan"})

        links = fm.get("links", [])
        if isinstance(links, list):
            for link in links:
                target = link[len("wiki/"):] if link.startswith("wiki/") else link
                if target not in existing:
                    findings.append({"level": "error", "rule": "broken-link", "target": link})

        if findings:
            results.append({"path": f"wiki/{rel}.md", "findings": findings})

    print(json.dumps(results, indent=2))
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/loppy/test_lint_frontmatter.py -v
```

Expected: all 8 PASS.

- [ ] **Step 5: Run full loppy suite to confirm no regressions**

```bash
uv run pytest tests/loppy/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add bin/loppy tests/loppy/test_lint_frontmatter.py
git commit -m "feat: port cmd_lint_frontmatter to Python with pytest coverage"
```

---

## Task 8: `guard_vault.py` + `hooks.json`

**Files:**
- Create: `hooks/guard_vault.py`
- Update: `hooks/hooks.json`
- Create: `tests/guard/test_guard_vault.py`

- [ ] **Step 1: Write `tests/guard/test_guard_vault.py`**

```python
import json
import os
import sys
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
GUARD_SCRIPT = REPO_ROOT / "hooks" / "guard_vault.py"


def run_guard(payload: dict, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GUARD_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
def guard_env(loppy_env):
    env, vault = loppy_env
    return env, vault


def test_guard_allows_loppy_command(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": "loppy config"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_blocks_rm_targeting_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": f"rm -rf {vault}/file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_mv_within_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": f"mv {vault}/a.md {vault}/b.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_shred_in_wiki(guard_env):
    env, vault = guard_env
    wiki = str(vault / "wiki")
    r = run_guard({"tool": "bash", "command": f"shred -vfz {wiki}/page.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_allows_find_in_vault(guard_env):
    env, vault = guard_env
    sources = str(vault / "sources")
    r = run_guard({"tool": "bash", "command": f'find {sources} -name "*.md"'}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_allows_git_mv(guard_env):
    env, vault = guard_env
    sources = str(vault / "sources")
    r = run_guard({"tool": "bash", "command": f"git mv {sources}/a.md {sources}/b.md"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_allows_git_rm(guard_env):
    env, vault = guard_env
    wiki = str(vault / "wiki")
    r = run_guard({"tool": "bash", "command": f"git rm {wiki}/page.md"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_blocks_rmdir_in_vault(guard_env):
    env, vault = guard_env
    wiki = str(vault / "wiki")
    r = run_guard({"tool": "bash", "command": f"rmdir {wiki}/subdir"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_dd_in_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": f"dd if=/dev/zero of={vault}/file.txt"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_unlink_in_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": f"unlink {vault}/file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_allows_non_bash_tool(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "read", "file_path": "/some/file.txt"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_allows_write_tool(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "write", "file_path": "/some/file.txt", "content": "test"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_fails_open_when_config_missing(guard_env, tmp_path):
    env, vault = guard_env
    # Remove config
    import os as _os
    cfg = (tmp_path / "xdg" / "loppy" / "config.json") if _os.name != "nt" \
        else (tmp_path / "appdata" / "loppy" / "config.json")
    if cfg.exists():
        cfg.unlink()
    r = run_guard({"tool": "bash", "command": f"rm -rf /tmp/unrelated"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_allows_rm_outside_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": "rm -rf /tmp/unrelated/file.txt"}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_passes_on_empty_command(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": ""}, env)
    assert r.returncode == 0
    assert r.stdout.strip() == "PASS"


def test_guard_passes_on_malformed_json(guard_env):
    env, vault = guard_env
    result = subprocess.run(
        [sys.executable, str(GUARD_SCRIPT)],
        input="not valid json",
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "PASS"


def test_guard_blocks_var_reference_to_vault(guard_env):
    env, vault = guard_env
    r = run_guard({"tool": "bash", "command": "rm -rf $VAULT_DIR/sensitive.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout


def test_guard_blocks_rm_with_sources_path(guard_env):
    env, vault = guard_env
    sources = str(vault / "sources")
    r = run_guard({"tool": "bash", "command": f"rm {sources}/file.md"}, env)
    assert r.returncode == 2
    assert "BLOCK" in r.stdout
```

- [ ] **Step 2: Run tests — expect failure (guard_vault.py doesn't exist yet)**

```bash
uv run pytest tests/guard/test_guard_vault.py -v
```

Expected: all 17 FAIL or ERROR (file not found).

- [ ] **Step 3: Create `hooks/guard_vault.py`**

```python
#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path


def config_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "loppy" / "config.json"


def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        print("PASS")
        sys.exit(0)

    if not isinstance(data, dict):
        print("PASS")
        sys.exit(0)

    if data.get("tool") != "bash":
        print("PASS")
        sys.exit(0)

    command = data.get("command", "")
    if not command:
        print("PASS")
        sys.exit(0)

    cfg_file = config_path()
    if not cfg_file.exists():
        print("PASS")
        sys.exit(0)

    try:
        cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
    except Exception:
        print("PASS")
        sys.exit(0)

    vault_dir = cfg.get("vault_dir", "")
    sources_dir = cfg.get("sources_dir", "")
    wiki_dir = cfg.get("wiki_dir", "")

    if not any([vault_dir, sources_dir, wiki_dir]):
        print("PASS")
        sys.exit(0)

    # Allowlist: loppy commands and git mv/rm
    if re.match(r"^loppy", command) or re.search(r"git\s+(mv|rm)", command):
        print("PASS")
        sys.exit(0)

    def vault_referenced(cmd: str) -> bool:
        for path in [vault_dir, sources_dir, wiki_dir]:
            if path and path in cmd:
                return True
        return any(v in cmd for v in ["$VAULT_DIR", "$SOURCES_DIR", "$WIKI_DIR"])

    block_msg = "BLOCK: Destructive operation on vault detected. Use 'loppy move' for file operations."

    if re.search(r"(^|\s)(rm|rmdir|shred|unlink)(\s|-)", command):
        if vault_referenced(command):
            print(block_msg)
            sys.exit(2)

    if re.search(r"(^|\s)mv(\s|-)", command):
        if vault_referenced(command):
            print(block_msg)
            sys.exit(2)

    if re.search(r"(^|\s)dd(\s|-)", command):
        if vault_referenced(command):
            print(block_msg)
            sys.exit(2)

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

Make executable on Unix:
```bash
chmod +x hooks/guard_vault.py
```

- [ ] **Step 4: Update `hooks/hooks.json`**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "uv run hooks/guard_vault.py"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Run tests — expect pass**

```bash
uv run pytest tests/guard/test_guard_vault.py -v
```

Expected: all 17 PASS.

- [ ] **Step 6: Commit**

```bash
git add hooks/guard_vault.py hooks/hooks.json tests/guard/test_guard_vault.py
git commit -m "feat: port guard_vault hook to Python, update hooks.json"
```

---

## Task 9: `setup.py`

**Files:**
- Create: `setup.py`
- Create: `tests/setup/test_setup.py`

- [ ] **Step 1: Write `tests/setup/test_setup.py`**

```python
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SETUP_SCRIPT = REPO_ROOT / "setup.py"


def run_setup(inputs: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SETUP_SCRIPT)],
        input=inputs,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
def setup_env(tmp_path):
    env = dict(os.environ)
    if os.name == "nt":
        env["APPDATA"] = str(tmp_path / "appdata")
    else:
        env["XDG_CONFIG_HOME"] = str(tmp_path / "xdg")
    env["HOME"] = str(tmp_path)
    return env, tmp_path


def _vault_inputs(vault: Path, sources="source", wiki="wiki", git="n") -> str:
    return f"{vault}\n{sources}\n{wiki}\n{git}\n"


def test_setup_creates_config(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault), env)
    if os.name == "nt":
        cfg = tmp / "appdata" / "loppy" / "config.json"
    else:
        cfg = tmp / "xdg" / "loppy" / "config.json"
    assert cfg.exists()


def test_setup_config_has_correct_keys(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault), env)
    if os.name == "nt":
        cfg = tmp / "appdata" / "loppy" / "config.json"
    else:
        cfg = tmp / "xdg" / "loppy" / "config.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert "vault_dir" in data
    assert "sources_dir" in data
    assert "wiki_dir" in data
    assert "batch_size" in data


def test_setup_sources_dir_defaults_to_source(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault, sources=""), env)
    if os.name == "nt":
        cfg = tmp / "appdata" / "loppy" / "config.json"
    else:
        cfg = tmp / "xdg" / "loppy" / "config.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["sources_dir"] == str(vault / "source")


def test_setup_wiki_dir_defaults_to_wiki(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault, wiki=""), env)
    if os.name == "nt":
        cfg = tmp / "appdata" / "loppy" / "config.json"
    else:
        cfg = tmp / "xdg" / "loppy" / "config.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["wiki_dir"] == str(vault / "wiki")


def test_setup_batch_size_defaults_to_5(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault), env)
    if os.name == "nt":
        cfg = tmp / "appdata" / "loppy" / "config.json"
    else:
        cfg = tmp / "xdg" / "loppy" / "config.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["batch_size"] == 5


def test_setup_copies_templates(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault, wiki="wiki"), env)
    assert (vault / "wiki-schema.yaml").exists()
    assert (vault / "index.md").exists()
    assert (vault / "log.md").exists()


def test_setup_creates_subdirectories(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault, sources="sources", wiki="wiki"), env)
    assert (vault / "sources").is_dir()
    assert (vault / "wiki").is_dir()


def test_setup_initializes_git_when_requested(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault, git="y"), env)
    assert (vault / ".git").is_dir()


def test_setup_installs_binary(setup_env):
    env, tmp = setup_env
    vault = tmp / "vault"
    vault.mkdir()
    run_setup(_vault_inputs(vault), env)
    bin_dir = tmp / ".local" / "bin"
    # On Unix: bin/loppy; on Windows: bin/loppy.cmd
    installed = list(bin_dir.glob("loppy*")) if bin_dir.exists() else []
    assert len(installed) >= 1
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/setup/test_setup.py -v
```

Expected: all 9 FAIL (setup.py doesn't exist yet).

- [ ] **Step 3: Create `setup.py`**

```python
#!/usr/bin/env python3
"""Loppy vault setup — interactive installer."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# ANSI colours — only when stdout is a TTY
def _c(code: str, text: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

RED   = lambda t: _c("0;31", t)
GREEN = lambda t: _c("0;32", t)
BLUE  = lambda t: _c("0;34", t)


def config_base() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))


def main():
    print(BLUE("=== Loppy Vault Setup ==="))
    print()

    # Vault directory
    while True:
        vault_str = input("Enter path to vault directory (required): ").strip()
        if not vault_str:
            print(RED("Error: vault directory is required"))
            continue
        vault_dir = Path(vault_str).resolve()
        vault_dir.mkdir(parents=True, exist_ok=True)
        break

    # Sources and wiki relative paths
    sources_rel = input("Relative path to raw sources (default: source): ").strip() or "source"
    wiki_rel    = input("Relative path to compiled wiki (default: wiki): ").strip() or "wiki"

    sources_abs = vault_dir / sources_rel
    wiki_abs    = vault_dir / wiki_rel
    sources_abs.mkdir(parents=True, exist_ok=True)
    wiki_abs.mkdir(parents=True, exist_ok=True)
    print(f"Created subdirectories: {sources_rel}/, {wiki_rel}/")
    print()

    # Write config
    cfg_dir = config_base() / "loppy"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = cfg_dir / "config.json"
    cfg_file.write_text(
        json.dumps(
            {
                "vault_dir": str(vault_dir),
                "sources_dir": str(sources_abs),
                "wiki_dir": str(wiki_abs),
                "batch_size": 5,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Config saved: {cfg_file}")
    print()

    # Copy templates
    tmpl_dir = SCRIPT_DIR / "templates"
    if tmpl_dir.is_dir():
        for name in ["wiki-schema.yaml", "index.md", "log.md"]:
            src = tmpl_dir / name
            if src.exists():
                shutil.copy(src, vault_dir / wiki_rel / name if name != "wiki-schema.yaml" else vault_dir / name)
        # index.md and log.md go into wiki_dir; wiki-schema.yaml goes into vault root
        shutil.copy(tmpl_dir / "wiki-schema.yaml", vault_dir / "wiki-schema.yaml")
        shutil.copy(tmpl_dir / "index.md",         wiki_abs / "index.md")
        shutil.copy(tmpl_dir / "log.md",           wiki_abs / "log.md")
        print("Templates copied to vault")
    else:
        print(RED("Warning: templates directory not found"))
    print()

    # Install binary
    print("Installing loppy binary...")
    home = Path(os.environ.get("HOME", str(Path.home())))
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    src_bin = SCRIPT_DIR / "bin" / "loppy"
    if src_bin.exists():
        if os.name == "nt":
            dest = bin_dir / "loppy.cmd"
            src_cmd = SCRIPT_DIR / "bin" / "loppy.cmd"
            if src_cmd.exists():
                shutil.copy(src_cmd, dest)
        else:
            dest = bin_dir / "loppy"
            shutil.copy(src_bin, dest)
            dest.chmod(dest.stat().st_mode | 0o111)
        print(f"Binary installed: {dest}")
    else:
        print(RED("Warning: bin/loppy not found"))
    print()

    # Git init
    if not (vault_dir / ".git").exists():
        answer = input("Initialize git repository in vault? (y/n): ").strip().lower()
        if answer.startswith("y"):
            subprocess.run(["git", "init", str(vault_dir)], check=False)
            print("Git repository initialized")
    else:
        print("Git repository already exists")

    print()
    print(GREEN("=== Setup Complete ==="))
    print(f"Vault:  {vault_dir}")
    print(f"Config: {cfg_file}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/setup/test_setup.py -v
```

Expected: all 9 PASS.

- [ ] **Step 5: Commit**

```bash
git add setup.py tests/setup/test_setup.py
git commit -m "feat: port setup script to Python with pytest coverage"
```

---

## Task 10: `scripts/validate.py`

**Files:**
- Create: `scripts/validate.py`

No new test file — validation is covered by CI.

- [ ] **Step 1: Create `scripts/validate.py`**

```python
#!/usr/bin/env python3
"""Loppy plugin pre-release validation."""
import json
import py_compile
import sys
from pathlib import Path
import subprocess

ROOT = Path(__file__).parent.parent
PASS = "✓"
FAIL = "✗"


def check(label: str, ok: bool) -> bool:
    mark = PASS if ok else FAIL
    print(f"  {mark} {label}")
    return ok


def main():
    print("=== Loppy Plugin Validation ===\n")
    errors = 0

    # Check 1: Essential files
    print("Check 1: Essential files exist")
    required = [
        "setup.py", "bin/loppy", "CLAUDE.md", "README.md",
        ".claude-plugin/plugin.json", "hooks/guard_vault.py",
    ]
    for f in required:
        if not check(f, (ROOT / f).is_file()):
            errors += 1
    print()

    # Check 2: Test count
    print("Check 2: Test coverage")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", str(ROOT / "tests")],
        capture_output=True, text=True, cwd=ROOT,
    )
    test_count = result.stdout.count("::test_")
    if not check(f"{test_count} tests collected (need ≥40)", test_count >= 40):
        errors += 1
    print()

    # Check 3: Plugin manifest
    print("Check 3: Plugin manifest validation")
    manifest_path = ROOT / ".claude-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        check("plugin.json valid JSON", True)
        for field in ["name", "version", "description", "author"]:
            if not check(f"plugin.json has .{field}", field in manifest):
                errors += 1
    except Exception as e:
        check(f"plugin.json readable: {e}", False)
        errors += 1
    print()

    # Check 4: Documentation
    print("Check 4: Documentation completeness")
    for doc, section in [("CLAUDE.md", "## Scope"), ("README.md", "## Architecture")]:
        content = (ROOT / doc).read_text(encoding="utf-8")
        if not check(f"{doc} has '{section}'", section in content):
            errors += 1
    print()

    # Check 5: No temp files
    print("Check 5: Clean working tree")
    temp_files = list(ROOT.rglob("*.tmp")) + list(ROOT.rglob("*.swp"))
    temp_files = [f for f in temp_files if ".git" not in str(f)]
    if not check("No temporary files", len(temp_files) == 0):
        errors += 1
    print()

    # Check 6: Python syntax
    print("Check 6: Python script syntax")
    py_scripts = [ROOT / "bin" / "loppy", ROOT / "setup.py",
                  ROOT / "hooks" / "guard_vault.py", ROOT / "scripts" / "validate.py"]
    for f in py_scripts:
        if f.exists():
            try:
                py_compile.compile(str(f), doraise=True)
                check(str(f.relative_to(ROOT)), True)
            except py_compile.PyCompileError as e:
                check(f"{f.relative_to(ROOT)}: {e}", False)
                errors += 1
    print()

    if errors == 0:
        print("=== All validations passed ===")
    else:
        print(f"=== {errors} validation(s) failed ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it manually to verify**

```bash
uv run scripts/validate.py
```

Expected: all checks pass.

- [ ] **Step 3: Commit**

```bash
git add scripts/validate.py
git commit -m "feat: port validate script to Python"
```

---

## Task 11: Structural Test Files

**Files:**
- Create: `tests/manifest/test_manifest.py`
- Create: `tests/docs/test_docs.py`
- Create: `tests/templates/test_templates.py`
- Create: `tests/commands/test_wiki.py`
- Create: `tests/ci/test_ci.py`
- Create: `tests/e2e/test_e2e.py`

- [ ] **Step 1: Write `tests/manifest/test_manifest.py`**

```python
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
```

- [ ] **Step 2: Write `tests/docs/test_docs.py`**

```python
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
```

- [ ] **Step 3: Write `tests/templates/test_templates.py`**

```python
import yaml
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
```

- [ ] **Step 4: Write `tests/commands/test_wiki.py`**

```python
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
```

- [ ] **Step 5: Write `tests/ci/test_ci.py`**

```python
import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def test_bin_loppy_has_python_shebang():
    first_line = (ROOT / "bin" / "loppy").read_text(encoding="utf-8").splitlines()[0]
    assert "python" in first_line or "uv" in first_line


def test_bin_loppy_cmd_exists():
    assert (ROOT / "bin" / "loppy.cmd").is_file()


def test_bin_loppy_python_syntax():
    py_compile.compile(str(ROOT / "bin" / "loppy"), doraise=True)


def test_guard_vault_python_syntax():
    py_compile.compile(str(ROOT / "hooks" / "guard_vault.py"), doraise=True)


def test_setup_py_python_syntax():
    py_compile.compile(str(ROOT / "setup.py"), doraise=True)


def test_no_hardcoded_home_paths():
    for f in [ROOT / "bin" / "loppy", ROOT / "hooks" / "guard_vault.py"]:
        content = f.read_text(encoding="utf-8")
        assert "/home/" not in content, f"{f} has hardcoded /home/ path"
```

- [ ] **Step 6: Write `tests/e2e/test_e2e.py`**

```python
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
```

- [ ] **Step 7: Run all structural tests**

```bash
uv run pytest tests/manifest/ tests/docs/ tests/templates/ tests/commands/ tests/ci/ tests/e2e/ -v
```

Expected: all tests pass (or skip for optional deps like pyyaml).

- [ ] **Step 8: Commit**

```bash
git add tests/manifest/test_manifest.py tests/docs/test_docs.py \
        tests/templates/test_templates.py tests/commands/test_wiki.py \
        tests/ci/test_ci.py tests/e2e/test_e2e.py
git commit -m "test: add structural pytest tests (manifest, docs, templates, commands, ci, e2e)"
```

---

## Task 12: CI Update + Delete Old Bash Files

**Files:**
- Update: `.github/workflows/ci.yml`
- Delete: `setup.sh`, `hooks/guard-vault.sh`, `scripts/validate.sh`, all `tests/**/*.bats`, `tests/helpers/setup.bash`

- [ ] **Step 1: Run full suite to confirm everything passes before deletion**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass. Do NOT proceed to deletion if any test fails.

- [ ] **Step 2: Update `.github/workflows/ci.yml`**

Replace entire file:

```yaml
name: CI

on:
  push:
    branches: [main, master, develop, "feat/*", "bugfix/*"]
  pull_request:
    branches: [main, master, develop]

jobs:
  test:
    name: Run Tests
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Run tests
        run: uv run pytest tests/ -v

      - name: Validate plugin manifest
        run: |
          python -c "
          import json, sys
          from pathlib import Path
          d = json.loads(Path('.claude-plugin/plugin.json').read_text())
          for f in ['name','version','description','author']:
              assert f in d, f'Missing: {f}'
          print('plugin.json OK')
          "

      - name: Run validation script
        run: uv run scripts/validate.py

  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - name: Check Python syntax
        run: |
          for f in bin/loppy setup.py hooks/guard_vault.py scripts/validate.py; do
            python -m py_compile "$f" && echo "OK: $f"
          done

  doc-check:
    name: Documentation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify commands documented
        run: |
          for cmd in config next move index-merge log lint-frontmatter; do
            grep -q "$cmd" CLAUDE.md || { echo "CLAUDE.md missing: $cmd"; exit 1; }
            grep -q "$cmd" README.md || { echo "README.md missing: $cmd"; exit 1; }
            echo "OK: $cmd"
          done
```

- [ ] **Step 3: Delete old bash files**

```bash
git rm setup.sh
git rm hooks/guard-vault.sh
git rm scripts/validate.sh
git rm tests/helpers/setup.bash
git rm tests/loppy/config.bats tests/loppy/next.bats tests/loppy/move.bats \
       tests/loppy/index-merge.bats tests/loppy/log.bats tests/loppy/lint-frontmatter.bats
git rm tests/guard/guard-vault.bats
git rm tests/setup/setup.bats
git rm tests/manifest/manifest.bats
git rm tests/commands/wiki.bats
git rm tests/docs/docs.bats
git rm tests/templates/templates.bats
git rm tests/ci/ci.bats
git rm tests/e2e/e2e.bats
```

- [ ] **Step 4: Run full suite one final time**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Run validation**

```bash
uv run scripts/validate.py
```

Expected: all checks pass.

- [ ] **Step 6: Commit everything**

```bash
git add .github/workflows/ci.yml
git commit -m "feat: complete cross-platform port — Python replaces all bash scripts, pytest replaces bats"
```

---

## Self-Review Notes

**Spec coverage check:**
- ✅ `bin/loppy` → Python (Tasks 0–7)
- ✅ `bin/loppy.cmd` Windows wrapper (Task 0)
- ✅ `hooks/guard_vault.py` (Task 8)
- ✅ `hooks/hooks.json` updated (Task 8)
- ✅ `setup.py` (Task 9)
- ✅ `scripts/validate.py` (Task 10)
- ✅ All `.bats` → `test_*.py` (Tasks 1–11)
- ✅ `tests/conftest.py` shared fixtures (Task 0)
- ✅ CI matrix for Windows/Linux/macOS (Task 12)
- ✅ Old bash files deleted (Task 12)

**Type/name consistency:**
- `run_loppy()` helper defined in `conftest.py` and used in every test module
- `loppy_env` fixture returns `(env, vault)` tuple — consistent across all test files
- `_index_sections()` returns `list[tuple[str, str]]` — used only in `cmd_index_merge`
- `_parse_frontmatter()` returns `dict` — used only in `cmd_lint_frontmatter`
- `_days_since()` returns `int | None` — used only in `cmd_lint_frontmatter`

**Windows newline note:** All file writes use `open(..., newline="\n")` explicitly to prevent `\r\n` in vault files on Windows.
