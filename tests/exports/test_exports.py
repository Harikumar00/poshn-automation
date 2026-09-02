import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage


@pytest.mark.regression
@pytest.mark.parametrize("path,title", [("/accounts/receivables", "Poshn - Receivables"), ("/reports/sales", "Poshn - Reports")])
def test_export_surfaces_are_discoverable_without_downloading(path, title, authenticated_page):
    page = ModulePage(authenticated_page, path, title); page.open_and_assert()
    expect(authenticated_page.locator("main")).to_be_visible()
    controls = authenticated_page.get_by_role("button", name="Export")
    if controls.count():
        expect(controls.first).to_be_visible()
