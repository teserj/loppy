#!/usr/bin/env bash
# Shared bats helpers. Sourced by every .bats file via `load '../helpers/setup.bash'`.

# Absolute path to the plugin repo root (two levels up from tests/helpers/).
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOPPY_BIN="$PLUGIN_ROOT/bin/loppy"
GUARD_SCRIPT="$PLUGIN_ROOT/hooks/guard-vault.sh"

# Create an isolated vault + config for one test. Call in `setup()`.
# Sets: VAULT_DIR, SOURCES_DIR, WIKI_DIR, CONFIG_DIR, CONFIG_FILE, XDG_CONFIG_HOME
isolate_env() {
  export TEST_TMP="$(mktemp -d)"
  export VAULT_DIR="$TEST_TMP/vault"
  export SOURCES_DIR="$VAULT_DIR/sources"
  export WIKI_DIR="$VAULT_DIR/wiki"
  mkdir -p "$SOURCES_DIR/processed" "$WIKI_DIR"

  export XDG_CONFIG_HOME="$TEST_TMP/config"
  export CONFIG_DIR="$XDG_CONFIG_HOME/loppy"
  export CONFIG_FILE="$CONFIG_DIR/config.json"
  mkdir -p "$CONFIG_DIR"
  cat >"$CONFIG_FILE" <<EOF
{
  "vault_dir": "$VAULT_DIR",
  "sources_dir": "$SOURCES_DIR",
  "wiki_dir": "$WIKI_DIR",
  "batch_size": 5
}
EOF
}

cleanup_env() {
  [[ -n "${TEST_TMP:-}" && -d "$TEST_TMP" ]] && rm -rf "$TEST_TMP"
}
