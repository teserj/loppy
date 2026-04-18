#!/usr/bin/env bats

load ../helpers/setup

setup() {
  isolate_env
  mkdir -p "$WIKI_DIR" "$SOURCES_DIR"
}

teardown() {
  cleanup_env
}

@test "wiki: command file exists" {
  [[ -f "$PLUGIN_ROOT/commands/wiki.js" ]]
}

@test "wiki: command is valid JavaScript" {
  node --check "$PLUGIN_ROOT/commands/wiki.js"
}

@test "wiki: exports handler function" {
  output=$(node -e "const m = require('$PLUGIN_ROOT/commands/wiki.js'); console.log(typeof m.handler)")
  [[ "$output" == "function" ]]
}

@test "wiki: exports subcommands array" {
  output=$(node -e "const m = require('$PLUGIN_ROOT/commands/wiki.js'); console.log(Array.isArray(m.subcommands))")
  [[ "$output" == "true" ]]
}

@test "wiki: ingest subcommand defined" {
  output=$(node -e "const m = require('$PLUGIN_ROOT/commands/wiki.js'); console.log(m.subcommands.some(s => s.name === 'ingest'))")
  [[ "$output" == "true" ]]
}

@test "wiki: query subcommand defined" {
  output=$(node -e "const m = require('$PLUGIN_ROOT/commands/wiki.js'); console.log(m.subcommands.some(s => s.name === 'query'))")
  [[ "$output" == "true" ]]
}

@test "wiki: lint subcommand defined" {
  output=$(node -e "const m = require('$PLUGIN_ROOT/commands/wiki.js'); console.log(m.subcommands.some(s => s.name === 'lint'))")
  [[ "$output" == "true" ]]
}

@test "wiki: handler accepts name, args, tools parameters" {
  output=$(node -e "const m = require('$PLUGIN_ROOT/commands/wiki.js'); console.log(m.handler.length >= 3 ? 'ok' : 'fail')")
  [[ "$output" == "ok" ]]
}

@test "wiki: ingest single mode returns readable output" {
  # Create a test source file
  echo "test content" > "$SOURCES_DIR/test.md"

  # Test ingest single mode - should return text mentioning the source
  output=$(node -e "
    process.env.XDG_CONFIG_HOME = '$XDG_CONFIG_HOME';
    const m = require('$PLUGIN_ROOT/commands/wiki.js');
    m.handler('wiki', ['ingest', 'single'], {}).then(result => {
      console.log(result);
    }).catch(err => {
      console.error('Error: ' + err.message);
      process.exit(1);
    });
  ")
  [[ "$output" =~ "test.md" ]] || [[ "$output" =~ "ingest" ]]
}

@test "wiki: query returns text mentioning no results when index missing" {
  output=$(node -e "
    process.env.XDG_CONFIG_HOME = '$XDG_CONFIG_HOME';
    const m = require('$PLUGIN_ROOT/commands/wiki.js');
    m.handler('wiki', ['query', 'test'], {}).then(result => {
      console.log(result);
    }).catch(err => {
      console.error('Error: ' + err.message);
      process.exit(1);
    });
  ")
  [[ "$output" =~ "index" ]] || [[ "$output" =~ "wiki" ]] || [[ "$output" =~ "No" ]]
}

@test "wiki: lint returns text about schema when no pages exist" {
  output=$(node -e "
    process.env.XDG_CONFIG_HOME = '$XDG_CONFIG_HOME';
    const m = require('$PLUGIN_ROOT/commands/wiki.js');
    m.handler('wiki', ['lint'], {}).then(result => {
      console.log(result);
    }).catch(err => {
      console.error('Error: ' + err.message);
      process.exit(1);
    });
  ")
  [[ "$output" =~ "schema" ]] || [[ "$output" =~ "valid" ]] || [[ "$output" =~ "issues" ]]
}
