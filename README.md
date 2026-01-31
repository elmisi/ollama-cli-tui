# Ollama CLI TUI

A terminal user interface for managing [Ollama](https://ollama.com) models. Built with Python and [Textual](https://textual.textualize.io/).

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Screenshots

### Models Tab
List, inspect, and delete local models.

![Models Tab](screenshots/01_models.svg)

### Running Tab
Monitor running models with auto-refresh.

![Running Tab](screenshots/02_running.svg)

### Search Tab
Search and pull models from the Ollama registry.

![Search Tab](screenshots/03_search.svg)

### Search with Filter
Real-time filtering as you type.

![Search Filter](screenshots/04_search_filter.svg)

## Features

- **Models View** - List, delete, and inspect local models
- **Running View** - Monitor running models with auto-refresh, stop models
- **Search View** - Search and pull models from the Ollama registry with real-time filtering
- **Keyboard-first** - Full keyboard navigation with mouse support
- **Progress tracking** - Visual progress bar during model downloads

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running

## Installation

### Quick Install (Recommended)

```bash
git clone https://github.com/elmisi/ollama-cli-tui.git
cd ollama-cli-tui
./install.sh
```

This creates a virtual environment and installs the `ollama-tui` command to `~/.local/bin/`.

### Uninstall

```bash
./uninstall.sh
```

### Manual Installation

```bash
git clone https://github.com/elmisi/ollama-cli-tui.git
cd ollama-cli-tui
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# If installed with install.sh
ollama-tui

# Or run directly from repo
./run.py

# Or with manual venv
source venv/bin/activate
PYTHONPATH=src python -m ollama_tui
```

## Keybindings

### Global

| Key | Action |
|-----|--------|
| `1` | Switch to Models tab |
| `2` | Switch to Running tab |
| `3` | Switch to Search tab |
| `←` `→` | Navigate between tabs |
| `q` | Quit |

### Models Tab

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate list |
| `Enter` | Show model info |
| `d` | Delete model |
| `r` | Refresh list |

### Running Tab

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate list |
| `s` | Stop model |
| `r` | Refresh list |

### Search Tab

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate list |
| `/` | Focus search input |
| `Enter` | Pull selected model |
| `Escape` | Back to list |
| `r` | Refresh from registry |

## Project Structure

```
ollama-cli-tui/
├── src/
│   └── ollama_tui/
│       ├── __init__.py         # Version info
│       ├── app.py              # Main application
│       ├── ollama_client.py    # Ollama CLI wrapper
│       ├── screens/            # Modal screens
│       │   ├── confirm_dialog.py
│       │   ├── model_info.py
│       │   └── pull_progress.py
│       ├── widgets/            # View widgets
│       │   ├── models_view.py
│       │   ├── ps_view.py
│       │   └── search_view.py
│       └── styles/
│           └── app.tcss        # CSS styling
├── scripts/
│   └── take_screenshots.py     # Screenshot generator
├── screenshots/                # Documentation images
├── install.sh                  # Installation script
├── uninstall.sh                # Uninstallation script
├── run.py                      # Entry point
├── pyproject.toml              # Build configuration
├── requirements.txt
└── README.md
```

## Development

### Regenerating Screenshots

After UI changes, regenerate the documentation screenshots:

```bash
source venv/bin/activate
python scripts/take_screenshots.py
```

Screenshots are saved as SVG files in the `screenshots/` directory.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

[elmisi](https://github.com/elmisi)
