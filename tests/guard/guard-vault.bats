#!/usr/bin/env bats

load '../helpers/setup.bash'

setup() {
  isolate_env
  mkdir -p "$WIKI_DIR" "$SOURCES_DIR"
}

teardown() {
  cleanup_env
}

@test "guard: allow config command (not destructive)" {
  input='{"tool": "bash", "command": "loppy config"}'
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: block rm targeting vault" {
  input="{\"tool\": \"bash\", \"command\": \"rm -rf $VAULT_DIR/file.md\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCK"* ]]
  [[ "$output" == *"Destructive"* ]]
}

@test "guard: block mv within vault" {
  input="{\"tool\": \"bash\", \"command\": \"mv $VAULT_DIR/a.md $VAULT_DIR/b.md\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCK"* ]]
}

@test "guard: block shred in wiki" {
  input="{\"tool\": \"bash\", \"command\": \"shred -vfz $WIKI_DIR/page.md\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCK"* ]]
}

@test "guard: allow safe find command" {
  input="{\"tool\": \"bash\", \"command\": \"find $SOURCES_DIR -name \\\"*.md\\\"\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: allow git mv (controlled by loppy move)" {
  input="{\"tool\": \"bash\", \"command\": \"git mv $SOURCES_DIR/a.md $SOURCES_DIR/b.md\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: allow git rm (controlled by git history)" {
  input="{\"tool\": \"bash\", \"command\": \"git rm $WIKI_DIR/page.md\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: block rmdir in vault" {
  input="{\"tool\": \"bash\", \"command\": \"rmdir $WIKI_DIR/subdir\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCK"* ]]
}

@test "guard: block rm of .git directory (prevent losing history)" {
  input="{\"tool\": \"bash\", \"command\": \"rm -rf $VAULT_DIR/.git\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCK"* ]]
}

@test "guard: block unlink in vault" {
  input="{\"tool\": \"bash\", \"command\": \"unlink $VAULT_DIR/file.md\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCK"* ]]
}

@test "guard: block dd in vault" {
  input="{\"tool\": \"bash\", \"command\": \"dd if=/dev/zero of=$VAULT_DIR/file.txt\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCK"* ]]
}

@test "guard: allow loppy commands (allowlisted)" {
  input="{\"tool\": \"bash\", \"command\": \"loppy move $VAULT_DIR/file.md\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: allow loppy subcommands (allowlisted)" {
  input="{\"tool\": \"bash\", \"command\": \"loppy index-merge < input.json\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: non-bash tools pass through" {
  input='{"tool": "read", "file_path": "/some/file.txt"}'
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: write tool passes through" {
  input='{"tool": "write", "file_path": "/some/file.txt", "content": "test"}'
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: config missing fails open with warning" {
  rm "$CONFIG_FILE"
  input="{\"tool\": \"bash\", \"command\": \"rm -rf /tmp/unrelated\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT' 2>&1"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: rm outside vault is allowed" {
  input='{"tool": "bash", "command": "rm -rf /tmp/unrelated/file.txt"}'
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: empty command passes through" {
  input='{"tool": "bash", "command": ""}'
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: malformed JSON passes through safely" {
  input='not valid json'
  run bash -c "echo '$input' | '$GUARD_SCRIPT' 2>&1"
  [ "$status" -eq 0 ]
  [ "$output" = "PASS" ]
}

@test "guard: detects vault path with variable expansion" {
  input='{"tool": "bash", "command": "rm -rf $VAULT_DIR/sensitive.md"}'
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCK"* ]]
}

@test "guard: block rm with sources_dir path" {
  input="{\"tool\": \"bash\", \"command\": \"rm $SOURCES_DIR/file.md\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCK"* ]]
}

@test "guard: block shred with wiki_dir path" {
  input="{\"tool\": \"bash\", \"command\": \"shred $WIKI_DIR/page.md\"}"
  run bash -c "echo '$input' | '$GUARD_SCRIPT'"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCK"* ]]
}
