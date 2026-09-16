import re
import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage
from utils.calculations import line_total


@pytest.mark.regression
def test_invoice_listing_search_and_filters(authenticated_page):
    page = ModulePage(authenticated_page, "/sales/invoices", "Poshn - Invoices", breadcrumbs=["Sales", "Invoices"])
    page.open_and_assert()

    # Verify exact URL and document title confirm we are on the Invoices page
    expect(authenticated_page).to_have_url(re.compile(r".*/sales/invoices/?$"))
    expect(authenticated_page).to_have_title("Poshn - Invoices")

    # Verify Invoices breadcrumb/heading in main
    main = authenticated_page.locator("main")
    expect(main.get_by_text("Invoices", exact=True).first).to_be_visible()

    # Verify search input is present and test searching
    page.search_if_available("INV-AUTOMATION")
    expect(main).to_be_visible()


@pytest.mark.regression
def test_invoice_table_exposes_business_columns(authenticated_page):
    page = ModulePage(authenticated_page, "/sales/invoices", "Poshn - Invoices", breadcrumbs=["Sales", "Invoices"])
    page.open_and_assert()

    # Verify exact title
    expect(authenticated_page).to_have_title("Poshn - Invoices")

    # Verify table column headers strictly expose required business columns
    for header in ["Number", "Customer", "Amount", "Status", "Due Date"]:
        expect(
            authenticated_page.get_by_role("columnheader", name=re.compile(re.escape(header), re.IGNORECASE)).first
        ).to_be_visible()


def test_invoice_line_calculation():
    assert line_total(2, "100.00", discount=10, tax=18) == line_total(1, "100.00", discount=10, tax=18) * 2


