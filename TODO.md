# TODO

Future improvements for ollama-cli-tui.

## Planned Features

### 1. Filter by parameter size in Search
Add ability to filter models by parameter count (e.g., show only 7B models, or models < 10GB).
- Add filter dropdown or input for size range
- Parse sizes from model data

### 2. Configurable refresh interval for Running tab
Allow users to customize the auto-refresh interval (currently fixed at 5 seconds).
- Add config file support (`~/.config/ollama-tui/config.toml`)
- Or command line option `--refresh-interval`

### 3. Fix pull output display
Ollama pull output still leaks to terminal in some cases.
- Investigate terminal escape sequences
- Better handling of progress output
- Consider using ollama API instead of CLI for pull

### 4. Fix pull crash
App sometimes crashes at the end of a pull operation.
- Debug the dismiss/callback flow
- Add error handling around completion

### 5. Fix Running tab not showing models
Models that are running don't appear in the Running tab list.
- Check `ollama ps` parsing
- Verify output format matches expected pattern

### 6. Chat with models
Add a Chat tab to interact with loaded models directly from the TUI.
- Text input for prompts
- Streaming response display
- Conversation history
- Model selection from loaded models

---

*Last updated: 2026-02-01*
