#!/usr/bin/env bats

load '../helpers/setup.bash'

setup() { isolate_env; }
teardown() { cleanup_env; }

@test "loppy config prints full JSON when no key given" {
  run "$LOPPY_BIN" config
  [ "$status" -eq 0 ]
  [[ "$output" == *"\"vault_dir\""* ]]
  [[ "$output" == *"\"batch_size\""* ]]
}

@test "loppy config with key prints scalar value" {
  run "$LOPPY_BIN" config batch_size
  [ "$status" -eq 0 ]
  [ "$output" = "5" ]
}

@test "loppy config with key prints string value without quotes" {
  run "$LOPPY_BIN" config vault_dir
  [ "$status" -eq 0 ]
  [ "$output" = "$VAULT_DIR" ]
}

@test "loppy config exits 1 when config missing" {
  rm "$CONFIG_FILE"
  run "$LOPPY_BIN" config
  [ "$status" -eq 1 ]
  [[ "$output" == *"config not found"* ]]
  [[ "$output" == *"setup.sh"* ]]
}

@test "loppy config exits 1 on malformed JSON" {
  echo "not json {{" > "$CONFIG_FILE"
  run "$LOPPY_BIN" config
  [ "$status" -eq 1 ]
}

@test "loppy config exits 1 on unknown key" {
  run "$LOPPY_BIN" config no_such_key
  [ "$status" -eq 1 ]
}
