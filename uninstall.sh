#!/bin/bash
# Uninstall ollama-cli-tui

set -e

INSTALL_DIR="$HOME/.local/share/ollama-tui"
BIN_DIR="$HOME/.local/bin"

echo "Uninstalling ollama-cli-tui..."

# Remove wrapper script
rm -f "$BIN_DIR/ollama-tui"

# Remove remote installation if present
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "Removed $INSTALL_DIR"
fi

# Remove local .venv if running from a clone
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$SCRIPT_DIR/.venv" ] && [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
    rm -rf "$SCRIPT_DIR/.venv"
    echo "Removed $SCRIPT_DIR/.venv"
fi

echo "Uninstallation complete!"
