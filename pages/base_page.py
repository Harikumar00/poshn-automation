from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def open(self, path: str) -> None:
        self.page.goto(path, wait_until="domcontentloaded")

    def heading_text(self) -> str:
        heading = self.page.locator("h1:visible, h2:visible, h3:visible").first
        return heading.inner_text().strip() if heading.count() else ""
