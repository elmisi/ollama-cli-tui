#!/bin/bash
# Install ollama-cli-tui
# Works both locally (./install.sh) and via curl (curl -fsSL <url> | sh)

set -e

REPO_URL="https://github.com/elmisi/ollama-cli-tui.git"
INSTALL_DIR="$HOME/.local/share/ollama-tui"
BIN_DIR="$HOME/.local/bin"

# Detect if running from a local clone or piped via curl
if [ -f "$(dirname "$0")/run.py" ] 2>/dev/null && [ -t 0 ]; then
    SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
else
    SOURCE_DIR=""
fi

echo "Installing ollama-cli-tui..."

# Check Python 3.10+
if ! command -v python3 &>/dev/null; then
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

if [ -z "$SOURCE_DIR" ]; then
    # Remote install: clone or update repo
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "Updating existing installation..."
        git -C "$INSTALL_DIR" fetch --quiet
        git -C "$INSTALL_DIR" reset --hard origin/main --quiet
    else
        # Clean up non-git remnants if any
        rm -rf "$INSTALL_DIR"
        echo "Cloning repository..."
        git clone --quiet "$REPO_URL" "$INSTALL_DIR"
    fi
    SOURCE_DIR="$INSTALL_DIR"
fi

# Create/update virtual environment
VENV_DIR="$SOURCE_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    echo "Updating virtual environment..."
else
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install -r "$SOURCE_DIR/requirements.txt" --quiet --upgrade

# Create bin directory and wrapper script
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/ollama-tui" << EOF
#!/bin/bash
"$VENV_DIR/bin/python" "$SOURCE_DIR/run.py" "\$@"
EOF

chmod +x "$BIN_DIR/ollama-tui"

VERSION=$("$VENV_DIR/bin/python" -c "import sys; sys.path.insert(0, '$SOURCE_DIR/src'); from ollama_tui import __version__; print(__version__)" 2>/dev/null || echo "unknown")

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
