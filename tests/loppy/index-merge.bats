#!/usr/bin/env bats

load '../helpers/setup.bash'

setup() {
  isolate_env
  # Fix today's date so the output is deterministic
  export LOPPY_TODAY="2026-04-17"
}
teardown() { cleanup_env; }

@test "index-merge inserts into empty index" {
  cp "$PLUGIN_ROOT/tests/fixtures/index-merge/empty-before.md" "$WIKI_DIR/index.md"
  mkdir -p "$WIKI_DIR/concepts" "$WIKI_DIR/sources"
  : > "$WIKI_DIR/concepts/foo.md"
  : > "$WIKI_DIR/sources/bar.md"
  run bash -c "echo '[
    {\"path\":\"wiki/concepts/foo.md\",\"summary\":\"Foo concept summary\"},
    {\"path\":\"wiki/sources/bar.md\",\"summary\":\"Bar source summary\"}
  ]' | '$LOPPY_BIN' index-merge"
  [ "$status" -eq 0 ]
  diff "$WIKI_DIR/index.md" "$PLUGIN_ROOT/tests/fixtures/index-merge/empty-after.md"
}

@test "index-merge updates an existing entry" {
  cp "$PLUGIN_ROOT/tests/fixtures/index-merge/one-entry-before.md" "$WIKI_DIR/index.md"
  mkdir -p "$WIKI_DIR/concepts"
  : > "$WIKI_DIR/concepts/foo.md"
  run bash -c "echo '[{\"path\":\"wiki/concepts/foo.md\",\"summary\":\"New summary\"}]' | '$LOPPY_BIN' index-merge"
  [ "$status" -eq 0 ]
  diff "$WIKI_DIR/index.md" "$PLUGIN_ROOT/tests/fixtures/index-merge/one-entry-after.md"
}

@test "index-merge warns on orphan (file on disk not in index)" {
  cp "$PLUGIN_ROOT/tests/fixtures/index-merge/empty-before.md" "$WIKI_DIR/index.md"
  mkdir -p "$WIKI_DIR/concepts"
  : > "$WIKI_DIR/concepts/foo.md"
  : > "$WIKI_DIR/concepts/orphan.md"
  run bash -c "echo '[{\"path\":\"wiki/concepts/foo.md\",\"summary\":\"x\"}]' | '$LOPPY_BIN' index-merge"
  [ "$status" -eq 0 ]
  [[ "$output" == *"orphan"* ]]
  [[ "$output" == *"wiki/concepts/orphan.md"* ]]
}

@test "index-merge ignores index.md and log.md themselves" {
  cp "$PLUGIN_ROOT/tests/fixtures/index-merge/empty-before.md" "$WIKI_DIR/index.md"
  : > "$WIKI_DIR/log.md"
  : > "$WIKI_DIR/wiki-schema.yaml"
  run bash -c "echo '[]' | '$LOPPY_BIN' index-merge"
  [ "$status" -eq 0 ]
  [[ "$output" != *"orphan: wiki/index.md"* ]]
  [[ "$output" != *"orphan: wiki/log.md"* ]]
}

@test "index-merge writes atomically (tmp file not left behind)" {
  cp "$PLUGIN_ROOT/tests/fixtures/index-merge/empty-before.md" "$WIKI_DIR/index.md"
  run bash -c "echo '[]' | '$LOPPY_BIN' index-merge"
  [ "$status" -eq 0 ]
  # No leftover .tmp files
  run find "$WIKI_DIR" -name "index.md.*"
  [ -z "$output" ]
}
