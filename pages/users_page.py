import re
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class UsersPage(BasePage):
    def __init__(self, page: Page, kind: str = "customers"):
        super().__init__(page)
        self.kind = kind

    def open_list(self):
        self.open(f"/users#{self.kind}")

    def verify_page(self):
        expect(self.page).to_have_url(re.compile(r".*/users/?#" + self.kind + r"$"))
        expect(self.page).to_have_title("Poshn - Users")
        expect(self.page.locator("main").get_by_text("Customers" if self.kind == "customers" else "Vendors", exact=True)).to_be_visible()
        self.assert_list_loaded()

    def assert_list_loaded(self):
        expect(self.page).to_have_title("Poshn - Users")
        expect(self.page.locator('input[placeholder="Search by name, trade name, phone or email"]:visible')).to_be_visible()
        expect(self.page.get_by_role("button", name=f"Add {'Customer' if self.kind == 'customers' else 'Vendor'}")).to_be_visible()
        expect(self.page.get_by_role("columnheader", name="Status")).to_be_visible()

    def search(self, value: str):
        box = self.page.locator('input[placeholder="Search by name, trade name, phone or email"]:visible')
        box.fill(value)
        box.press("Enter")

    def open_add(self):
        self.page.get_by_role("button", name=f"Add {'Customer' if self.kind == 'customers' else 'Vendor'}").click()

    def assert_add_form(self):
        expect(self.page.get_by_text("BASIC INFO", exact=True)).to_be_visible()
        for label in ["Contact Name *", "Contact No. *", "Business Channel *", "Distribution Type *"]:
            expect(self.page.get_by_text(label, exact=True)).to_be_visible()
        expect(self.page.get_by_role("button", name="Save & Next")).to_be_visible()
