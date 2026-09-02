import pytest
import re
from playwright.sync_api import expect

from config.settings import settings


MODULES = {
    "Home": "/home",
    "Users": "/users#customers",
    "Roles Management": "/roles-management",
    "Catalogue": "/catalogue#products",
    "RFQs": "/trade/rfqs",
    "Vendor Orders": "/trade/vendor-orders",
    "Purchase Orders": "/sales/purchase-orders",
    "Invoices": "/sales/invoices",
    "Proof of Deliveries": "/sales/proof-of-deliveries",
    "Sales Credit Notes": "/sales/credit-notes",
    "Sales Debit Notes": "/sales/debit-notes",
    "Purchase Bills": "/purchases/purchase-bills",
    "Purchase Credit Notes": "/purchases/credit-notes",
    "Purchase Debit Notes": "/purchases/debit-notes",
    "Payments": "/purchases/payments",
    "E-Way Bills": "/shipping/e-way-bills",
    "Invoice Requests": "/accounts/invoice-requests",
    "Payment Requests": "/accounts/payment-requests",
    "Receivables": "/accounts/receivables",
    "Transactions": "/accounts/transactions",
    "Reports": "/reports/sales",
    "Inbox": "/inbox",
    "Customer Payments": "/cashflow-manager/customer-payments",
    "Vendor Payments": "/cashflow-manager/vendor-payments",
    "File Manager": "/file-manager",
    "Audit Logs": "/utility/audit-logs",
    "Credit Score Check": "/utility/credit-score-check",
    "Ledger Requests": "/utility/ledger-requests",
    "Transaction Series": "/utility/transaction-series",
    "PDF Templates": "/utility/pdf-templates",
}

IDENTITIES = {
    "Home": "Create RFQ", "Users": "Customers", "Roles Management": "Roles Management",
    "Catalogue": "Products", "RFQs": "RFQs", "Vendor Orders": "Vendor Orders",
    "Purchase Orders": "Purchase Orders", "Invoices": "Invoices", "Proof of Deliveries": "Proof of Deliveries",
    "Sales Credit Notes": "Credit Notes", "Sales Debit Notes": "Debit Notes", "Purchase Bills": "Purchase Bills",
    "Purchase Credit Notes": "Credit Notes", "Purchase Debit Notes": "Debit Notes", "Payments": "Payments",
    "E-Way Bills": "E Way Bills", "Invoice Requests": "Invoice Requests", "Payment Requests": "Payment Requests",
    "Receivables": "Receivables", "Transactions": "Transactions", "Reports": "Reports", "Inbox": "Inbox",
    "Customer Payments": "Customer Payments", "Vendor Payments": "Vendor Payments", "File Manager": "File Manager",
    "Audit Logs": "Audit Logs", "Credit Score Check": "Credit Score", "Ledger Requests": "Ledger Requests",
    "Transaction Series": "Transaction Series", "PDF Templates": "PDF Templates",
}


@pytest.mark.smoke
def test_dashboard_loads(authenticated_page):
    authenticated_page.goto("/home", wait_until="domcontentloaded")
    expect(authenticated_page).to_have_url(re.compile(re.escape(settings.base_url) + r"/home/?$"))
    expect(authenticated_page).to_have_title("Poshn - Home")
    expect(authenticated_page.locator("main")).to_be_visible()
    expect(authenticated_page.get_by_role("button", name="Create RFQ")).to_be_visible()


@pytest.mark.smoke
@pytest.mark.parametrize("name,path", MODULES.items())
def test_major_module_route_loads(authenticated_page, name, path):
    authenticated_page.goto(path, wait_until="domcontentloaded")
    expect(authenticated_page).to_have_url(re.compile(re.escape(settings.base_url) + re.escape(path.split('#')[0]) + r"/?(?:#.*)?$"))
    if name == "Inbox":
        # Inbox updates its document title asynchronously; this assertion auto-waits
        # for the meaningful loaded state rather than accepting the transient title.
        expect(authenticated_page).to_have_title("Poshn - Inbox")
        main = authenticated_page.locator("main")
        expect(main.get_by_text("Inbox", exact=True).first).to_be_visible()
        expect(main.locator('input[placeholder="Search name, phone or message"]:visible')).to_be_visible()
        expect(main.get_by_text("All", exact=True).first).to_be_visible()
        expect(main.get_by_text(re.compile(r"^Unread(?: \(\d+\))?$"))).to_be_visible()
        expect(main.get_by_text("No Chat Selected", exact=True)).to_be_visible()
        return
    expect(authenticated_page).to_have_title(re.compile(r"^Poshn - .+"))
    expect(authenticated_page.locator("main")).to_be_visible()
    expect(authenticated_page.locator("main").get_by_text(IDENTITIES[name], exact=False).first).to_be_visible()
