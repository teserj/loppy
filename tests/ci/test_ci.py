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
