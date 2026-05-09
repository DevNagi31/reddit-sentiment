"""Capture dashboard screenshots for the README.

Drives the running Streamlit dashboard via Playwright + the installed
Google Chrome (no chromium download). Captures each of the four tabs.

Usage (with the dashboard running on :8501):
    python scripts/capture_screenshots.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8501"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

TABS = [
    ("01-overview.png",       "Overview"),
    ("02-deep-dive.png",      "Company Deep-Dive"),
    ("03-themes.png",         "Themes"),
    ("04-posts-explorer.png", "Posts Explorer"),
]


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1100},
                                  device_scale_factor=2)
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60_000)
        page.wait_for_selector('div[data-baseweb="tab-list"]', timeout=30_000)
        # Allow charts/images (logos) a beat to render
        page.wait_for_timeout(2_500)

        for filename, tab_label in TABS:
            tab = page.locator(f'button[role="tab"]:has-text("{tab_label}")').first
            tab.click()
            # Wait for tab transition + chart redraw
            page.wait_for_timeout(2_000)

            # If it's the Deep-Dive, hover off the selectbox so it doesn't
            # cover content with its dropdown shadow
            page.mouse.move(0, 0)
            page.wait_for_timeout(500)

            target = OUT / filename
            page.screenshot(path=str(target), full_page=True)
            print(f"  saved {target.relative_to(OUT.parent.parent)}")

        browser.close()
    print("done.")


if __name__ == "__main__":
    main()
