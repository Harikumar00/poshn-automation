import pytest
from playwright.sync_api import expect

from pages.purchase_orders_page import PurchaseOrdersPage


@pytest.mark.smoke
def test_purchase_orders_listing_and_pagination(authenticated_page):
    page = PurchaseOrdersPage(authenticated_page)
    page.open("/sales/purchase-orders")
    # Strictly verify URL, title, breadcrumbs, and page elements
    page.verify_page()
    expect(page.page.get_by_role("button", name="Create PO")).to_be_visible()
    expect(page.page.get_by_role("columnheader", name="Status")).to_be_visible()
    expect(page.page.get_by_text("of", exact=False).last).to_be_visible()


@pytest.mark.regression
def test_purchase_orders_search_is_read_only(authenticated_page):
    page = PurchaseOrdersPage(authenticated_page)
    page.open("/sales/purchase-orders")
    page.verify_page()
    page.search("PO-POSHN")
    expect(page.page.locator("main")).to_be_visible()
    page.clear_search()


@pytest.mark.regression
def test_create_po_required_fields_are_exposed_without_submit(authenticated_page):
    page = PurchaseOrdersPage(authenticated_page)
    page.open("/sales/purchase-orders")
    page.verify_page()
    page.open_create_form()
    for label in page.required_form_labels():
        expect(page.page.get_by_text(label, exact=True)).to_be_visible()
    expect(page.page.get_by_role("button", name="Submit")).to_be_disabled()
    expect(page.page.get_by_text("At least one item is required.", exact=False)).to_be_visible()
