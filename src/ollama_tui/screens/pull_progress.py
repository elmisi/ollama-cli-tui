"""Pull progress modal screen."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static, Label, ProgressBar
from textual import work
from textual.message import Message

from ..ollama_client import OllamaClient


class PullProgressScreen(ModalScreen[bool]):
    """Modal screen showing pull progress."""

    DEFAULT_CSS = """
    PullProgressScreen {
        align: center middle;
    }

    PullProgressScreen > Vertical {
        width: 70;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    PullProgressScreen #pull-title {
        text-style: bold;
        margin-bottom: 1;
    }

    PullProgressScreen #pull-status {
        margin-bottom: 1;
    }

    PullProgressScreen ProgressBar {
        margin-bottom: 1;
    }

    PullProgressScreen #cancel-btn {
        width: 100%;
    }
    """

    def __init__(self, model_name: str) -> None:
        super().__init__()
        self.model_name = model_name
        self._cancelled = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Pulling: {self.model_name}", id="pull-title")
            yield ProgressBar(total=100, show_eta=False, id="pull-progress")
            yield Static("Starting...", id="pull-status")
            yield Button("Cancel", variant="error", id="cancel-btn")

    def on_mount(self) -> None:
        self._do_pull()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self._cancelled = True
            self.dismiss(False)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self._cancelled = True
            self.dismiss(False)

    @work(exclusive=True)
    async def _do_pull(self) -> None:
        status = self.query_one("#pull-status", Static)
        progress = self.query_one("#pull-progress", ProgressBar)

        client = OllamaClient()
        last_line = ""

        async for line in client.pull_model(self.model_name):
            if self._cancelled:
                return

            if line:
                last_line = line
                status.update(line)

                # Try to parse percentage from line
                if "%" in line:
                    try:
                        # Extract percentage like "pulling abc123... 45%"
                        parts = line.split("%")[0].split()
                        for part in reversed(parts):
                            if part.replace(".", "").isdigit():
                                pct = float(part)
                                progress.update(progress=pct)
                                break
                    except (ValueError, IndexError):
                        pass

        if self._cancelled:
            return

        if "error" in last_line.lower():
            status.update(f"Error: {last_line}")
            self.notify(f"Pull failed: {last_line}", severity="error")
            # Keep dialog open on error so user can see
        else:
            progress.update(progress=100)
            status.update("Completed!")
            self.dismiss(True)
