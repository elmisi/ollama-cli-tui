"""Models view widget - list, delete, show info."""

import logging

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static
from textual.binding import Binding
from textual import work

from ..ollama_client import OllamaClient
from ..screens import ConfirmDialog, ModelInfoScreen

logger = logging.getLogger(__name__)


class ModelsView(Vertical):
    """View for managing local Ollama models."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
        Binding("d", "delete_model", "Delete", show=True),
        Binding("enter", "show_info", "Info", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield DataTable(id="models-table")
        yield Static("", id="status-bar")

    def on_mount(self) -> None:
        logger.info("ModelsView mounted")
        table = self.query_one("#models-table", DataTable)
        table.add_columns("Name", "ID", "Size", "Modified")
        table.cursor_type = "row"
        self.refresh_models()

    @work(exclusive=True, group="refresh")
    async def refresh_models(self) -> None:
        """Load models from ollama list."""
        table = self.query_one("#models-table", DataTable)
        table.loading = True

        client = OllamaClient()
        models = await client.list_models()

        table.clear()
        for model in models:
            table.add_row(model.name, model.id, model.size, model.modified)

        table.loading = False
        # Move cursor to first row after loading
        if table.row_count > 0:
            table.move_cursor(row=0)
        self.query_one("#status-bar", Static).update(f"{len(models)} models")

    def action_refresh(self) -> None:
        self.refresh_models()

    def action_delete_model(self) -> None:
        table = self.query_one("#models-table", DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            row = table.get_row_at(table.cursor_row)
            model_name = str(row[0])
            self.app.push_screen(
                ConfirmDialog(f"Delete model '{model_name}'?"),
                lambda confirmed: self._do_delete(model_name) if confirmed else None,
            )

    def action_show_info(self) -> None:
        table = self.query_one("#models-table", DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            row = table.get_row_at(table.cursor_row)
            model_name = str(row[0])
            self.app.push_screen(ModelInfoScreen(model_name))

    @work
    async def _do_delete(self, model_name: str) -> None:
        status = self.query_one("#status-bar", Static)
        status.update(f"Deleting {model_name}...")

        client = OllamaClient()
        success, message = await client.delete_model(model_name)

        if success:
            self.notify(f"Deleted {model_name}")
            self.refresh_models()
        else:
            self.notify(f"Failed: {message}", severity="error")
            status.update(f"Error: {message}")
