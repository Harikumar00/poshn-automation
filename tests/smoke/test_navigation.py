import pytest
import re
from playwright.sync_api import expect

from config.settings import settings


MODULE_SPECS = {
    "Home": ("/home", "Poshn - Home", ["Create RFQ"]),
    "Users": ("/users#customers", "Poshn - Users", ["Users", "Customers"]),
    "Roles Management": ("/roles-management", "Poshn - Roles Management", ["Roles Management"]),
    "Catalogue": ("/catalogue#products", "Poshn - Catalogue", ["Catalogue", "Products"]),
    "RFQs": ("/trade/rfqs", "Poshn - Requests For Quotation (RFQs)", ["Trade", "Rfqs"]),
    "Vendor Orders": ("/trade/vendor-orders", "Poshn - Vendor Orders", ["Trade", "Vendor Orders"]),
    "Purchase Orders": ("/sales/purchase-orders", "Poshn - Purchase Orders", ["Sales", "Purchase Orders"]),
    "Invoices": ("/sales/invoices", "Poshn - Invoices", ["Sales", "Invoices"]),
    "Proof of Deliveries": ("/sales/proof-of-deliveries", "Poshn - Proof of Deliveries", ["Sales", "Proof Of Deliveries"]),
    "Sales Credit Notes": ("/sales/credit-notes", "Poshn - Credit Notes", ["Sales", "Credit Notes"]),
    "Sales Debit Notes": ("/sales/debit-notes", "Poshn - Debit Notes", ["Sales", "Debit Notes"]),
    "Purchase Bills": ("/purchases/purchase-bills", "Poshn - Purchase Bills", ["Purchases", "Purchase Bills"]),
    "Purchase Credit Notes": ("/purchases/credit-notes", "Poshn - Credit Notes", ["Purchases", "Credit Notes"]),
    "Purchase Debit Notes": ("/purchases/debit-notes", "Poshn - Debit Notes", ["Purchases", "Debit Notes"]),
    "Payments": ("/purchases/payments", "Poshn - Payments", ["Purchases", "Payments"]),
    "E-Way Bills": ("/shipping/e-way-bills", "Poshn - E-Way Bills", ["Shipping", "E Way Bills"]),
    "Invoice Requests": ("/accounts/invoice-requests", "Poshn - Invoice Requests", ["Accounts", "Invoice Requests"]),
    "Payment Requests": ("/accounts/payment-requests", "Poshn - Payment Requests", ["Accounts", "Payment Requests"]),
    "Receivables": ("/accounts/receivables", "Poshn - Receivables", ["Accounts", "Receivables"]),
    "Transactions": ("/accounts/transactions", "Poshn - Transactions", ["Accounts", "Transactions"]),
    "Reports": ("/reports/sales", "Poshn - Reports", ["Reports", "Sales"]),
    "Inbox": ("/inbox", "Poshn - Inbox", ["Inbox"]),
    "Customer Payments": ("/cashflow-manager/customer-payments", "Poshn - Customer Payments", ["Cashflow Manager", "Customer Payments"]),
    "Vendor Payments": ("/cashflow-manager/vendor-payments", "Poshn - Vendor Payments", ["Cashflow Manager", "Vendor Payments"]),
    "File Manager": ("/file-manager", "Poshn - File Manager", ["File Manager"]),
    "Audit Logs": ("/utility/audit-logs", "Poshn - Audit Logs", ["Utility", "Audit Logs"]),
    "Credit Score Check": ("/utility/credit-score-check", "Poshn - Credit Score Check", ["Utility", "Credit Score Check"]),
    "Ledger Requests": ("/utility/ledger-requests", "Poshn - Ledger Requests", ["Utility", "Ledger Requests"]),
    "Transaction Series": ("/utility/transaction-series", "Poshn - Transaction Series", ["Utility", "Transaction Series"]),
    "PDF Templates": ("/utility/pdf-templates", "Poshn - PDF Templates", ["Utility", "Pdf Templates"]),
}


@pytest.mark.smoke
def test_dashboard_loads(authenticated_page):
    authenticated_page.goto("/home", wait_until="domcontentloaded")
    expect(authenticated_page).to_have_url(re.compile(re.escape(settings.base_url) + r"/home/?$"), timeout=settings.timeout_ms)
    expect(authenticated_page).to_have_title("Poshn - Home", timeout=settings.timeout_ms)
    expect(authenticated_page.locator("main")).to_be_visible(timeout=settings.timeout_ms)
    expect(authenticated_page.get_by_role("button", name="Create RFQ")).to_be_visible(timeout=settings.timeout_ms)


@pytest.mark.smoke
@pytest.mark.parametrize(
    "name,path,expected_title,breadcrumbs",
    [(k, v[0], v[1], v[2]) for k, v in MODULE_SPECS.items()],
)
def test_major_module_route_loads(authenticated_page, name, path, expected_title, breadcrumbs):
    authenticated_page.goto(path, wait_until="domcontentloaded")
    # Verify exact URL path
    expect(authenticated_page).to_have_url(
        re.compile(re.escape(settings.base_url) + re.escape(path.split('#')[0]) + r"/?(?:#.*)?$"),
        timeout=settings.timeout_ms,
    )
    # Strictly verify the exact expected page title
    expect(authenticated_page).to_have_title(expected_title, timeout=settings.timeout_ms)
    expect(authenticated_page.locator("main")).to_be_visible(timeout=settings.timeout_ms)

    if name == "Inbox":
        main = authenticated_page.locator("main")
        expect(main.get_by_text("Inbox", exact=True).first).to_be_visible(timeout=settings.timeout_ms)
        expect(main.locator('input[placeholder="Search name, phone or message"]:visible')).to_be_visible(timeout=settings.timeout_ms)
        expect(main.get_by_text("All", exact=True).first).to_be_visible(timeout=settings.timeout_ms)
        expect(main.get_by_text(re.compile(r"^Unread(?: \(\d+\))?$"))).to_be_visible(timeout=settings.timeout_ms)
        expect(main.get_by_text("No Chat Selected", exact=True)).to_be_visible(timeout=settings.timeout_ms)
        return

    # Strictly verify page-identifying breadcrumb/heading in main
    main = authenticated_page.locator("main")
    for token in breadcrumbs:
        expect(main.get_by_text(token, exact=False).first).to_be_visible(timeout=settings.timeout_ms)
