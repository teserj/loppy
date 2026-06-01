#!/usr/bin/env python3
"""Loppy vault setup — interactive installer."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


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

    while True:
        vault_str = input("Enter path to vault directory (required): ").strip()
        if not vault_str:
            print(RED("Error: vault directory is required"))
            continue
        vault_dir = Path(vault_str).resolve()
        vault_dir.mkdir(parents=True, exist_ok=True)
        break

    sources_rel = input("Relative path to raw sources (default: source): ").strip() or "source"
    wiki_rel    = input("Relative path to compiled wiki (default: wiki): ").strip() or "wiki"

    sources_abs = vault_dir / sources_rel
    wiki_abs    = vault_dir / wiki_rel
    sources_abs.mkdir(parents=True, exist_ok=True)
    wiki_abs.mkdir(parents=True, exist_ok=True)
    print(f"Created subdirectories: {sources_rel}/, {wiki_rel}/")
    print()

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

    tmpl_dir = SCRIPT_DIR / "templates"
    if tmpl_dir.is_dir():
        schema_dst = vault_dir / "wiki-schema.yaml"
        if schema_dst.exists():
            answer = input("wiki-schema.yaml already exists in vault. Overwrite? (y/n): ").strip().lower()
            if answer.startswith("y"):
                shutil.copy(tmpl_dir / "wiki-schema.yaml", schema_dst)
                print("wiki-schema.yaml overwritten")
            else:
                print("wiki-schema.yaml kept unchanged")
        else:
            shutil.copy(tmpl_dir / "wiki-schema.yaml", schema_dst)
            print("wiki-schema.yaml copied to vault")
        for fname in ("index.md", "log.md"):
            dst = wiki_abs / fname
            if not dst.exists():
                shutil.copy(tmpl_dir / fname, dst)
                print(f"{fname} created in wiki")
            else:
                print(f"{fname} already exists, skipping")
        print("Templates applied")
    else:
        print(RED("Warning: templates directory not found"))
    print()

    print("Installing loppy binary...")
    uv_path = shutil.which("uv") or "uv"
    if os.name == "nt":
        local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        bin_dir = local_app_data / "Programs" / "loppy"
    else:
        bin_dir = Path(os.environ.get("HOME", str(Path.home()))) / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    src_bin = SCRIPT_DIR / "bin" / "loppy"
    if src_bin.exists():
        if os.name == "nt":
            dest = bin_dir / "loppy.cmd"
            loppy_script = bin_dir / "loppy"
            shutil.copy(src_bin, loppy_script)
            dest.write_text(
                f'@echo off\n"{uv_path}" run python "%~dp0loppy" %*\n',
                encoding="utf-8",
            )
        else:
            dest = bin_dir / "loppy"
            shutil.copy(src_bin, dest)
            dest.chmod(dest.stat().st_mode | 0o111)
        print(f"Binary installed: {dest}")
        if os.name == "nt":
            print(f"  Add to PATH: {bin_dir}")
    else:
        print(RED("Warning: bin/loppy not found"))
    print()

    if not (vault_dir / ".git").exists():
        answer = input("Initialize git repository in vault? (y/n): ").strip().lower()
        if answer.startswith("y"):
            subprocess.run(["git", "init", str(vault_dir)], check=False)
            print("Git repository initialized")
    else:
        print("Git repository already exists")

    guard_script = SCRIPT_DIR / "hooks" / "guard_vault.py"
    if guard_script.exists():
        codex_cfg_dir = Path.home() / ".codex"
        codex_cfg_dir.mkdir(exist_ok=True)
        codex_hooks = codex_cfg_dir / "hooks.json"
        codex_hooks.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PreToolUse": [
                            {
                                "matcher": "Bash",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": (
                                            f'python "{guard_script}"'
                                            if os.name == "nt"
                                            else f'"{uv_path}" run "{guard_script}"'
                                        ),
                                    }
                                ],
                            }
                        ]
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"Codex hooks installed: {codex_hooks}")
        shutil.copy(SCRIPT_DIR / "AGENTS.md", vault_dir / "AGENTS.md")
        print(f"AGENTS.md copied to vault: {vault_dir / 'AGENTS.md'}")
    else:
        print(RED("Warning: hooks/guard_vault.py not found, skipping Codex setup"))

    claude_md = SCRIPT_DIR / "CLAUDE.md"
    if claude_md.exists():
        shutil.copy(claude_md, vault_dir / "CLAUDE.md")
        print(f"CLAUDE.md copied to vault: {vault_dir / 'CLAUDE.md'}")
    else:
        print(RED("Warning: CLAUDE.md not found, skipping Claude Code setup"))

    print()

    print(GREEN("=== Setup Complete ==="))
    print(f"Vault:  {vault_dir}")
    print(f"Config: {cfg_file}")


if __name__ == "__main__":
    main()
