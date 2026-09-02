import re
from playwright.sync_api import expect

from pages.list_page import ListPage


class PurchaseOrdersPage(ListPage):
    path = "/sales/purchase-orders"
    expected_title = "Poshn - Purchase Orders"

    def verify_page(self) -> None:
        expect(self.page).to_have_url(re.compile(r".*/sales/purchase-orders/?$"))
        expect(self.page).to_have_title(self.expected_title)
        expect(self.page.locator("main").get_by_text("Purchase Orders", exact=False).first).to_be_visible()
        expect(self.page.get_by_role("button", name="Create PO")).to_be_visible()
        expect(self.page.get_by_role("columnheader", name="Status")).to_be_visible()

    def open_create_form(self) -> None:
        self.page.get_by_role("button", name="Create PO").click()
        expect(self.page.get_by_text("Create Purchase Order", exact=True)).to_be_visible()

    def required_form_labels(self) -> list[str]:
        return [
            "Select Customer *", "Delivery Type *", "Payment Terms *",
            "Issue Date *", "Expect. Delivery Date *", "Bill To *",
            "Ship To *", "Account Owner *",
        ]
