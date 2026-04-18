#!/bin/bash

# Loppy Plugin Validation Script
# Runs comprehensive checks before release

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Loppy Plugin Validation ==="
echo

# Check 1: File existence
echo "Check 1: Essential files exist"
files=(
  "setup.sh"
  "bin/loppy"
  "CLAUDE.md"
  "README.md"
  ".claude-plugin/plugin.json"
  "hooks/guard-vault.sh"
  "commands/wiki.js"
)

for f in "${files[@]}"; do
  if [[ -f "$f" ]]; then
    echo "  ✓ $f"
  else
    echo "  ✗ $f MISSING"
    exit 1
  fi
done
echo

# Check 2: Test count
echo "Check 2: Test coverage"
test_count=$(find tests -name "*.bats" -exec wc -l {} + | awk '{s+=$1} END {print s}')
if [[ $test_count -gt 500 ]]; then
  echo "  ✓ $test_count total test lines (sufficient coverage)"
else
  echo "  ✗ $test_count test lines (need >500)"
  exit 1
fi
echo

# Check 3: Plugin manifest
echo "Check 3: Plugin manifest validation"
if jq . .claude-plugin/plugin.json > /dev/null 2>&1; then
  echo "  ✓ plugin.json is valid JSON"
else
  echo "  ✗ plugin.json is invalid JSON"
  exit 1
fi

# Verify required fields
required_fields=("name" "version" "description" "commands" "hooks" "slashCommands")
for field in "${required_fields[@]}"; do
  if jq -e ".$field" .claude-plugin/plugin.json > /dev/null 2>&1; then
    echo "  ✓ plugin.json has .$field"
  else
    echo "  ✗ plugin.json missing .$field"
    exit 1
  fi
done
echo

# Check 4: Documentation
echo "Check 4: Documentation completeness"
if grep -q "## Scope" CLAUDE.md; then
  echo "  ✓ CLAUDE.md has Scope section"
else
  echo "  ✗ CLAUDE.md missing Scope section"
  exit 1
fi

if grep -q "## Architecture" README.md; then
  echo "  ✓ README.md has Architecture section"
else
  echo "  ✗ README.md missing Architecture section"
  exit 1
fi
echo

# Check 5: No temporary files
echo "Check 5: Clean working tree"
temp_files=$(find . -name "*.tmp" -o -name "*.swp" -o -name ".DS_Store" | wc -l)
if [[ $temp_files -eq 0 ]]; then
  echo "  ✓ No temporary files"
else
  echo "  ✗ Found $temp_files temporary files"
  exit 1
fi
echo

# Check 6: Shell syntax
echo "Check 6: Shell script syntax"
for f in setup.sh bin/loppy hooks/*.sh scripts/*.sh; do
  if [[ -f "$f" ]]; then
    if bash -n "$f" 2>/dev/null; then
      echo "  ✓ $f"
    else
      echo "  ✗ $f has syntax errors"
      exit 1
    fi
  fi
done
echo

# Check 7: Version consistency
echo "Check 7: Version consistency"
version=$(jq -r '.version' .claude-plugin/plugin.json)
echo "  Version in plugin.json: $version"
echo "  ✓ Version check (manual verification needed)"
echo

echo -e "${GREEN}=== All validations passed ===${NC}"
echo
echo "Next steps:"
echo "  1. Review RELEASE_CHECKLIST.md"
echo "  2. Run manual E2E tests from tests/fixtures/e2e-protocol.md"
echo "  3. Tag release: git tag -a v$version -m \"Release $version\""
echo "  4. Push with tags: git push origin --tags"
