"""Model info modal screen."""

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static, Label
from textual import work

from ..ollama_client import OllamaClient


class ModelInfoScreen(ModalScreen):
    """Modal screen showing detailed model information."""

    DEFAULT_CSS = """
    ModelInfoScreen {
        align: center middle;
    }

    ModelInfoScreen > Vertical {
        width: 80%;
        height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    ModelInfoScreen #info-title {
        text-style: bold;
        margin-bottom: 1;
    }

    ModelInfoScreen VerticalScroll {
        height: 1fr;
        border: solid $secondary;
        padding: 1;
    }

    ModelInfoScreen #close-btn {
        margin-top: 1;
        width: 100%;
    }
    """

    def __init__(self, model_name: str) -> None:
        super().__init__()
        self.model_name = model_name

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Model: {self.model_name}", id="info-title")
            with VerticalScroll():
                yield Static("Loading...", id="model-info")
            yield Button("Close [Esc]", variant="primary", id="close-btn")

    def on_mount(self) -> None:
        self.query_one("#close-btn", Button).focus()
        self.load_info()

    @work
    async def load_info(self) -> None:
        client = OllamaClient()
        info = await client.show_model(self.model_name)
        self.query_one("#model-info", Static).update(info)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-btn":
            self.dismiss()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss()
