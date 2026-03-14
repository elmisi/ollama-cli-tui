# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ollama CLI TUI is a terminal user interface for managing Ollama models, built with Python and Textual. It scrapes the Ollama registry (no public API exists) to provide model discovery for 200+ models. Single external dependency: `textual>=0.50.0`. Requires Python 3.10+.

## Development Commands

```bash
# Run from source (development)
./run.py

# Alternative: run as module
PYTHONPATH=src python -m ollama_tui

# Clear cached registry data (useful when debugging scraping)
./run.py --flush-cache
```

There are no tests, linters, or formatters configured for this project.

## Architecture

### Entry Point Flow
`run.py` → `src/ollama_tui/app.py:main()` → `OllamaTUI` (Textual App)

### Core Components

**app.py** - Main Textual application with 3 tabs:
- Tab 1 (ModelsView): Local model management
- Tab 2 (PSView): Running models monitor (auto-refreshes every 5s)
- Tab 3 (SearchView): Registry browser with real-time filtering

**ollama_client.py** - All Ollama interactions:
- CLI wrapper: Executes `ollama list`, `ollama ps`, `ollama pull`, `ollama rm`, `ollama stop`, `ollama show` via `asyncio.create_subprocess_exec`
- Web scraper: Fetches model catalog from `ollama.com/library` and tags from `/library/{model}/tags` using `urllib.request` + regex HTML parsing
- Caching: 24h TTL JSON files stored in `~/.cache/ollama-tui/`

**screens/** - Modal dialogs (ConfirmDialog, TagSelectionScreen, PullProgressScreen, ModelInfoScreen). All inherit from `ModalScreen` and return results via `dismiss()`.

**widgets/** - Tab views (ModelsView, PSView, SearchView). Each is a `Vertical` container with a `DataTable` and status bar.

**styles/app.tcss** - Textual CSS for layout and theming.

### Key Patterns

**Async operations**: Use `@work(exclusive=True, group="name")` decorator for UI-blocking operations. Each widget creates its own `OllamaClient()` instance per operation.

**Modal screen callbacks**: Screens return values via `dismiss()`, consumed by the caller's callback:
```python
self.app.push_screen(ConfirmDialog("Delete?"), lambda confirmed: self._do_action() if confirmed else None)
```

**Cross-tab messaging**: `SearchView.PullCompleted` message bubbles up to `OllamaTUI.on_search_view_pull_completed()` which switches to Models tab and refreshes.

### Data Flow
1. CLI output is parsed via regex in `_parse_list_output()` and `_parse_ps_output()` — these are fragile and break when `ollama` changes its output format
2. Registry data is scraped via HTML regex parsing — fragile, depends on ollama.com HTML structure (CSS class names like `x-test-size`, `text-neutral-800`)
3. All async operations update the UI through Textual's reactive data binding

### Version Tracking
Version is defined in two places that must stay in sync:
- `src/ollama_tui/__init__.py` (`__version__`)
- `pyproject.toml` (`project.version`)

## Logging

Debug logs written to `ollama_tui.log` in project root (4 levels up from `app.py`).
