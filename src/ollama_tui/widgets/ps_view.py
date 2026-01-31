"""PS view widget - running models with auto-refresh."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static
from textual.binding import Binding
from textual import work

from ..ollama_client import OllamaClient
from ..screens import ConfirmDialog


class PSView(Vertical):
    """View for monitoring running Ollama models."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "stop_model", "Stop", show=True),
    ]

    def __init__(self, refresh_interval: int = 5) -> None:
        super().__init__()
        self.refresh_interval = refresh_interval
        self._refresh_timer = None

    def compose(self) -> ComposeResult:
        yield Static(
            f"Running Models (auto-refresh: {self.refresh_interval}s)",
            id="ps-title",
        )
        yield DataTable(id="ps-table")
        yield Static("", id="ps-status")

    def on_mount(self) -> None:
        table = self.query_one("#ps-table", DataTable)
        table.add_columns("Name", "ID", "Size", "Processor", "Context", "Until")
        table.cursor_type = "row"
        self.refresh_ps()
        self._refresh_timer = self.set_interval(self.refresh_interval, self.refresh_ps)

    def on_unmount(self) -> None:
        if self._refresh_timer:
            self._refresh_timer.stop()

    @work(exclusive=True, group="refresh")
    async def refresh_ps(self) -> None:
        """Load running models from ollama ps."""
        table = self.query_one("#ps-table", DataTable)

        client = OllamaClient()
        models = await client.list_running()

        table.clear()
        for model in models:
            table.add_row(
                model.name,
                model.id,
                model.size,
                model.processor,
                model.context,
                model.until,
            )

        status = self.query_one("#ps-status", Static)
        if models:
            status.update(f"{len(models)} running")
        else:
            status.update("No models running")

    def action_refresh(self) -> None:
        self.refresh_ps()

    def action_stop_model(self) -> None:
        table = self.query_one("#ps-table", DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            row = table.get_row_at(table.cursor_row)
            model_name = str(row[0])
            self.app.push_screen(
                ConfirmDialog(f"Stop model '{model_name}'?"),
                lambda confirmed: self._do_stop(model_name) if confirmed else None,
            )

    @work
    async def _do_stop(self, model_name: str) -> None:
        status = self.query_one("#ps-status", Static)
        status.update(f"Stopping {model_name}...")

        client = OllamaClient()
        success, message = await client.stop_model(model_name)

        if success:
            self.notify(f"Stopped {model_name}")
            self.refresh_ps()
        else:
            self.notify(f"Failed: {message}", severity="error")
            status.update(f"Error: {message}")
