import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage


@pytest.mark.regression
def test_accounts_transactions_search_and_filters(authenticated_page):
    page = ModulePage(authenticated_page, "/accounts/transactions", "Poshn - Transactions")
    page.open_and_assert(); page.search_if_available()
    expect(authenticated_page.locator("main")).to_be_visible()


@pytest.mark.regression
def test_customer_and_vendor_payment_pages_are_available(authenticated_page):
    for path, title in [("/cashflow-manager/customer-payments", "Poshn - Customer Payments"), ("/cashflow-manager/vendor-payments", "Poshn - Vendor Payments")]:
        page = ModulePage(authenticated_page, path, title); page.open_and_assert()

