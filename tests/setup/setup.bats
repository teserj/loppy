#!/usr/bin/env bats

load ../helpers/setup

setup() {
  isolate_env
}

teardown() {
  cleanup_env
}

@test "setup: script exists and is executable" {
  [[ -x "$PLUGIN_ROOT/setup.sh" ]]
}

@test "setup: creates config directory" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"

  # Run setup non-interactively
  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault
source
wiki
n
EOF

  # Check config was created
  [[ -f "$XDG_CONFIG_HOME/loppy/config.json" ]]
}

@test "setup: config has correct keys" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"

  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault
source
wiki
n
EOF

  config="$XDG_CONFIG_HOME/loppy/config.json"
  [[ -f "$config" ]]
  jq -e '.vault_dir' "$config" > /dev/null
  jq -e '.sources_dir' "$config" > /dev/null
  jq -e '.wiki_dir' "$config" > /dev/null
  jq -e '.batch_size' "$config" > /dev/null
}

@test "setup: sources_dir defaults to source" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"

  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault

wiki
n
EOF

  config="$XDG_CONFIG_HOME/loppy/config.json"
  sources=$(jq -r '.sources_dir' "$config")
  [[ "$sources" == "$vault/source" ]]
}

@test "setup: wiki_dir defaults to wiki" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"

  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault
source

n
EOF

  config="$XDG_CONFIG_HOME/loppy/config.json"
  wiki=$(jq -r '.wiki_dir' "$config")
  [[ "$wiki" == "$vault/wiki" ]]
}

@test "setup: batch_size defaults to 5" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"

  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault
source
wiki
n
EOF

  config="$XDG_CONFIG_HOME/loppy/config.json"
  batch=$(jq -r '.batch_size' "$config")
  [[ "$batch" == 5 ]]
}

@test "setup: copies templates to vault" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"

  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault
source
wiki
n
EOF

  [[ -f "$vault/wiki-schema.yaml" ]]
  [[ -f "$vault/index.md" ]]
  [[ -f "$vault/log.md" ]]
}

@test "setup: creates subdirectories" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"

  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault
sources
wiki
n
EOF

  [[ -d "$vault/sources" ]]
  [[ -d "$vault/wiki" ]]
}

@test "setup: initializes git repo if needed" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"

  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault
source
wiki
y
EOF

  [[ -d "$vault/.git" ]]
}

@test "setup: skips git init if repo exists" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"
  cd "$vault"
  git init -q

  # Re-run setup
  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault
source
wiki
y
EOF

  # Should not error
  [[ -d "$vault/.git" ]]
}

@test "setup: produces valid JSON config" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"

  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault
source
wiki
n
EOF

  config="$XDG_CONFIG_HOME/loppy/config.json"
  # jq will error if JSON is invalid
  jq . "$config" > /dev/null
}

@test "setup: installs binary to ~/.local/bin" {
  vault="$TEST_TMP/vault"
  mkdir -p "$vault"
  bin_dir="$TEST_TMP/.local/bin"
  mkdir -p "$bin_dir"

  # Override HOME to use test bin directory
  export HOME="$TEST_TMP"

  bash "$PLUGIN_ROOT/setup.sh" <<EOF
$vault
source
wiki
n
EOF

  # Check binary installed
  [[ -f "$bin_dir/loppy" ]]
  [[ -x "$bin_dir/loppy" ]]
}
