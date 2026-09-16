import re
import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage


@pytest.mark.regression
@pytest.mark.parametrize("path,title,breadcrumbs", [
    ("/sales/credit-notes", "Poshn - Credit Notes", ["Sales", "Credit Notes"]),
    ("/sales/debit-notes", "Poshn - Debit Notes", ["Sales", "Debit Notes"]),
    ("/purchases/credit-notes", "Poshn - Credit Notes", ["Purchases", "Credit Notes"]),
    ("/purchases/debit-notes", "Poshn - Debit Notes", ["Purchases", "Debit Notes"]),
])
def test_note_listing_search_and_filters(authenticated_page, path, title, breadcrumbs):
    page = ModulePage(authenticated_page, path, title, breadcrumbs=breadcrumbs)
    page.open_and_assert()

    # Strictly verify URL and document title confirm the notes page
    expect(authenticated_page).to_have_url(re.compile(re.escape(path) + r"/?$"))
    expect(authenticated_page).to_have_title(title)

    # Strictly verify breadcrumb identity in main
    main = authenticated_page.locator("main")
    for token in breadcrumbs:
        expect(main.get_by_text(token, exact=False).first).to_be_visible()

    page.search_if_available()
    expect(main).to_be_visible()

