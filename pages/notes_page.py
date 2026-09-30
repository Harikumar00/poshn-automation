import re
from playwright.sync_api import Locator, Page, expect

from pages.list_page import ListPage


class NotesPage(ListPage):
    """Page Object for Credit Note and Debit Note listing pages (Sales and Purchases)."""

    def __init__(self, page: Page, path: str, title: str):
        super().__init__(page)
        self.path = path
        self.expected_title = title

    def verify_page(self) -> None:
        expect(self.page).to_have_url(re.compile(re.escape(self.path) + r"/?$"))
        expect(self.page).to_have_title(self.expected_title)
        expect(self.page.locator("main")).to_be_visible()

    def search_note(self, note_or_ref_number: str) -> Locator:
        """Searches for a note by note number or reference (invoice/bill) number."""
        search_inp = self.page.locator("main input:visible").first
        search_inp.fill(note_or_ref_number)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(2000)
        return self.page.locator("tbody tr:visible").first

    def verify_note_listed(
        self,
        note_number: str,
        ref_number: str | None = None,
        party: str | None = None,
        expected_status: str = "Active",
    ) -> None:
        """Asserts that the note is listed with the expected reference and status."""
        self.open(self.path)
        self.verify_page()
        row = self.search_note(note_number)
        expect(row).to_be_visible(timeout=15000)
        expect(row).to_contain_text(note_number)

        if ref_number:
            expect(row).to_contain_text(ref_number)

        if party:
            short_party = party.split()[0]
            expect(row).to_contain_text(re.compile(re.escape(short_party), re.IGNORECASE))

        if expected_status:
            expect(row).to_contain_text(expected_status)
