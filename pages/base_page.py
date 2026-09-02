from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def open(self, path: str) -> None:
        self.page.goto(path, wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")

    def heading_text(self) -> str:
        heading = self.page.locator("h1, h2, h3").filter(visible=True).first
        return heading.inner_text().strip() if heading.count() else ""

