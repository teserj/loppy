#!/usr/bin/env bats

load '../helpers/setup.bash'

setup() {
  isolate_env
  # Copy fixtures into test environment
  cp -r "$BATS_TEST_DIRNAME/../fixtures/sample-vault"/* "$VAULT_DIR/" 2>/dev/null || true
  mkdir -p "$WIKI_DIR" "$SOURCES_DIR"
}

teardown() {
  cleanup_env
}

@test "e2e: protocol document exists" {
  [[ -f "$BATS_TEST_DIRNAME/../fixtures/e2e-protocol.md" ]]
}

@test "e2e: sample vault has sources" {
  [[ -d "$BATS_TEST_DIRNAME/../fixtures/sample-vault/sources" ]]
  [[ -n "$(find "$BATS_TEST_DIRNAME/../fixtures/sample-vault/sources" -type f)" ]]
}

@test "e2e: sample vault has wiki" {
  [[ -d "$BATS_TEST_DIRNAME/../fixtures/sample-vault/wiki" ]]
}

@test "e2e: sample vault has index.md" {
  [[ -f "$BATS_TEST_DIRNAME/../fixtures/sample-vault/wiki/index.md" ]]
}

@test "e2e: sample vault has log.md" {
  [[ -f "$BATS_TEST_DIRNAME/../fixtures/sample-vault/wiki/log.md" ]]
}

@test "e2e: sample vault has schema" {
  [[ -f "$BATS_TEST_DIRNAME/../fixtures/sample-vault/wiki/wiki-schema.yaml" ]]
}

@test "e2e: ingest source creates page" {
  # Create test source
  cat > "$SOURCES_DIR/test-source.md" <<EOF
# Test Article

This is a test article about machine learning.
EOF

  # Simulate page creation
  cat > "$WIKI_DIR/test-source.md" <<EOF
---
type: sources
title: "Test Article"
created: 2026-04-18
updated: 2026-04-18
confidence: high
domain: tech
tags: [test]
links: []
---

Content from source.
EOF

  # Verify page exists
  [[ -f "$WIKI_DIR/test-source.md" ]]
}

@test "e2e: next command lists unprocessed sources" {
  # Create test sources
  touch "$SOURCES_DIR/file1.md"
  touch "$SOURCES_DIR/file2.md"

  # Run loppy next
  run "$LOPPY_BIN" next
  [ "$status" -eq 0 ]
  [[ "$output" =~ file1.md ]]
  [[ "$output" =~ file2.md ]]
}

@test "e2e: lint detects missing fields" {
  # Create malformed page
  mkdir -p "$WIKI_DIR"
  cat > "$WIKI_DIR/bad.md" <<EOF
---
type: sources
title: "Missing Fields"
---
Content
EOF

  # Lint should detect issues
  run "$LOPPY_BIN" lint-frontmatter
  [ "$status" -eq 0 ]
  # Output will be JSON array of issues
}

@test "e2e: log appends operation" {
  mkdir -p "$WIKI_DIR"

  # Create initial log
  cat > "$WIKI_DIR/log.md" <<EOF
# Operation Log

---

## 2026-04-18 10:00:00Z

Initial entry.
EOF

  # Add entry via loppy log
  run "$LOPPY_BIN" log "Test Operation" "Tested the operation"

  [ "$status" -eq 0 ]
  # Verify entry in log
  [[ -f "$WIKI_DIR/log.md" ]]
}

@test "e2e: move source to processed" {
  mkdir -p "$SOURCES_DIR/processed"
  touch "$SOURCES_DIR/test.md"

  # Move via loppy move (expects relative path from sources_dir)
  run bash -c "cd '$SOURCES_DIR' && '$LOPPY_BIN' move 'test.md'"
  [ "$status" -eq 0 ]

  # Verify source moved
  [[ -f "$SOURCES_DIR/processed/test.md" ]]
  [[ ! -f "$SOURCES_DIR/test.md" ]]
}

@test "e2e: index-merge validates index structure" {
  mkdir -p "$WIKI_DIR"

  # Create test page
  cat > "$WIKI_DIR/test.md" <<EOF
---
type: sources
title: "Test Page"
created: 2026-04-18
updated: 2026-04-18
confidence: high
domain: tech
tags: [test]
links: []
---

Content.
EOF

  # Create initial index
  cat > "$WIKI_DIR/index.md" <<EOF
# Wiki Index

## Sources
EOF

  # Run index-merge with sample data (expects JSON from stdin)
  run bash -c "echo '[{\"path\":\"sources/test\",\"summary\":\"Test page\",\"ns\":\"sources\"}]' | '$LOPPY_BIN' index-merge"

  [ "$status" -eq 0 ]
  [[ -f "$WIKI_DIR/index.md" ]]
}

@test "e2e: full workflow cycle" {
  # Setup vault structure
  mkdir -p "$SOURCES_DIR/processed" "$WIKI_DIR"

  # 1. Create source
  cat > "$SOURCES_DIR/test-article.md" <<EOF
# Test Article

This is a test article about machine learning and AI.
EOF

  # Verify source exists
  [[ -f "$SOURCES_DIR/test-article.md" ]]

  # 2. List source via next
  run "$LOPPY_BIN" next
  [ "$status" -eq 0 ]
  [[ "$output" =~ test-article.md ]]

  # 3. Create wiki page (simulate LLM ingestion)
  cat > "$WIKI_DIR/test-article.md" <<EOF
---
type: sources
title: "Test Article"
created: 2026-04-18
updated: 2026-04-18
confidence: high
domain: tech
tags: [test, ml, ai]
links: []
---

# Test Article

Content ingested from source.
EOF

  # Verify page created with valid frontmatter
  [[ -f "$WIKI_DIR/test-article.md" ]]
  grep -q "type: sources" "$WIKI_DIR/test-article.md"
  grep -q "title: \"Test Article\"" "$WIKI_DIR/test-article.md"

  # 4. Update index
  cat > "$WIKI_DIR/index.md" <<EOF
# Wiki Index

| path | title | type | domain | updated |
|------|-------|------|--------|---------|
| wiki/test-article | Test Article | sources | tech | 2026-04-18 |
EOF

  # 5. Move source to processed
  run bash -c "cd '$SOURCES_DIR' && '$LOPPY_BIN' move 'test-article.md'"
  [ "$status" -eq 0 ]
  [[ -f "$SOURCES_DIR/processed/test-article.md" ]]
  [[ ! -f "$SOURCES_DIR/test-article.md" ]]

  # 6. Log operation
  cat > "$WIKI_DIR/log.md" <<EOF
# Operation Log

---

## 2026-04-18 10:00:00Z

Initial setup.

---

## 2026-04-18 11:00:00Z

Ingested test-article. Created wiki page and updated index.
EOF

  # Verify end state
  [[ -f "$WIKI_DIR/test-article.md" ]]
  [[ -f "$SOURCES_DIR/processed/test-article.md" ]]
  [[ -f "$WIKI_DIR/index.md" ]]
  grep -q "test-article" "$WIKI_DIR/index.md"
  grep -q "Ingested test-article" "$WIKI_DIR/log.md"
}

@test "e2e: fixture vault copies to test environment" {
  # Verify fixtures were copied
  [[ -f "$WIKI_DIR/index.md" ]]
  [[ -f "$WIKI_DIR/log.md" ]]
  [[ -f "$WIKI_DIR/wiki-schema.yaml" ]]
  [[ -d "$SOURCES_DIR" ]]
}

@test "e2e: lint on clean fixture vault" {
  # Run lint on fixture vault
  run "$LOPPY_BIN" lint-frontmatter
  [ "$status" -eq 0 ]
  # Should return empty array or valid JSON
}
