#!/bin/sh
# Uninstall ollama-cli-tui

set -e

BIN_DIR="$HOME/.local/bin"

echo "Uninstalling ollama-cli-tui..."

rm -f "$BIN_DIR/ollama-tui"

# Remove .venv if running from the repo
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$SCRIPT_DIR/.venv" ]; then
    rm -rf "$SCRIPT_DIR/.venv"
    echo "Removed $SCRIPT_DIR/.venv"
fi

echo "Uninstallation complete!"
