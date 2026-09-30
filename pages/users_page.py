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

    @property
    def add_drawer(self):
        return self.page.get_by_role("complementary").filter(has_text=f"Add {'Customer' if self.kind == 'customers' else 'Vendor'}")

    @property
    def details_drawer(self):
        return self.page.get_by_role("complementary").filter(has_text=f"{'Customer' if self.kind == 'customers' else 'Vendor'} Details")

    def fill_basic_info(
        self,
        name: str,
        phone: str,
        email: str,
        channel: str = "General Trade",
        distribution_type: str = "Wholesaler",
    ) -> None:
        drawer = self.add_drawer
        name_input = drawer.locator("input[placeholder='Enter contact name']")
        expect(name_input).to_be_visible()
        name_input.click()
        name_input.fill(name)

        phone_input = drawer.locator("input[placeholder='Enter 10 digit phone number']")
        expect(phone_input).to_be_visible()
        phone_input.click()
        phone_input.fill(phone)

        email_input = drawer.locator("input[placeholder='Enter email']")
        expect(email_input).to_be_visible()
        email_input.click()
        email_input.fill(email)

        # Select distribution type radio/button
        dist_btn = drawer.get_by_text(distribution_type, exact=True)
        expect(dist_btn).to_be_visible()
        dist_btn.click()
        self.page.wait_for_timeout(300)

        # Select business channel dropdown
        channel_input = drawer.locator("input[placeholder='Select business channel']")
        expect(channel_input).to_be_visible()
        channel_input.click()
        self.page.wait_for_timeout(500)
        options = self.page.locator(".q-menu .q-item")
        matched = options.filter(has_text=channel)
        if matched.count() > 0:
            matched.first.click()
        else:
            options.first.click()
        self.page.wait_for_timeout(400)

    def save_and_next(self) -> None:
        btn = self.add_drawer.get_by_role("button", name="Save & Next")
        expect(btn).to_be_visible(timeout=10000)
        btn.click(force=True)
        self.page.wait_for_timeout(1000)

    def assert_stepper_step(self, step_name: str) -> None:
        expect(self.add_drawer.get_by_text(step_name, exact=False).first).to_be_visible()

    def close_drawer(self) -> None:
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

    def switch_tab(self, tab_name: str) -> None:
        tab = self.page.locator("[role='tab']").filter(has_text=tab_name).first
        expect(tab).to_be_visible()
        tab.click()
        self.page.wait_for_timeout(1000)

    def open_record_details(self, search_term: str):
        self.search(search_term)
        self.page.wait_for_timeout(1500)
        row = self.page.locator("tbody tr:visible").filter(has_text=search_term).first
        expect(row).to_be_visible(timeout=15000)
        row.locator("td").last.locator("button, a, .q-btn").first.click()
        expect(self.details_drawer).to_be_visible(timeout=15000)
        return row

    def assert_details_profile(self, name: str, phone: str, email: str) -> None:
        drawer = self.details_drawer
        expect(drawer.get_by_text(name, exact=False).first).to_be_visible()
        expect(drawer.get_by_text(phone, exact=False).first).to_be_visible()
        expect(drawer.get_by_text(email, exact=False).first).to_be_visible()

    def open_approve_modal(self) -> None:
        btn = self.details_drawer.get_by_role("button", name="Approve")
        expect(btn).to_be_visible()
        btn.click()
        expect(self.page.locator(".q-dialog:visible")).to_be_visible()

    def assert_approve_modal(self) -> None:
        dialog = self.page.locator(".q-dialog:visible")
        expect(dialog.get_by_text("Approve", exact=True).first).to_be_visible()
        expect(dialog.get_by_text("Remarks *", exact=True)).to_be_visible()
        expect(dialog.get_by_text("Note: This action is irreversible. Please take caution.", exact=True)).to_be_visible()
        expect(dialog.get_by_role("button", name="Approve")).to_be_visible()

    def submit_approve(self, remarks: str = "Approved via QA automation") -> None:
        dialog = self.page.locator(".q-dialog:visible")
        remarks_field = dialog.locator("input, textarea").first
        remarks_field.fill(remarks)
        dialog.get_by_role("button", name="Approve").click()

    def open_reject_modal(self) -> None:
        btn = self.details_drawer.get_by_role("button", name="Reject")
        expect(btn).to_be_visible()
        btn.click()
        expect(self.page.locator(".q-dialog:visible")).to_be_visible()

    def assert_reject_modal(self) -> None:
        dialog = self.page.locator(".q-dialog:visible")
        expect(dialog.get_by_text("Reject", exact=True).first).to_be_visible()
        expect(dialog.get_by_text("Rejection reason *", exact=True)).to_be_visible()
        expect(dialog.get_by_text("Note: This action is irreversible. Please take caution.", exact=True)).to_be_visible()
        expect(dialog.get_by_role("button", name="Reject")).to_be_visible()

    def close_dialog(self) -> None:
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)
