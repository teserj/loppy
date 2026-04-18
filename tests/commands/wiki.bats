#!/usr/bin/env bats

load ../helpers/setup

# Skills replace commands/wiki.js. Tests verify skill content quality.

@test "skill ingest: documents single mode" {
  grep -q "single" "$PLUGIN_ROOT/skills/ingest/SKILL.md"
}

@test "skill ingest: documents batch mode" {
  grep -q "batch" "$PLUGIN_ROOT/skills/ingest/SKILL.md"
}

@test "skill ingest: includes frontmatter schema" {
  grep -q "type:" "$PLUGIN_ROOT/skills/ingest/SKILL.md"
  grep -q "confidence:" "$PLUGIN_ROOT/skills/ingest/SKILL.md"
  grep -q "domain:" "$PLUGIN_ROOT/skills/ingest/SKILL.md"
}

@test "skill ingest: instructs to update index" {
  grep -q "index-merge" "$PLUGIN_ROOT/skills/ingest/SKILL.md"
}

@test "skill ingest: instructs to move source" {
  grep -q "loppy move" "$PLUGIN_ROOT/skills/ingest/SKILL.md"
}

@test "skill ingest: instructs to log operation" {
  grep -q "loppy log" "$PLUGIN_ROOT/skills/ingest/SKILL.md"
}

@test "skill query: uses ARGUMENTS placeholder" {
  grep -q "ARGUMENTS" "$PLUGIN_ROOT/skills/query/SKILL.md"
}

@test "skill query: documents filter syntax" {
  grep -q "type:" "$PLUGIN_ROOT/skills/query/SKILL.md"
  grep -q "domain:" "$PLUGIN_ROOT/skills/query/SKILL.md"
}

@test "skill lint: documents error categories" {
  grep -q "missing_field\|bad_enum\|broken_link" "$PLUGIN_ROOT/skills/lint/SKILL.md"
}

@test "skill lint: offers to fix issues" {
  grep -qi "fix" "$PLUGIN_ROOT/skills/lint/SKILL.md"
}

@test "skill lint: logs result" {
  grep -q "loppy log" "$PLUGIN_ROOT/skills/lint/SKILL.md"
}
