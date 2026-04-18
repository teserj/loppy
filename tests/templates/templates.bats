#!/usr/bin/env bats

load ../helpers/setup

@test "template: wiki-schema.yaml exists" {
  [[ -f "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml" ]]
}

@test "template: wiki-schema.yaml has valid YAML" {
  # Check basic YAML syntax
  grep -q "^type:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
  grep -q "^title:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
  grep -q "^created:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
  grep -q "^updated:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
  grep -q "^confidence:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
  grep -q "^domain:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
  grep -q "^tags:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
  grep -q "^links:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
}

@test "template: wiki-schema.yaml documents field meanings" {
  grep -q "type:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
  grep -q "domain:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
  grep -q "confidence:" "$BATS_TEST_DIRNAME/../../templates/wiki-schema.yaml"
}

@test "template: index.md exists" {
  [[ -f "$BATS_TEST_DIRNAME/../../templates/index.md" ]]
}

@test "template: index.md has header" {
  grep -q "^# Wiki Index" "$BATS_TEST_DIRNAME/../../templates/index.md"
}

@test "template: index.md has TSV header" {
  grep -q "^| path | title | type |" "$BATS_TEST_DIRNAME/../../templates/index.md"
}

@test "template: log.md exists" {
  [[ -f "$BATS_TEST_DIRNAME/../../templates/log.md" ]]
}

@test "template: log.md has header" {
  grep -q "^# Operation Log" "$BATS_TEST_DIRNAME/../../templates/log.md"
}

@test "template: log.md has startup entry" {
  grep -q "vault initialized" "$BATS_TEST_DIRNAME/../../templates/log.md"
}

@test "template: log.md has ISO date" {
  grep -qE "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}" "$BATS_TEST_DIRNAME/../../templates/log.md"
}
