import re
from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class ModulePage(BasePage):
    def __init__(self, page: Page, path: str, title: str, breadcrumbs: list[str] | None = None):
        super().__init__(page)
        self.path = path
        self.expected_title = title
        self.breadcrumbs = breadcrumbs or []

    def open_and_assert(self, identity: str | None = None):
        self.open(self.path)
        expect(self.page).to_have_url(
            re.compile(re.escape(self.path.split('#')[0]) + r"/?(?:#.*)?$"),
            timeout=15000,
        )
        expect(self.page).to_have_title(self.expected_title, timeout=15000)
        expect(self.page.locator("main")).to_be_visible()

        main = self.page.locator("main")
        for token in self.breadcrumbs:
            expect(main.get_by_text(token, exact=False).first).to_be_visible()
        if identity:
            expect(main.get_by_text(identity, exact=False).first).to_be_visible()

    def search_if_available(self, value: str = "automation-probe"):
        boxes = self.page.locator("main input:visible")
        if boxes.count():
            box = boxes.first
            expect(box).to_be_visible()
            box.fill(value)
            box.press("Enter")

    def assert_headers(self, headers: list[str]):
        main = self.page.locator("main")
        for header in headers:
            expect(
                main.get_by_role("columnheader", name=re.compile(re.escape(header), re.IGNORECASE)).first
            ).to_be_visible()
