import re
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class ModulePage(BasePage):
    def __init__(self, page: Page, path: str, title: str):
        super().__init__(page)
        self.path, self.expected_title = path, title

    def open_and_assert(self, identity: str | None = None):
        self.open(self.path)
        expect(self.page).to_have_url(re.compile(re.escape(self.path.split('#')[0]) + r"/?(?:#.*)?$"))
        expect(self.page).to_have_title(self.expected_title)
        expect(self.page.locator("main")).to_be_visible()
        if identity:
            expect(self.page.locator("main").get_by_text(identity, exact=False).first).to_be_visible()

    def search_if_available(self, value: str = "automation-probe"):
        boxes = self.page.locator("main input:visible")
        if boxes.count():
            boxes.first.fill(value)
            boxes.first.press("Enter")

    def assert_headers(self, headers):
        for header in headers:
            expect(self.page.get_by_role("columnheader", name=header)).to_be_visible()
