#!/bin/bash

# PreToolUse hook: block destructive vault operations
# Reads JSON from stdin: {"tool": "...", "command": "...", ...}
# Outputs: PASS (allow) or BLOCK: <reason> (deny)
# Exit codes: 0 = PASS, 2 = BLOCK

set -o pipefail

# Read stdin (handle empty/malformed gracefully)
input=$(cat 2>/dev/null) || {
  echo "PASS"
  exit 0
}

# Only guard bash tool; others pass through
tool=$(echo "$input" | jq -r '.tool // empty' 2>/dev/null) || {
  echo "PASS"
  exit 0
}

[[ "$tool" != "bash" ]] && echo "PASS" && exit 0

# Extract command
command=$(echo "$input" | jq -r '.command // empty' 2>/dev/null) || {
  echo "PASS"
  exit 0
}

[[ -z "$command" ]] && echo "PASS" && exit 0

# Load config to get vault paths
config_file="${XDG_CONFIG_HOME:-$HOME/.config}/loppy/config.json"
if [[ ! -f "$config_file" ]]; then
  # Config missing: fail-open with warning (can't protect what we don't know)
  echo "PASS"
  exit 0
fi

# Extract vault paths from config (handle missing gracefully)
vault_dir=$(jq -r '.vault_dir // empty' "$config_file" 2>/dev/null) || vault_dir=""
sources_dir=$(jq -r '.sources_dir // empty' "$config_file" 2>/dev/null) || sources_dir=""
wiki_dir=$(jq -r '.wiki_dir // empty' "$config_file" 2>/dev/null) || wiki_dir=""

# Empty config is treated as pass-through (can't guard without valid paths)
[[ -z "$vault_dir" && -z "$sources_dir" && -z "$wiki_dir" ]] && {
  echo "PASS"
  exit 0
}

# Allowlist: any command starting with 'loppy' or containing 'git mv' or 'git rm' is permitted
# These are controlled by the Loppy helpers or git's history preservation
if [[ "$command" =~ ^loppy ]] || [[ "$command" =~ git\ (mv|rm) ]]; then
  echo "PASS"
  exit 0
fi

# Check for destructive patterns: rm, rmdir, shred, unlink, dd (not prefixed with git)
# Must also reference a vault path variable or actual path
destructive_pattern=0

# Helper function to check if command references vault
vault_referenced() {
  local cmd="$1"
  # Check for explicit vault paths or variable references
  [[ "$cmd" =~ $vault_dir ]] && return 0
  [[ "$cmd" =~ \$VAULT_DIR ]] && return 0
  [[ "$cmd" =~ $sources_dir ]] && return 0
  [[ "$cmd" =~ \$SOURCES_DIR ]] && return 0
  [[ "$cmd" =~ $wiki_dir ]] && return 0
  [[ "$cmd" =~ \$WIKI_DIR ]] && return 0
  return 1
}

# Pattern 1: rm/rmdir/shred/unlink with vault paths
if [[ "$command" =~ (^|[[:space:]])(rm|rmdir|shred|unlink)([[:space:]]|-) ]]; then
  if vault_referenced "$command"; then
    destructive_pattern=1
  fi
fi

# Pattern 2: mv with vault paths (move operations within vault)
if [[ "$command" =~ (^|[[:space:]])mv([[:space:]]|-) ]]; then
  if vault_referenced "$command"; then
    destructive_pattern=1
  fi
fi

# Pattern 3: dd with vault paths (disk overwrite)
if [[ "$command" =~ (^|[[:space:]])dd([[:space:]]|-) ]]; then
  if vault_referenced "$command"; then
    destructive_pattern=1
  fi
fi

if [[ $destructive_pattern -eq 1 ]]; then
  echo "BLOCK: Destructive operation on vault detected. Use 'loppy move' for file operations."
  exit 2
fi

echo "PASS"
exit 0
