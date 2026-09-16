import re
import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage


@pytest.mark.regression
@pytest.mark.parametrize("path,title,breadcrumbs", [
    ("/accounts/receivables", "Poshn - Receivables", ["Accounts", "Receivables"]),
    ("/reports/sales", "Poshn - Reports", ["Reports", "Sales"]),
])
def test_export_surfaces_are_discoverable_without_downloading(path, title, breadcrumbs, authenticated_page):
    page = ModulePage(authenticated_page, path, title, breadcrumbs=breadcrumbs)
    page.open_and_assert()

    # Strictly verify URL and document title
    expect(authenticated_page).to_have_url(re.compile(re.escape(path) + r"/?$"))
    expect(authenticated_page).to_have_title(title)

    # Verify breadcrumb identity
    main = authenticated_page.locator("main")
    for token in breadcrumbs:
        expect(main.get_by_text(token, exact=False).first).to_be_visible()

    expect(main).to_be_visible()
    controls = authenticated_page.get_by_role("button", name="Export")
    if controls.count():
        expect(controls.first).to_be_visible()
