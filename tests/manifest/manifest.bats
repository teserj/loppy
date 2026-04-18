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

@test "manifest: has commands array" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.commands | type == "array"' "$manifest" > /dev/null
}

@test "manifest: defines config command" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.commands[] | select(.name == "config")' "$manifest" > /dev/null
}

@test "manifest: defines next command" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.commands[] | select(.name == "next")' "$manifest" > /dev/null
}

@test "manifest: defines move command" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.commands[] | select(.name == "move")' "$manifest" > /dev/null
}

@test "manifest: defines index-merge command" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.commands[] | select(.name == "index-merge")' "$manifest" > /dev/null
}

@test "manifest: defines log command" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.commands[] | select(.name == "log")' "$manifest" > /dev/null
}

@test "manifest: defines lint-frontmatter command" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.commands[] | select(.name == "lint-frontmatter")' "$manifest" > /dev/null
}

@test "manifest: has hooks array" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.hooks | type == "array"' "$manifest" > /dev/null
}

@test "manifest: defines guard-vault hook" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.hooks[] | select(.id == "guard-vault")' "$manifest" > /dev/null
}

@test "manifest: guard-vault is PreToolUse" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  event=$(jq -r '.hooks[] | select(.id == "guard-vault") | .event' "$manifest")
  [[ "$event" == "PreToolUse" ]]
}

@test "manifest: has slashCommands array" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.slashCommands | type == "array"' "$manifest" > /dev/null
}

@test "manifest: defines wiki slash command" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.slashCommands[] | select(.name == "wiki")' "$manifest" > /dev/null
}

@test "manifest: wiki command has subcommands" {
  manifest="$BATS_TEST_DIRNAME/../../.claude-plugin/plugin.json"
  jq -e '.slashCommands[] | select(.name == "wiki") | .subcommands | length > 0' "$manifest" > /dev/null
}
