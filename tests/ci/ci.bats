#!/usr/bin/env bats

load ../helpers/setup

@test "ci: GitHub workflow exists" {
  [[ -f "$BATS_TEST_DIRNAME/../../.github/workflows/ci.yml" ]]
}

@test "ci: validate script exists and is executable" {
  [[ -x "$BATS_TEST_DIRNAME/../../scripts/validate.sh" ]]
}

@test "ci: validate script is valid bash" {
  bash -n "$BATS_TEST_DIRNAME/../../scripts/validate.sh"
}

@test "ci: release checklist exists" {
  [[ -f "$BATS_TEST_DIRNAME/../../RELEASE_CHECKLIST.md" ]]
}

@test "ci: workflow file is valid YAML" {
  # Check basic YAML structure
  grep -q "^name:" "$BATS_TEST_DIRNAME/../../.github/workflows/ci.yml"
  grep -q "^on:" "$BATS_TEST_DIRNAME/../../.github/workflows/ci.yml"
  grep -q "^jobs:" "$BATS_TEST_DIRNAME/../../.github/workflows/ci.yml"
}

@test "ci: workflow runs tests" {
  grep -q "bats" "$BATS_TEST_DIRNAME/../../.github/workflows/ci.yml"
}

@test "ci: workflow validates plugin" {
  grep -q "validate\|plugin\|jq" "$BATS_TEST_DIRNAME/../../.github/workflows/ci.yml"
}

@test "ci: release checklist has items" {
  grep -q '\- \[ \]' "$BATS_TEST_DIRNAME/../../RELEASE_CHECKLIST.md"
  [[ $(grep -c '\- \[ \]' "$BATS_TEST_DIRNAME/../../RELEASE_CHECKLIST.md") -ge 5 ]]
}
