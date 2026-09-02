import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage


@pytest.mark.regression
@pytest.mark.parametrize("path,title", [
    ("/sales/credit-notes", "Poshn - Credit Notes"),
    ("/sales/debit-notes", "Poshn - Debit Notes"),
    ("/purchases/credit-notes", "Poshn - Credit Notes"),
    ("/purchases/debit-notes", "Poshn - Debit Notes"),
])
def test_note_listing_search_and_filters(authenticated_page, path, title):
    page = ModulePage(authenticated_page, path, title); page.open_and_assert(); page.search_if_available()
    expect(authenticated_page.locator("main")).to_be_visible()

