"""Vendor Ledger Page Object."""

from playwright.sync_api import Page

from config.settings import settings
from pages.base_ledger_page import BaseLedgerPage


class VendorLedgerPage(BaseLedgerPage):
    """Page Object for Vendor Statement of Accounts (/ledgers/vendor-ledger)."""

    path: str = "/ledgers/vendor-ledger"
    expected_title: str = "Poshn - Ledger"
    party_label_text: str = "Vendor *"
    generate_btn_name: str = "Generate Vendor Ledger"

    def __init__(self, page: Page, base_url: str | None = None):
        super().__init__(page, base_url=base_url)
        self.vendor_input = self.page.locator("input[placeholder='Select Vendor']")
        self.party_input = self.vendor_input

    def select_vendor(self, vendor_name: str | None = None) -> str:
        """Selects a vendor from the vendor dropdown."""
        return self.select_party(vendor_name or settings.test_vendor)
