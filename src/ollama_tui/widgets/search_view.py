"""Search view widget - search and pull remote models."""

import logging

from datetime import datetime, timedelta

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import DataTable, Input, Static, Select
from textual.binding import Binding
from textual import work
from textual.message import Message

from ..ollama_client import OllamaClient, RemoteModel, parse_param_sizes
from ..screens import ConfirmDialog, PullProgressScreen, TagSelectionScreen

logger = logging.getLogger(__name__)

PERIOD_OPTIONS = [
    ("All time", "all"),
    ("Last week", "week"),
    ("Last month", "month"),
    ("Last year", "year"),
]

PARAMS_OPTIONS = [
    ("Any size", "all"),
    ("< 1B", "1"),
    ("< 7B", "7"),
    ("< 14B", "14"),
    ("< 70B", "70"),
]

CLOUD_OPTIONS = [
    ("All models", "all"),
    ("Hide cloud-only", "hide"),
]


class SearchView(Vertical):
    """View for searching and pulling remote Ollama models."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
        Binding("p", "pull_model", "Pull", show=True),
        Binding("/", "focus_search", "Search", show=True),
        Binding("escape", "focus_table", "Back to list", show=False),
    ]

    class PullCompleted(Message):
        """Message sent when a pull is completed."""
        pass

    def __init__(self) -> None:
        super().__init__()
        self._all_models: list[RemoteModel] = []

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Type to filter models... [/]", id="search-input")
        with Horizontal(id="filter-bar"):
            yield Select(PERIOD_OPTIONS, value="all", id="filter-period", prompt="Period")
            yield Select(PARAMS_OPTIONS, value="all", id="filter-params", prompt="Params")
            yield Select(CLOUD_OPTIONS, value="all", id="filter-cloud", prompt="Cloud")
        yield DataTable(id="search-table")
        yield Static("", id="search-status")

    def on_mount(self) -> None:
        table = self.query_one("#search-table", DataTable)
        table.add_columns("Name", "Parameters", "Updated", "Description")
        table.cursor_type = "row"
        self.load_models()

    @work(exclusive=True, group="load")
    async def load_models(self) -> None:
        """Load models from Ollama registry."""
        table = self.query_one("#search-table", DataTable)
        status = self.query_one("#search-status", Static)
        table.loading = True
        status.update("Loading models from registry...")

        client = OllamaClient()
        self._all_models = await client.search_models()

        self._update_table("")
        table.loading = False

    def _update_table(self, filter_text: str) -> None:
        """Update table with filtered models."""
        table = self.query_one("#search-table", DataTable)
        status = self.query_one("#search-status", Static)

        period = self.query_one("#filter-period", Select).value
        params_max = self.query_one("#filter-params", Select).value
        cloud_filter = self.query_one("#filter-cloud", Select).value

        table.clear()
        filter_lower = filter_text.lower()
        count = 0
        any_filter_active = filter_text or period != "all" or params_max != "all" or cloud_filter != "all"

        for model in self._all_models:
            if filter_lower and filter_lower not in model.name.lower():
                continue

            param_sizes = parse_param_sizes(model.sizes)

            if cloud_filter == "hide" and model.is_cloud and not param_sizes:
                continue

            if period != "all" and model.updated_date:
                if not self._passes_period_filter(model.updated_date, period):
                    continue

            if params_max != "all" and param_sizes:
                max_val = float(params_max)
                if not any(s < max_val for s in param_sizes):
                    continue

            desc = model.description[:60] + "..." if len(model.description) > 60 else model.description
            table.add_row(model.name, model.sizes, model.updated, desc)
            count += 1

        if table.row_count > 0:
            table.move_cursor(row=0)

        status.update(f"{count} models" + (" (filtered)" if any_filter_active else ""))

    @staticmethod
    def _passes_period_filter(updated_date: str, period: str) -> bool:
        try:
            model_date = datetime.fromisoformat(updated_date)
        except ValueError:
            return True
        now = datetime.now()
        cutoffs = {
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "year": timedelta(days=365),
        }
        cutoff = cutoffs.get(period)
        if cutoff is None:
            return True
        return (now - model_date) <= cutoff

    def on_select_changed(self, event: Select.Changed) -> None:
        search_text = self.query_one("#search-input", Input).value
        self._update_table(search_text)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self._update_table(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            self.query_one("#search-table", DataTable).focus()

    def action_focus_table(self) -> None:
        self.query_one("#search-table", DataTable).focus()

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_refresh(self) -> None:
        self.load_models()

    def action_pull_model(self) -> None:
        table = self.query_one("#search-table", DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            row = table.get_row_at(table.cursor_row)
            model_name = str(row[0])
            self._fetch_and_show_tags(model_name)

    @work(exclusive=True, group="fetch_tags")
    async def _fetch_and_show_tags(self, model_name: str) -> None:
        """Fetch tags for a model and show selection screen."""
        status = self.query_one("#search-status", Static)
        status.update(f"Loading versions for {model_name}...")

        client = OllamaClient()
        tags = await client.fetch_model_tags(model_name)

        if not tags:
            status.update(f"No versions found for {model_name}")
            return

        # Fetch local models to mark already-downloaded tags
        local_models = await client.list_models()
        local_names = {m.name for m in local_models}

        status.update(f"{len(tags)} versions available")
        self.app.push_screen(
            TagSelectionScreen(model_name, tags, local_names),
            self._on_tag_selected,
        )

    def _on_tag_selected(self, tag: str | None) -> None:
        """Handle tag selection."""
        if tag:
            self.app.push_screen(
                ConfirmDialog(f"Pull '{tag}'?"),
                lambda confirmed: self._start_pull(tag) if confirmed else None,
            )

    def _start_pull(self, tag: str) -> None:
        """Start pull with progress screen."""
        self.app.push_screen(
            PullProgressScreen(tag),
            lambda success: self._on_pull_done(success),
        )

    def _on_pull_done(self, success: bool) -> None:
        """Called when pull completes."""
        if success:
            self.post_message(self.PullCompleted())
