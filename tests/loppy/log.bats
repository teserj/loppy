#!/usr/bin/env bats

load '../helpers/setup.bash'

setup() {
  isolate_env
  export LOPPY_TODAY="2026-04-17"
  # Seed a starter log file.
  cat > "$WIKI_DIR/log.md" <<'EOF'
---
type: log
title: Wiki Activity Log
---

# Wiki Log

Append-only. New entries at top.

---

EOF
}
teardown() { cleanup_env; }

@test "log prepends a new entry under the header" {
  run bash -c "echo 'body line one' | '$LOPPY_BIN' log ingest 'first batch'"
  [ "$status" -eq 0 ]
  grep -q "^## \[2026-04-17\] ingest | first batch" "$WIKI_DIR/log.md"
  grep -q "body line one" "$WIKI_DIR/log.md"
}

@test "log preserves the file header (frontmatter + title)" {
  run bash -c "echo x | '$LOPPY_BIN' log lint 'nothing found'"
  [ "$status" -eq 0 ]
  head -5 "$WIKI_DIR/log.md" | grep -q "type: log"
  head -8 "$WIKI_DIR/log.md" | grep -q "# Wiki Log"
}

@test "log places newest entry above any prior entries" {
  run bash -c "echo 'first' | '$LOPPY_BIN' log ingest 'entry-one'"
  run bash -c "echo 'second' | '$LOPPY_BIN' log ingest 'entry-two'"
  # find the line numbers of each header; entry-two must come first (smaller line number)
  local_one=$(grep -n "entry-one" "$WIKI_DIR/log.md" | head -1 | cut -d: -f1)
  local_two=$(grep -n "entry-two" "$WIKI_DIR/log.md" | head -1 | cut -d: -f1)
  [ "$local_two" -lt "$local_one" ]
}

@test "log requires op and title args" {
  run bash -c "echo x | '$LOPPY_BIN' log"
  [ "$status" -ne 0 ]
  run bash -c "echo x | '$LOPPY_BIN' log ingest"
  [ "$status" -ne 0 ]
}

@test "log supports multi-line body from stdin" {
  run bash -c "printf 'line 1\nline 2\nline 3\n' | '$LOPPY_BIN' log ingest 'multi'"
  [ "$status" -eq 0 ]
  grep -q "line 1" "$WIKI_DIR/log.md"
  grep -q "line 2" "$WIKI_DIR/log.md"
  grep -q "line 3" "$WIKI_DIR/log.md"
}

@test "log appends entry and creates separator when log.md has no trailing separator" {
  # Write a log file that has the H1 but no trailing --- separator
  cat > "$WIKI_DIR/log.md" <<'EOF'
---
type: log
title: Wiki Activity Log
---

# Wiki Log

Append-only. New entries at top.
EOF
  run bash -c "echo 'no-sep body' | '$LOPPY_BIN' log ingest 'no-sep-title'"
  [ "$status" -eq 0 ]
  grep -q "^## \[2026-04-17\] ingest | no-sep-title" "$WIKI_DIR/log.md"
  grep -q "no-sep body" "$WIKI_DIR/log.md"
  grep -q "^---" "$WIKI_DIR/log.md"
}

@test "log fails with error when log.md is missing" {
  rm -f "$WIKI_DIR/log.md"
  run bash -c "echo x | '$LOPPY_BIN' log ingest 'missing'"
  [ "$status" -ne 0 ]
  echo "$output" | grep -q "not found"
}
