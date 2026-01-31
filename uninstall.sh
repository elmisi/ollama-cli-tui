#!/bin/bash
# Uninstall ollama-cli-tui

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
BIN_DIR="$HOME/.local/bin"

echo "Uninstalling ollama-cli-tui..."

# Remove wrapper script
rm -f "$BIN_DIR/ollama-tui"

# Remove virtual environment
rm -rf "$VENV_DIR"

echo "Uninstallation complete!"
