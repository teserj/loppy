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
