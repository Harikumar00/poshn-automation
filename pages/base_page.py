"""Base Page Object Model adhering to enterprise automation standards."""

import re
from pathlib import Path
from typing import Pattern
from playwright.sync_api import Page, expect

from config.constants import REPORTS_DIR


class BasePage:
    """Core Page Object providing standard browser interactions, waits, and assertions."""

    def __init__(self, page: Page):
        self.page = page

    def open(self, path: str, wait_until: str = "domcontentloaded") -> None:
        """Navigates to the specified URL or path."""
        self.page.goto(path, wait_until=wait_until)

    def heading_text(self) -> str:
        """Extracts the first visible heading text."""
        heading = self.page.locator("h1:visible, h2:visible, h3:visible").first
        return heading.inner_text().strip() if heading.count() else ""

    def assert_url(self, expected: str | Pattern[str]) -> None:
        """Asserts that the current URL matches the expected string or pattern."""
        expect(self.page).to_have_url(expected if isinstance(expected, re.Pattern) else re.compile(re.escape(expected)))

    def assert_title(self, expected_title: str | Pattern[str]) -> None:
        """Asserts that the page title matches the expected title."""
        expect(self.page).to_have_title(expected_title)

    def press_escape(self) -> None:
        """Simulates an Escape keypress to dismiss overlays, drawers, or dialogs."""
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(400)

    def wait_for_idle(self, timeout: int = 10000) -> None:
        """Safely awaits network idle state with fallback."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass

    def wait_for_toast(self, text: str | Pattern[str] | None = None, timeout: int = 7000) -> None:
        """Awaits Quasar notification or toast alert."""
        toast = self.page.locator(".q-notification, .q-toast, [role='alert']").first
        if text:
            pattern = text if isinstance(text, re.Pattern) else re.compile(re.escape(text), re.I)
            expect(toast.filter(has_text=pattern)).to_be_visible(timeout=timeout)
        else:
            expect(toast).to_be_visible(timeout=timeout)

    def take_screenshot(self, name: str) -> Path:
        """Saves a debug screenshot to the reports directory."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = REPORTS_DIR / f"{name}.png"
        self.page.screenshot(path=str(file_path), full_page=True)
        return file_path
