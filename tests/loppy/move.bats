#!/usr/bin/env bats

load '../helpers/setup.bash'

setup() { isolate_env; }
teardown() { cleanup_env; }

@test "loppy move relocates file to processed/ in non-git vault" {
  echo "hello" > "$SOURCES_DIR/note.md"
  run "$LOPPY_BIN" move "$SOURCES_DIR/note.md"
  [ "$status" -eq 0 ]
  [ ! -f "$SOURCES_DIR/note.md" ]
  [ -f "$SOURCES_DIR/processed/note.md" ]
  [ "$(cat "$SOURCES_DIR/processed/note.md")" = "hello" ]
}

@test "loppy move uses git mv in git vault" {
  git -C "$VAULT_DIR" init -q
  git -C "$VAULT_DIR" config user.email "test@test.com"
  git -C "$VAULT_DIR" config user.name "Test"
  echo "content" > "$SOURCES_DIR/tracked.md"
  git -C "$VAULT_DIR" add "$SOURCES_DIR/tracked.md"
  git -C "$VAULT_DIR" commit -q -m "add tracked"
  run "$LOPPY_BIN" move "$SOURCES_DIR/tracked.md"
  [ "$status" -eq 0 ]
  [ ! -f "$SOURCES_DIR/tracked.md" ]
  [ -f "$SOURCES_DIR/processed/tracked.md" ]
  # git status should show a rename
  git_status="$(git -C "$VAULT_DIR" status --short)"
  [[ "$git_status" =~ "R" ]]
}

@test "loppy move refuses if destination already exists" {
  echo "original" > "$SOURCES_DIR/note.md"
  echo "existing" > "$SOURCES_DIR/processed/note.md"
  run "$LOPPY_BIN" move "$SOURCES_DIR/note.md"
  [ "$status" -ne 0 ]
  [[ "$output" =~ "destination exists" ]]
  [ -f "$SOURCES_DIR/note.md" ]
}

@test "loppy move creates processed/ directory if missing" {
  rm -rf "$SOURCES_DIR/processed"
  echo "data" > "$SOURCES_DIR/new.md"
  run "$LOPPY_BIN" move "$SOURCES_DIR/new.md"
  [ "$status" -eq 0 ]
  [ -d "$SOURCES_DIR/processed" ]
  [ -f "$SOURCES_DIR/processed/new.md" ]
}

@test "loppy move fails if source does not exist" {
  run "$LOPPY_BIN" move "$SOURCES_DIR/nonexistent.md"
  [ "$status" -ne 0 ]
  [[ "$output" =~ "source not found" ]]
}

@test "loppy move requires a file argument" {
  run "$LOPPY_BIN" move
  [ "$status" -ne 0 ]
  [[ "$output" =~ "source path required" ]]
}
