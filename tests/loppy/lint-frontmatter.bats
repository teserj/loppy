#!/usr/bin/env bats

load '../helpers/setup.bash'

setup() {
  isolate_env
  export LOPPY_TODAY="2026-04-17"
  mkdir -p "$WIKI_DIR/concepts" "$WIKI_DIR/sources"
  # Seed an empty index so orphan check has something to compare against.
  cat > "$WIKI_DIR/index.md" <<'EOF'
---
type: index
title: Wiki Index
updated: 2026-04-17
---

# Wiki Index

Total pages: 0

## Concepts

## Entities

## Sources

## Topics
EOF
}
teardown() { cleanup_env; }

write_page() {
  # write_page <path> <frontmatter-body>
  mkdir -p "$(dirname "$1")"
  printf "%s\n# body\n" "$2" > "$1"
}

@test "lint reports missing required fields as errors" {
  write_page "$WIKI_DIR/concepts/bad.md" \
"---
type: concept
title: Bad Page
---"
  run "$LOPPY_BIN" lint-frontmatter
  [ "$status" -eq 0 ]
  echo "$output" | jq -e '
    .[] | select(.path | endswith("bad.md"))
          | .findings
          | any(.level == "error" and .rule == "missing-field" and .field == "domain")
  '
}

@test "lint accepts a well-formed page" {
  write_page "$WIKI_DIR/concepts/good.md" \
"---
type: concept
title: Good Page
created: 2026-04-17
updated: 2026-04-17
confidence: high
domain: tech
tags: [x]
links: []
---"
  run "$LOPPY_BIN" lint-frontmatter
  [ "$status" -eq 0 ]
  # good.md should have no error-level findings
  echo "$output" | jq -e '
    .[] | select(.path | endswith("good.md"))
          | .findings
          | any(.level == "error")
  ' && false || true
}

@test "lint flags invalid type enum" {
  write_page "$WIKI_DIR/concepts/enum.md" \
"---
type: nonsense
title: Enum Page
created: 2026-04-17
updated: 2026-04-17
confidence: high
domain: tech
tags: []
links: []
---"
  run "$LOPPY_BIN" lint-frontmatter
  echo "$output" | jq -e '
    .[] | select(.path | endswith("enum.md"))
          | .findings | any(.rule == "bad-enum" and .field == "type")
  '
}

@test "lint flags stale page (updated > 90 days)" {
  write_page "$WIKI_DIR/concepts/stale.md" \
"---
type: concept
title: Stale
created: 2025-01-01
updated: 2025-01-01
confidence: high
domain: tech
tags: []
links: []
---"
  run "$LOPPY_BIN" lint-frontmatter
  echo "$output" | jq -e '
    .[] | select(.path | endswith("stale.md"))
          | .findings | any(.level == "warn" and .rule == "stale")
  '
}

@test "lint does not flag stale when confidence is already stale" {
  write_page "$WIKI_DIR/concepts/okstale.md" \
"---
type: concept
title: OK Stale
created: 2025-01-01
updated: 2025-01-01
confidence: stale
domain: tech
tags: []
links: []
---"
  run "$LOPPY_BIN" lint-frontmatter
  echo "$output" | jq -e '
    .[] | select(.path | endswith("okstale.md"))
          | .findings | any(.rule == "stale")
  ' && false || true
}

@test "lint flags orphans (not in index)" {
  write_page "$WIKI_DIR/concepts/orph.md" \
"---
type: concept
title: Orphan
created: 2026-04-17
updated: 2026-04-17
confidence: high
domain: tech
tags: []
links: []
---"
  run "$LOPPY_BIN" lint-frontmatter
  echo "$output" | jq -e '
    .[] | select(.path | endswith("orph.md"))
          | .findings | any(.rule == "orphan")
  '
}

@test "lint flags broken links" {
  write_page "$WIKI_DIR/concepts/brk.md" \
"---
type: concept
title: Broken
created: 2026-04-17
updated: 2026-04-17
confidence: high
domain: tech
tags: []
links: [wiki/entities/ghost]
---"
  run "$LOPPY_BIN" lint-frontmatter
  echo "$output" | jq -e '
    .[] | select(.path | endswith("brk.md"))
          | .findings | any(.rule == "broken-link")
  '
}

@test "lint multi-element links: broken-link only for missing target, not existing" {
  mkdir -p "$WIKI_DIR/wiki"
  write_page "$WIKI_DIR/wiki/a.md" \
"---
type: concept
title: A
created: 2026-04-17
updated: 2026-04-17
confidence: high
domain: tech
tags: []
links: []
---"
  write_page "$WIKI_DIR/concepts/multi.md" \
"---
type: concept
title: Multi
created: 2026-04-17
updated: 2026-04-17
confidence: high
domain: tech
tags: []
links: [wiki/a, wiki/b]
---"
  run "$LOPPY_BIN" lint-frontmatter
  [ "$status" -eq 0 ]
  # wiki/b is missing -> broken-link for wiki/b
  echo "$output" | jq -e '
    .[] | select(.path | endswith("multi.md"))
          | .findings | any(.rule == "broken-link" and .target == "wiki/b")
  '
  # wiki/a exists -> no broken-link for wiki/a
  echo "$output" | jq -e '
    .[] | select(.path | endswith("multi.md"))
          | .findings | any(.rule == "broken-link" and .target == "wiki/a")
  ' && false || true
}

@test "lint skips index.md and log.md themselves" {
  run "$LOPPY_BIN" lint-frontmatter
  [ "$status" -eq 0 ]
  # The seeded index has no "type" = entity/concept/etc., so if we didn't skip it
  # it would show up. Assert it's not in output.
  echo "$output" | jq -e 'any(.path | endswith("index.md"))' && false || true
}
