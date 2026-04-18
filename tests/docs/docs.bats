#!/usr/bin/env bats

load '../helpers/setup.bash'

@test "docs: CLAUDE.md exists" {
  [[ -f "$PLUGIN_ROOT/CLAUDE.md" ]]
}

@test "docs: README.md exists" {
  [[ -f "$PLUGIN_ROOT/README.md" ]]
}

@test "docs: CLAUDE.md has scope section" {
  grep -q "## Scope" "$PLUGIN_ROOT/CLAUDE.md"
}

@test "docs: CLAUDE.md documents bin commands" {
  grep -q "bin/loppy" "$PLUGIN_ROOT/CLAUDE.md"
}

@test "docs: CLAUDE.md documents slash commands" {
  grep -q "/wiki" "$PLUGIN_ROOT/CLAUDE.md"
}

@test "docs: CLAUDE.md mentions guard hook" {
  grep -q "guard-vault" "$PLUGIN_ROOT/CLAUDE.md"
}

@test "docs: README.md has quick start" {
  grep -qE "(## Quick Start|## Installation|## Getting Started)" "$PLUGIN_ROOT/README.md"
}

@test "docs: README.md has usage examples" {
  grep -q "## Usage" "$PLUGIN_ROOT/README.md"
}

@test "docs: README.md has architecture section" {
  grep -q "## Architecture" "$PLUGIN_ROOT/README.md"
}

@test "docs: README.md mentions Karpathy" {
  grep -q -i "karpathy\|llm wiki" "$PLUGIN_ROOT/README.md"
}
