#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path

SHELL_TOOLS = {"bash", "powershell", "cmd"}


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

    if data.get("tool") not in SHELL_TOOLS:
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

    if re.match(r"^loppy", command) or re.search(r"git\s+(mv|rm)", command):
        print("PASS")
        sys.exit(0)

    def vault_referenced(cmd: str) -> bool:
        for path in [vault_dir, sources_dir, wiki_dir]:
            if path and path in cmd:
                return True
        return any(v in cmd for v in [
            "$VAULT_DIR", "$SOURCES_DIR", "$WIKI_DIR",
            "%VAULT_DIR%", "%SOURCES_DIR%", "%WIKI_DIR%",
            "$env:VAULT_DIR", "$env:SOURCES_DIR", "$env:WIKI_DIR",
        ])

    block_msg = "BLOCK: Destructive operation on vault detected. Use 'loppy move' for file operations."

    def block_if_vault(cmd: str) -> None:
        if vault_referenced(cmd):
            print(block_msg)
            sys.exit(2)

    # Unix
    if re.search(r"(^|\s)(rm|rmdir|shred|unlink)(\s|-)", command):
        block_if_vault(command)

    if re.search(r"(^|\s)mv(\s|-)", command):
        block_if_vault(command)

    if re.search(r"(^|\s)dd(\s|-)", command):
        block_if_vault(command)

    # Windows CMD
    if re.search(r"(^|\s)(del|erase)(\s|/)", command, re.IGNORECASE):
        block_if_vault(command)

    if re.search(r"(^|\s)(rd|rmdir)(\s|/)", command, re.IGNORECASE):
        block_if_vault(command)

    if re.search(r"(^|\s)move(\s|/)", command, re.IGNORECASE):
        block_if_vault(command)

    # PowerShell cmdlets and aliases
    if re.search(r"(^|\s|;|\|)Remove-Item(\s|-)", command, re.IGNORECASE):
        block_if_vault(command)

    if re.search(r"(^|\s|;|\|)Move-Item(\s|-)", command, re.IGNORECASE):
        block_if_vault(command)

    if re.search(r"(^|\s|;|\|)ri(\s|-)", command):
        block_if_vault(command)

    if re.search(r"(^|\s|;|\|)mi(\s|-)", command):
        block_if_vault(command)

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
