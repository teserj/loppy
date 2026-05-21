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
        shutil.copy(tmpl_dir / "wiki-schema.yaml", vault_dir / "wiki-schema.yaml")
        shutil.copy(tmpl_dir / "index.md",         wiki_abs / "index.md")
        shutil.copy(tmpl_dir / "log.md",           wiki_abs / "log.md")
        print("Templates copied to vault")
    else:
        print(RED("Warning: templates directory not found"))
    print()

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
