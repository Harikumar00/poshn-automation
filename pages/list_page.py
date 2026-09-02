from playwright.sync_api import expect

from pages.base_page import BasePage


class ListPage(BasePage):
    def assert_loaded(self, title: str) -> None:
        expect(self.page).to_have_title(title)
        expect(self.page.locator("main")).to_be_visible()

    def search(self, value: str) -> None:
        field = self.page.locator("main input:visible").nth(1)
        field.fill(value)
        self.page.keyboard.press("Enter")

    def clear_search(self) -> None:
        field = self.page.locator("main input:visible").nth(1)
        field.fill("")
        self.page.keyboard.press("Enter")
