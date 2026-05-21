# Cross-Platform Port Design

**Date:** 2026-05-21
**Status:** Approved
**Scope:** Port all Loppy shell scripts to Python 3 so the plugin runs on Windows, Linux, and macOS without WSL or Git Bash.

---

## Goal

Replace every bash script with a Python 3 equivalent. Use `uv run` as the cross-platform executor. Preserve all existing behavior and test coverage.

---

## Approach

Python 3 + `uv run`. Single codebase for all platforms. Stdlib only — no pip dependencies. `uv run` handles Python version management and works identically on Windows, Linux, and macOS.

---

## File Map

| Old | New | Notes |
|-----|-----|-------|
| `bin/loppy` (bash) | `bin/loppy` | Renamed in-place: Python replaces bash, same filename |
| *(none)* | `bin/loppy.cmd` | Windows batch wrapper calling `bin/loppy` |
| `setup.sh` | `setup.py` | Interactive setup |
| `hooks/guard-vault.sh` | `hooks/guard_vault.py` | PreToolUse hook |
| `hooks/hooks.json` | `hooks/hooks.json` | Updated command path |
| `scripts/validate.sh` | `scripts/validate.py` | CI validation |
| `tests/**/*.bats` | `tests/**/test_*.py` | pytest, same coverage |
| `tests/helpers/setup.bash` | `tests/conftest.py` | Shared fixtures |

Old bash files are deleted after Python equivalents are in place.

---

## Entry Points

### Unix (`bin/loppy`)
```bash
#!/usr/bin/env -S uv run python3
# ... Python source follows
```
`bin/loppy` IS the Python file — no `.py` extension, same filename as before. The shebang makes it directly executable on Unix.

### Windows (`bin/loppy.cmd`)
```bat
@echo off
uv run "%~dp0loppy" %*
```

### Hook (`hooks/hooks.json`)
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

---

## Core CLI (`bin/loppy.py`)

### Stdlib imports
`pathlib`, `json`, `re`, `shutil`, `tempfile`, `subprocess`, `datetime`, `sys`, `os`

### Config path
```python
def config_path() -> Path:
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    return base / 'loppy' / 'config.json'
```

### Bash → Python translation

| Bash | Python |
|------|--------|
| `jq` | `json` module |
| `find -maxdepth 1 *.md` | `Path(d).glob('*.md')` |
| `find -type f -name '*.md'` | `Path(d).rglob('*.md')` |
| `mktemp -d` | `tempfile.mkdtemp()` |
| `awk` (index/log parsing) | `re` + string slicing |
| `date +%Y-%m-%d` | `date.today().isoformat()` |
| `date -d` (GNU-only) | `date.fromisoformat()` + `timedelta` |
| `mv` | `Path.replace()` or `shutil.move()` |
| `head -n N` / `tail -n +N` | list slicing |
| atomic write (`mv tmp real`) | `Path.replace()` |
| `bash =~` regex | `re.search()` |
| `grep -Fxq` | `str in set` or `line in lines` |

### Invocation in tests
Tests call `uv run bin/loppy` (not `bin/loppy.py`) to match the installed binary name.

### Subcommands
All six subcommands preserved with identical CLI interface:

- `config [key]` — read JSON or single value
- `next [N]` — glob sources, sort, head N
- `move <file>` — git ls-files check, git mv or shutil.move
- `index-merge` — stdin JSON, parse index, upsert, orphan detect, atomic write
- `log <op> <title>` — prepend entry, atomic write
- `lint-frontmatter` — rglob wiki pages, parse frontmatter, emit JSON findings

`LOPPY_TODAY` env var respected throughout (required for deterministic tests).

---

## Setup (`setup.py`)

- `input()` replaces `read -p`
- ANSI colors: emitted only when `sys.stdout.isatty()` — works on modern Windows Terminal, stripped otherwise
- Paths: `Path.resolve()`, `Path.mkdir(parents=True, exist_ok=True)`
- Template copy: `shutil.copy()`
- Binary install:
  - Unix: copies `loppy.py` to `~/.local/bin/loppy`, sets executable bit via `os.chmod()`
  - Windows: copies `loppy.cmd` to `%USERPROFILE%\.local\bin\loppy.cmd`, prints PATH hint
- Git init: `subprocess.run(['git', 'init', str(vault_dir)])`

---

## Guard Hook (`hooks/guard_vault.py`)

Direct translation of `guard-vault.sh`. Same logic, same exit codes.

- `json.load(sys.stdin)` reads hook payload
- `re.search()` replaces bash `=~` pattern matching
- Exit `0` → PASS, exit `2` → BLOCK
- Prints `"PASS"` or `"BLOCK: <reason>"` to stdout
- Fail-open on missing config (same as bash version)

---

## Validate (`scripts/validate.py`)

- File existence: `Path.exists()`
- JSON validation: `json.load()` — no `jq`
- Python syntax check: `py_compile.compile()` replaces `bash -n`
- Doc section checks: `re.search()` replaces `grep -q`
- Test coverage: `subprocess.run(['pytest', '--collect-only', '-q'])` replaces line-count heuristic

---

## Tests (`pytest`)

### Two-layer strategy
- **Unit**: import functions directly from `loppy.py` — fast, no subprocess overhead
- **Integration**: `subprocess.run(['uv', 'run', 'bin/loppy.py', ...])` — full invocation path

### File mapping (1:1 coverage)
| Old `.bats` | New `test_*.py` |
|-------------|-----------------|
| `tests/loppy/config.bats` | `tests/loppy/test_config.py` |
| `tests/loppy/next.bats` | `tests/loppy/test_next.py` |
| `tests/loppy/move.bats` | `tests/loppy/test_move.py` |
| `tests/loppy/index-merge.bats` | `tests/loppy/test_index_merge.py` |
| `tests/loppy/log.bats` | `tests/loppy/test_log.py` |
| `tests/loppy/lint-frontmatter.bats` | `tests/loppy/test_lint_frontmatter.py` |
| `tests/guard/guard-vault.bats` | `tests/guard/test_guard_vault.py` |
| `tests/setup/setup.bats` | `tests/setup/test_setup.py` |
| `tests/manifest/manifest.bats` | `tests/manifest/test_manifest.py` |
| `tests/commands/wiki.bats` | `tests/commands/test_wiki.py` |
| `tests/docs/docs.bats` | `tests/docs/test_docs.py` |
| `tests/templates/templates.bats` | `tests/templates/test_templates.py` |
| `tests/ci/ci.bats` | `tests/ci/test_ci.py` |
| `tests/e2e/e2e.bats` | `tests/e2e/test_e2e.py` |

### Shared fixtures (`tests/conftest.py`)
- `tmp_vault` — creates temp vault dir with sources/, wiki/, index.md, log.md, wiki-schema.yaml
- `config_file` — writes config.json pointing at tmp_vault
- `loppy_env` — env dict with `LOPPY_TODAY` set and config path overridden

---

## CI (`ci.yml`)

Remove `bats` install step. Add:
```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v4

- name: Run tests
  run: uv run pytest tests/
```

Add matrix for cross-platform validation:
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
```

---

## What Does NOT Change

- Vault directory structure (`sources/`, `wiki/`, `index.md`, `log.md`)
- Config JSON schema
- Wiki frontmatter schema
- Index TSV format
- Log markdown format
- `loppy` CLI interface (subcommands, args, stdout format)
- Plugin manifest (`plugin.json`)
- Skill files (`skills/*/SKILL.md`)
- Template files (`templates/`)

---

## Out of Scope

- Adding new features
- Changing the vault data model
- Packaging as a pip/uv installable package
