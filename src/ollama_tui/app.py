"""Main Ollama TUI application."""

import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane, DataTable, Input

from . import __version__
from .ollama_client import OllamaClient
from .widgets import ModelsView, PSView, SearchView

# Setup file logging
LOG_FILE = Path(__file__).parent.parent.parent.parent / "ollama_tui.log"
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class OllamaTUI(App):
    """Main Ollama TUI Application."""

    CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"
    TITLE = f"Ollama TUI v{__version__}"

    BINDINGS = [
        Binding("1", "tab_models", "Models", show=True),
        Binding("2", "tab_ps", "Running", show=True),
        Binding("3", "tab_search", "Search", show=True),
        Binding("left", "tab_prev", "Prev Tab", show=False),
        Binding("right", "tab_next", "Next Tab", show=False),
        Binding("q", "quit", "Quit", show=True),
    ]

    TAB_ORDER = ["models", "ps", "search"]

    def compose(self) -> ComposeResult:
        logger.info("Composing app UI")
        yield Header()
        with TabbedContent(initial="models"):
            with TabPane("Models [1]", id="models"):
                yield ModelsView()
            with TabPane("Running [2]", id="ps"):
                yield PSView()
            with TabPane("Search [3]", id="search"):
                yield SearchView()
        yield Footer()
        logger.info("App UI composed")

    async def on_mount(self) -> None:
        """Check Ollama availability on startup."""
        logger.info("App mounted, checking ollama availability")
        client = OllamaClient()
        available = await client.check_available()
        logger.info(f"Ollama available: {available}")
        if not available:
            self.notify(
                "Ollama not found! Please install ollama.",
                severity="error",
                timeout=10,
            )
        # Focus on models table at startup
        self.query_one("#models-table", DataTable).focus()

    def action_tab_models(self) -> None:
        """Switch to Models tab."""
        self.query_one(TabbedContent).active = "models"
        self.call_after_refresh(lambda: self.query_one("#models-table", DataTable).focus())

    def action_tab_ps(self) -> None:
        """Switch to Running tab."""
        self.query_one(TabbedContent).active = "ps"
        self.call_after_refresh(lambda: self.query_one("#ps-table", DataTable).focus())

    def action_tab_search(self) -> None:
        """Switch to Search tab."""
        self.query_one(TabbedContent).active = "search"
        self.call_after_refresh(lambda: self.query_one("#search-table", DataTable).focus())

    def action_tab_prev(self) -> None:
        """Switch to previous tab."""
        tc = self.query_one(TabbedContent)
        current_idx = self.TAB_ORDER.index(tc.active)
        new_idx = (current_idx - 1) % len(self.TAB_ORDER)
        self._switch_to_tab(self.TAB_ORDER[new_idx])

    def action_tab_next(self) -> None:
        """Switch to next tab."""
        tc = self.query_one(TabbedContent)
        current_idx = self.TAB_ORDER.index(tc.active)
        new_idx = (current_idx + 1) % len(self.TAB_ORDER)
        self._switch_to_tab(self.TAB_ORDER[new_idx])

    def _switch_to_tab(self, tab_id: str) -> None:
        """Switch to tab and focus its main widget."""
        self.query_one(TabbedContent).active = tab_id
        table_ids = {
            "models": "#models-table",
            "ps": "#ps-table",
            "search": "#search-table",
        }
        self.call_after_refresh(lambda: self.query_one(table_ids[tab_id], DataTable).focus())

    def on_search_view_pull_completed(self, event: SearchView.PullCompleted) -> None:
        """Handle pull completed - switch to Models tab and refresh."""
        self.action_tab_models()
        self.query_one(ModelsView).refresh_models()


def main():
    """Run the Ollama TUI application."""
    app = OllamaTUI()
    app.run()


if __name__ == "__main__":
    main()
