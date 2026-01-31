#!/usr/bin/env python3
"""
Automated screenshot generator for ollama-cli-tui documentation.

Uses Textual's pilot mode to navigate through the app and capture screenshots.
Run this script after UI changes to update documentation images.

Usage:
    python scripts/take_screenshots.py

Output:
    screenshots/*.svg - Vector screenshots
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ollama_tui.app import OllamaTUI
from ollama_tui.widgets import PSView, SearchView
from ollama_tui.ollama_client import RemoteModel


SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"

# Demo data for search results
DEMO_REMOTE_MODELS = [
    RemoteModel("llama3.2:latest", "2.0 GB", "2025-01-15"),
    RemoteModel("llama3.1:8b", "4.7 GB", "2025-01-10"),
    RemoteModel("llama3.1:70b", "40 GB", "2025-01-10"),
    RemoteModel("llama2:latest", "3.8 GB", "2024-12-01"),
    RemoteModel("codellama:latest", "3.8 GB", "2024-11-15"),
    RemoteModel("mistral:latest", "4.1 GB", "2025-01-12"),
    RemoteModel("mixtral:8x7b", "26 GB", "2025-01-08"),
    RemoteModel("qwen2.5:7b", "4.7 GB", "2025-01-20"),
    RemoteModel("qwen2.5:14b", "9.0 GB", "2025-01-20"),
    RemoteModel("gemma2:2b", "1.6 GB", "2025-01-18"),
    RemoteModel("gemma2:9b", "5.4 GB", "2025-01-18"),
    RemoteModel("phi3:latest", "2.2 GB", "2025-01-05"),
    RemoteModel("deepseek-r1:latest", "4.7 GB", "2025-01-25"),
]


async def take_screenshots():
    """Navigate through the app and take screenshots of each screen."""

    SCREENSHOTS_DIR.mkdir(exist_ok=True)

    app = OllamaTUI()

    async with app.run_test(size=(100, 28)) as pilot:
        # Wait for app to load and models to be fetched
        await asyncio.sleep(1)

        # Screenshot 1: Models tab
        app.save_screenshot(str(SCREENSHOTS_DIR / "01_models.svg"))
        print("✓ 01_models.svg")

        # Switch to Running tab
        await pilot.press("2")
        await asyncio.sleep(0.5)

        # Inject demo data for Running tab (real data may be empty)
        ps_view = app.query_one(PSView)
        ps_table = ps_view.query_one("#ps-table")
        ps_table.clear()
        ps_table.add_row("llama3.2:latest", "a1b2c3d4e5f6", "2.0 GB", "100% GPU", "4096", "4 minutes from now")
        ps_table.add_row("qwen2.5:7b", "845dbda0ea48", "4.7 GB", "100% GPU", "8192", "3 minutes from now")
        if ps_table.row_count > 0:
            ps_table.move_cursor(row=0)
        ps_view.query_one("#ps-status").update("2 running")
        await asyncio.sleep(0.2)

        # Screenshot 2: Running tab
        app.save_screenshot(str(SCREENSHOTS_DIR / "02_running.svg"))
        print("✓ 02_running.svg")

        # Switch to Search tab
        await pilot.press("3")
        await asyncio.sleep(0.5)

        # Inject demo data for Search tab (network may be slow/unavailable)
        search_view = app.query_one(SearchView)
        search_view._all_models = DEMO_REMOTE_MODELS
        search_view._update_table("")
        search_table = search_view.query_one("#search-table")
        search_table.focus()
        await asyncio.sleep(0.2)

        # Screenshot 3: Search tab
        app.save_screenshot(str(SCREENSHOTS_DIR / "03_search.svg"))
        print("✓ 03_search.svg")

        # Type in search filter
        await pilot.press("/")
        for char in "llama":
            await pilot.press(char)
        await asyncio.sleep(0.3)

        # Back to table for screenshot
        await pilot.press("escape")
        await asyncio.sleep(0.2)

        # Screenshot 4: Search with filter
        app.save_screenshot(str(SCREENSHOTS_DIR / "04_search_filter.svg"))
        print("✓ 04_search_filter.svg")

        # Press p to show pull confirmation dialog
        await pilot.press("p")
        await asyncio.sleep(0.3)

        # Screenshot 5: Pull confirmation dialog
        app.save_screenshot(str(SCREENSHOTS_DIR / "05_pull_confirm.svg"))
        print("✓ 05_pull_confirm.svg")

        print(f"\nScreenshots saved to: {SCREENSHOTS_DIR}")


def main():
    """Entry point."""
    print("Generating screenshots for ollama-cli-tui...\n")
    asyncio.run(take_screenshots())
    print("\nDone!")


if __name__ == "__main__":
    main()
