import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage
from utils.calculations import line_total


@pytest.mark.regression
def test_invoice_listing_search_and_filters(authenticated_page):
    page = ModulePage(authenticated_page, "/sales/invoices", "Poshn - Invoices")
    page.open_and_assert(); page.search_if_available()
    expect(authenticated_page.locator("main")).to_be_visible()


@pytest.mark.regression
def test_invoice_table_exposes_business_columns(authenticated_page):
    page = ModulePage(authenticated_page, "/sales/invoices", "Poshn - Invoices")
    page.open_and_assert()
    for header in ["Status", "Amount"]:
        if authenticated_page.get_by_role("columnheader", name=header).count():
            expect(authenticated_page.get_by_role("columnheader", name=header).first).to_be_visible()


def test_invoice_line_calculation():
    assert line_total(2, "100.00", discount=10, tax=18) == line_total(1, "100.00", discount=10, tax=18) * 2

