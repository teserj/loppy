#!/usr/bin/env bats

load '../helpers/setup.bash'

setup() { isolate_env; }
teardown() { cleanup_env; }

@test "loppy next with empty sources dir returns empty output" {
  run "$LOPPY_BIN" next
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "loppy next uses batch_size from config when no N given" {
  # Create 7 files in sources_dir
  for i in {1..7}; do
    touch "$SOURCES_DIR/file${i}.md"
  done
  run "$LOPPY_BIN" next
  [ "$status" -eq 0 ]
  # batch_size is 5, so should return 5 lines
  [ "$(echo "$output" | wc -l)" -eq 5 ]
}

@test "loppy next limits to N files when given" {
  # Create 7 files in sources_dir
  for i in {1..7}; do
    touch "$SOURCES_DIR/file${i}.md"
  done
  run "$LOPPY_BIN" next 2
  [ "$status" -eq 0 ]
  [ "$(echo "$output" | wc -l)" -eq 2 ]
}

@test "loppy next excludes processed/ subdir" {
  touch "$SOURCES_DIR/keep.md"
  touch "$SOURCES_DIR/processed/already.md"
  run "$LOPPY_BIN" next
  [ "$status" -eq 0 ]
  [[ "$output" =~ keep.md ]]
  [[ "$output" != *"already.md" ]]
}

@test "loppy next includes .txt files" {
  touch "$SOURCES_DIR/file1.md"
  touch "$SOURCES_DIR/file2.txt"
  run "$LOPPY_BIN" next
  [ "$status" -eq 0 ]
  [[ "$output" =~ file1.md ]]
  [[ "$output" =~ file2.txt ]]
}

@test "loppy next returns absolute paths" {
  touch "$SOURCES_DIR/test.md"
  run "$LOPPY_BIN" next
  [ "$status" -eq 0 ]
  [[ "$output" == /* ]]
}

@test "loppy next produces sorted output" {
  touch "$SOURCES_DIR/zebra.md"
  touch "$SOURCES_DIR/apple.md"
  touch "$SOURCES_DIR/banana.md"
  run "$LOPPY_BIN" next
  [ "$status" -eq 0 ]
  # Check first line contains apple, last contains zebra
  [ "$(echo "$output" | head -1)" = "$SOURCES_DIR/apple.md" ]
  [ "$(echo "$output" | tail -1)" = "$SOURCES_DIR/zebra.md" ]
}
