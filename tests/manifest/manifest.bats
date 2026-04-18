#!/usr/bin/env bats

load ../helpers/setup

@test "manifest: plugin.json exists" {
  [[ -f "$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json" ]]
}

@test "manifest: valid JSON" {
  jq . "$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json" > /dev/null
}

@test "manifest: has required metadata fields" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.name' "$manifest" > /dev/null
  jq -e '.version' "$manifest" > /dev/null
  jq -e '.description' "$manifest" > /dev/null
  jq -e '.author' "$manifest" > /dev/null
}

@test "manifest: no commands/hooks/slashCommands (metadata only)" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  # plugin.json should be metadata only per Claude Code spec
  jq -e 'has("commands") | not' "$manifest" > /dev/null
  jq -e 'has("slashCommands") | not' "$manifest" > /dev/null
}

@test "skills: ingest SKILL.md exists" {
  [[ -f "$BATS_TEST_DIRNAME/../../skills/ingest/SKILL.md" ]]
}

@test "skills: query SKILL.md exists" {
  [[ -f "$BATS_TEST_DIRNAME/../../skills/query/SKILL.md" ]]
}

@test "skills: lint SKILL.md exists" {
  [[ -f "$BATS_TEST_DIRNAME/../../skills/lint/SKILL.md" ]]
}

@test "skills: ingest has description in frontmatter" {
  grep -q "^description:" "$BATS_TEST_DIRNAME/../../skills/ingest/SKILL.md"
}

@test "skills: query has description in frontmatter" {
  grep -q "^description:" "$BATS_TEST_DIRNAME/../../skills/query/SKILL.md"
}

@test "skills: lint has description in frontmatter" {
  grep -q "^description:" "$BATS_TEST_DIRNAME/../../skills/lint/SKILL.md"
}

@test "skills: ingest references loppy commands" {
  grep -q "loppy" "$BATS_TEST_DIRNAME/../../skills/ingest/SKILL.md"
}

@test "skills: query references loppy commands" {
  grep -q "loppy" "$BATS_TEST_DIRNAME/../../skills/query/SKILL.md"
}

@test "skills: lint references loppy commands" {
  grep -q "loppy lint-frontmatter" "$BATS_TEST_DIRNAME/../../skills/lint/SKILL.md"
}

@test "hooks: hooks.json exists" {
  [[ -f "$BATS_TEST_DIRNAME/../../hooks/hooks.json" ]]
}

@test "hooks: hooks.json valid JSON" {
  jq . "$BATS_TEST_DIRNAME/../../hooks/hooks.json" > /dev/null
}

@test "hooks: PreToolUse guard-vault registered" {
  jq -e '.hooks.PreToolUse | length > 0' "$BATS_TEST_DIRNAME/../../hooks/hooks.json" > /dev/null
}

@test "hooks: guard-vault matches Bash tool" {
  matcher=$(jq -r '.hooks.PreToolUse[0].matcher' "$BATS_TEST_DIRNAME/../../hooks/hooks.json")
  [[ "$matcher" == "Bash" ]]
}
