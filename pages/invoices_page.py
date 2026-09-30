import re
from playwright.sync_api import Locator, Page, expect

from pages.list_page import ListPage


class InvoicesPage(ListPage):
    path = "/sales/invoices"
    expected_title = "Poshn - Invoices"

    def verify_page(self) -> None:
        expect(self.page).to_have_url(re.compile(r".*/sales/invoices/?$"))
        expect(self.page).to_have_title(self.expected_title)
        expect(self.page.locator("main").get_by_text("Invoices", exact=False).first).to_be_visible()

    def search_invoice(self, invoice_number: str) -> Locator:
        """Searches for an invoice in the Sales Invoices list and returns the first row."""
        search_inp = self.page.locator("input[placeholder*='Search']").first
        search_inp.fill(invoice_number)
        self.page.wait_for_timeout(2000)
        return self.page.locator("tbody tr:visible").first

    def verify_invoice_listed(
        self,
        invoice_number: str,
        customer: str | None = None,
        expected_stage: str = "POD Pending",
    ) -> None:
        """Asserts that the invoice is listed with expected customer and stage."""
        self.open(self.path)
        self.verify_page()
        row = self.search_invoice(invoice_number)
        expect(row).to_be_visible(timeout=15000)
        expect(row).to_contain_text(invoice_number)

        if customer:
            short_cust = customer.split()[0]
            expect(row).to_contain_text(re.compile(re.escape(short_cust), re.IGNORECASE))

        if expected_stage:
            expect(row).to_contain_text(expected_stage)
