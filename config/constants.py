"""Centralized constants and paths for Poshn QA Automation."""

from pathlib import Path

# Project Roots & Directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
REPORTS_DIR = PROJECT_ROOT / "reports"
AUTH_DIR = PROJECT_ROOT / "auth"

# Standard Fixture Files
DEFAULT_FIXTURE_DOC = FIXTURES_DIR / "sample_document.pdf"
DEFAULT_AUTH_FILE = AUTH_DIR / ".auth.json"

# Core Application Routes
ROUTES = {
    "HOME": "/home",
    "CUSTOMERS": "/users#customers",
    "VENDORS": "/users#vendors",
    "PURCHASE_ORDERS": "/sales/purchase-orders",
    "INVOICES": "/sales/invoices",
    "SALES_CREDIT_NOTES": "/sales/credit-notes",
    "PURCHASE_DEBIT_NOTES": "/purchases/debit-notes",
    "PURCHASE_BILLS": "/purchases/purchase-bills",
    "INVOICE_REQUESTS": "/accounts/invoice-requests",
    "RECEIVABLES": "/accounts/receivables",
    "VENDOR_LEDGER": "/ledgers/vendor-ledger",
    "CUSTOMER_LEDGER": "/ledgers/customer-ledger",
    "PDF_TEMPLATES": "/utility/pdf-templates",
}
