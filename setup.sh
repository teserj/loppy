#!/bin/bash

# Loppy Setup Script
# Initializes a new Loppy vault in user's directory with interactive prompts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Loppy Vault Setup ===${NC}"
echo

# Prompt for VAULT_DIR
while true; do
  read -p "Enter path to vault directory (required): " VAULT_DIR
  if [[ -z "$VAULT_DIR" ]]; then
    echo -e "${RED}Error: vault directory is required${NC}"
    continue
  fi

  # Resolve to absolute path
  if [[ ! "$VAULT_DIR" = /* ]]; then
    VAULT_DIR="$(cd "$(dirname "$VAULT_DIR")" && pwd)/$(basename "$VAULT_DIR")"
  fi

  # Create if doesn't exist
  if [[ ! -d "$VAULT_DIR" ]]; then
    mkdir -p "$VAULT_DIR"
    echo "Created directory: $VAULT_DIR"
  fi

  break
done

# Prompt for SOURCES_DIR
read -p "Relative path to raw sources (default: source): " SOURCES_DIR
SOURCES_DIR="${SOURCES_DIR:-source}"

# Prompt for WIKI_DIR
read -p "Relative path to compiled wiki (default: wiki): " WIKI_DIR
WIKI_DIR="${WIKI_DIR:-wiki}"

# Create subdirectories
mkdir -p "$VAULT_DIR/$SOURCES_DIR" "$VAULT_DIR/$WIKI_DIR"
echo "Created subdirectories: $SOURCES_DIR/, $WIKI_DIR/"
echo

# Determine config directory
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/loppy"
mkdir -p "$CONFIG_DIR"

# Build config JSON with absolute paths
CONFIG_FILE="$CONFIG_DIR/config.json"
SOURCES_ABS="$VAULT_DIR/$SOURCES_DIR"
WIKI_ABS="$VAULT_DIR/$WIKI_DIR"

cat > "$CONFIG_FILE" <<EOJSON
{
  "vault_dir": "$VAULT_DIR",
  "sources_dir": "$SOURCES_ABS",
  "wiki_dir": "$WIKI_ABS",
  "batch_size": 5
}
EOJSON

echo "Config saved: $CONFIG_FILE"
echo

# Copy templates
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [[ -d "$SCRIPT_DIR/templates" ]]; then
  cp "$SCRIPT_DIR/templates/wiki-schema.yaml" "$VAULT_DIR/"
  cp "$SCRIPT_DIR/templates/index.md" "$VAULT_DIR/"
  cp "$SCRIPT_DIR/templates/log.md" "$VAULT_DIR/"
  echo "Templates copied to vault"
else
  echo -e "${RED}Warning: templates directory not found${NC}"
fi
echo

# Initialize git if needed
if [[ ! -d "$VAULT_DIR/.git" ]]; then
  read -p "Initialize git repository in vault? (y/n): " INIT_GIT
  if [[ "$INIT_GIT" =~ ^[Yy]$ ]]; then
    cd "$VAULT_DIR"
    git init
    echo "Git repository initialized"
  fi
else
  echo "Git repository already exists"
fi

echo
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo "Vault: $VAULT_DIR"
echo "Sources: $SOURCES_DIR"
echo "Wiki: $WIKI_DIR"
echo "Config: $CONFIG_FILE"
echo
echo "Next steps:"
echo "1. Place raw source files in: $VAULT_DIR/$SOURCES_DIR/"
echo "2. Run: loppy next 1"
echo "3. Run: loppy query <search-term>"
echo
