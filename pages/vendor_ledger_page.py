from __future__ import annotations

import re
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.base_page import BasePage


class VendorLedgerPage(BasePage):
    path = "/ledgers/vendor-ledger"
    expected_title = "Poshn - Ledger"

    EXPECTED_COLUMNS = [
        "Date",
        "Voucher Type",
        "Debit",
        "Credit",
        "Balance",
        "Voucher#",
        "Details",
        "State",
    ]

    EXPECTED_ACTION_MENU_ITEMS = [
        "Export as PDF",
        "Export as XLS",
        "Past Generated Ledger",
        "Display Additional Columns",
        "Activity Logs",
    ]

    def __init__(self, page: Page, base_url: str | None = None):
        super().__init__(page)
        self.base_url = (base_url or settings.base_url).rstrip("/")
        self.generate_button = page.get_by_role("button", name="Generate Vendor Ledger")
        self.reset_button = page.get_by_role("button", name="Reset")
        self.more_filters_button = page.locator("button:has-text('More Filters')")
        self.vendor_input = page.locator("input[placeholder='Select Vendor']")
        self.duration_input = page.locator("input[placeholder='Select duration']")

    def navigate(self) -> None:
        self.page.goto(f"{self.base_url}{self.path}", wait_until="networkidle")

    def assert_initial_state(self) -> None:
        expect(self.page).to_have_title(self.expected_title)
        expect(self.page.get_by_text("No Ledger Found", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Party Type *", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Vendor *", exact=True)).to_be_visible()
        expect(self.page.get_by_text("State *", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Duration *", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Date Range *", exact=True)).to_be_visible()
        expect(self.generate_button).to_be_disabled()
        expect(self.more_filters_button).to_be_disabled()

    def select_vendor(self, vendor_name: str | None = None) -> str:
        self.vendor_input.click()
        self.page.wait_for_timeout(1000)
        options = self.page.locator(".q-menu .q-item, [role='option']")
        expect(options.first).to_be_visible()

        if vendor_name:
            target = self.page.locator(f".q-menu .q-item:has-text('{vendor_name}')").first
            selected_text = target.inner_text().strip().split("\n")[0]
            target.click()
        else:
            selected_text = options.first.inner_text().strip().split("\n")[0]
            options.first.click()

        self.page.wait_for_timeout(500)
        return selected_text

    def select_duration(self, duration_label: str = "Financial Year") -> None:
        self.duration_input.click()
        self.page.wait_for_timeout(1000)
        opt = self.page.locator(f".q-menu .q-item:has-text('{duration_label}')").first
        expect(opt).to_be_visible()
        opt.click()
        self.page.wait_for_timeout(500)

    def generate_ledger(self) -> None:
        expect(self.generate_button).to_be_enabled()
        self.generate_button.click()
        # Wait for the table to render
        expect(self.page.locator("table, .q-table").first).to_be_visible(timeout=15000)

    def assert_table_columns(self) -> None:
        for column in self.EXPECTED_COLUMNS:
            expect(
                self.page.locator("th, [role='columnheader']").filter(has_text=column).first
            ).to_be_visible()

    def assert_balance_due_summary(self) -> None:
        expect(self.page.get_by_text("Balance Due", exact=True)).to_be_visible()

    def expand_more_filters(self) -> None:
        expect(self.more_filters_button).to_be_enabled()
        self.more_filters_button.click()
        self.page.wait_for_timeout(1000)
        expect(self.page.get_by_text("Location", exact=True)).to_be_visible()

    def open_action_menu(self) -> list[str]:
        # Top-right 3-dots action menu
        action_button = self.page.locator("main .q-btn--rounded.text-primary").first
        expect(action_button).to_be_visible()
        action_button.click()
        self.page.wait_for_timeout(1000)

        menu_container = self.page.locator(".q-menu")
        expect(menu_container).to_be_visible()

        for item in self.EXPECTED_ACTION_MENU_ITEMS:
            expect(menu_container.get_by_text(item, exact=True).first).to_be_visible()

        return self.EXPECTED_ACTION_MENU_ITEMS
