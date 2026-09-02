from playwright.sync_api import Page, expect


class Navigation:
    def __init__(self, page: Page):
        self.page = page

    def open(self, label: str, href: str) -> None:
        link = self.page.locator(f'a[href="{href}"]').first
        expect(link).to_be_visible()
        link.click()

    def visible_labels(self) -> list[str]:
        return [x.strip() for x in self.page.locator("aside a, aside button").all_inner_texts() if x.strip()]

