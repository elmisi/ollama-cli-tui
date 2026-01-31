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

# Demo data for search results with parameters and pull counts
DEMO_REMOTE_MODELS = [
    RemoteModel("codellama", "7b, 13b, 34b, 70b", "5.2M"),
    RemoteModel("deepseek-coder", "1.3b, 6.7b, 33b", "8.1M"),
    RemoteModel("deepseek-r1", "1.5b, 7b, 8b, 14b, 32b, 70b, 671b", "42.3M"),
    RemoteModel("gemma", "2b, 7b", "6.8M"),
    RemoteModel("gemma2", "2b, 9b, 27b", "12.4M"),
    RemoteModel("llama2", "7b, 13b, 70b", "18.9M"),
    RemoteModel("llama3", "8b, 70b", "24.1M"),
    RemoteModel("llama3.1", "8b, 70b, 405b", "31.5M"),
    RemoteModel("llama3.2", "1b, 3b", "45.2M"),
    RemoteModel("llama3.3", "70b", "8.7M"),
    RemoteModel("mistral", "7b", "15.3M"),
    RemoteModel("mixtral", "8x7b, 8x22b", "9.6M"),
    RemoteModel("phi3", "3.8b, 14b", "7.2M"),
    RemoteModel("qwen", "0.5b, 1.8b, 4b, 7b, 14b, 72b", "4.1M"),
    RemoteModel("qwen2", "0.5b, 1.5b, 7b, 72b", "11.8M"),
    RemoteModel("qwen2.5", "0.5b, 1.5b, 3b, 7b, 14b, 32b, 72b", "22.6M"),
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
