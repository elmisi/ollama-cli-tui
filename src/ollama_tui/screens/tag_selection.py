"""Tag selection screen for choosing model version to pull."""

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Label, Static

from ..ollama_client import ModelTag


class TagSelectionScreen(ModalScreen[str | None]):
    """Screen for selecting a model tag/version to pull."""

    DEFAULT_CSS = """
    TagSelectionScreen {
        align: center middle;
    }

    TagSelectionScreen > Vertical {
        width: 70;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: solid $primary;
        padding: 1 2;
    }

    TagSelectionScreen #title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    TagSelectionScreen #hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    TagSelectionScreen DataTable {
        height: auto;
        max-height: 20;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "select", "Select"),
    ]

    def __init__(self, model_name: str, tags: list[ModelTag]) -> None:
        super().__init__()
        self.model_name = model_name
        self.tags = tags

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Select version for {self.model_name}", id="title")
            yield DataTable(id="tag-table")
            yield Static("Enter=Select  Escape=Cancel", id="hint")

    def on_mount(self) -> None:
        table = self.query_one("#tag-table", DataTable)
        table.add_columns("Tag", "Size")
        table.cursor_type = "row"

        for tag in self.tags:
            # Show just the tag suffix (e.g., "8b" instead of "llama3.1:8b")
            tag_display = tag.tag.split(":")[-1] if ":" in tag.tag else tag.tag
            table.add_row(tag_display, tag.size, key=tag.tag)

        if table.row_count > 0:
            table.move_cursor(row=0)
            table.focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_select(self) -> None:
        table = self.query_one("#tag-table", DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            # Get the full tag from the row key
            row_key = table.get_row_at(table.cursor_row)
            # The key is stored, we need to get it differently
            cursor_row = table.cursor_row
            keys = list(table.rows.keys())
            if cursor_row < len(keys):
                full_tag = str(keys[cursor_row].value)
                self.dismiss(full_tag)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle double-click or Enter on row."""
        full_tag = str(event.row_key.value)
        self.dismiss(full_tag)
