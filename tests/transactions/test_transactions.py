import re
import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage


@pytest.mark.regression
def test_accounts_transactions_search_and_filters(authenticated_page):
    page = ModulePage(
        authenticated_page,
        "/accounts/transactions",
        "Poshn - Transactions",
        breadcrumbs=["Accounts", "Transactions"],
    )
    page.open_and_assert()

    # Strictly verify URL and document title confirm Transactions page
    expect(authenticated_page).to_have_url(re.compile(r".*/accounts/transactions/?$"))
    expect(authenticated_page).to_have_title("Poshn - Transactions")
    expect(authenticated_page.locator("main").get_by_text("Transactions", exact=True).first).to_be_visible()

    # Verify column headers
    for header in ["Type", "Amount", "Status"]:
        expect(
            authenticated_page.get_by_role("columnheader", name=re.compile(re.escape(header), re.IGNORECASE)).first
        ).to_be_visible()

    page.search_if_available()
    expect(authenticated_page.locator("main")).to_be_visible()


@pytest.mark.regression
def test_customer_and_vendor_payment_pages_are_available(authenticated_page):
    pages_to_test = [
        ("/cashflow-manager/customer-payments", "Poshn - Customer Payments", ["Cashflow Manager", "Customer Payments"]),
        ("/cashflow-manager/vendor-payments", "Poshn - Vendor Payments", ["Cashflow Manager", "Vendor Payments"]),
    ]
    for path, title, breadcrumbs in pages_to_test:
        page = ModulePage(authenticated_page, path, title, breadcrumbs=breadcrumbs)
        page.open_and_assert()
        expect(authenticated_page).to_have_url(re.compile(re.escape(path) + r"/?$"))
        expect(authenticated_page).to_have_title(title)
        for token in breadcrumbs:
            expect(authenticated_page.locator("main").get_by_text(token, exact=False).first).to_be_visible()

