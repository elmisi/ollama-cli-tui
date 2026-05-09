#!/bin/sh
# Install ollama-cli-tui from a local clone

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"

# Verify we're in the repo
if [ ! -f "$SCRIPT_DIR/run.py" ]; then
    echo "Error: run this script from inside the ollama-cli-tui repo."
    exit 1
fi

echo "Installing ollama-cli-tui..."

# Check Python 3.10+
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required but not found."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo "Error: Python 3.10+ is required (found $PYTHON_VERSION)."
    exit 1
fi

# Create/update virtual environment
VENV_DIR="$SCRIPT_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    echo "Updating virtual environment..."
else
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet --upgrade

# Create bin directory and wrapper script
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/ollama-tui" << EOF
#!/bin/sh
"$VENV_DIR/bin/python" "$SCRIPT_DIR/run.py" "\$@"
EOF

chmod +x "$BIN_DIR/ollama-tui"

VERSION=$("$VENV_DIR/bin/python" -c "import sys; sys.path.insert(0, '$SCRIPT_DIR/src'); from ollama_tui import __version__; print(__version__)" 2>/dev/null || echo "unknown")

echo ""
echo "ollama-tui v${VERSION} installed successfully!"
echo ""

# Check if BIN_DIR is in PATH
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
    echo "Add $BIN_DIR to your PATH:"
    echo ""
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

echo "Run: ollama-tui"
