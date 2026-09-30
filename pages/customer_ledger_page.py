"""Customer Ledger Page Object."""

from playwright.sync_api import Page

from config.settings import settings
from pages.base_ledger_page import BaseLedgerPage


class CustomerLedgerPage(BaseLedgerPage):
    """Page Object for Customer Statement of Accounts (/ledgers/customer-ledger)."""

    path: str = "/ledgers/customer-ledger"
    expected_title: str = "Poshn - Ledger"
    party_label_text: str = "Party Type *"
    generate_btn_name: str = "Generate Customer Ledger"

    def __init__(self, page: Page, base_url: str | None = None):
        super().__init__(page, base_url=base_url)
        self.customer_input = self.page.locator("input[placeholder*='Select Customer' i]")
        self.party_input = self.customer_input

    def select_customer(self, customer_name: str | None = None) -> str:
        """Selects a customer from the customer dropdown."""
        return self.select_party(customer_name or settings.test_customer)
