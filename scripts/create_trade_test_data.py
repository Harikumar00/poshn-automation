#!/usr/bin/env python3
"""
Create Test Data on engg-2406 branch:
1. Create Purchase Order (PO)
2. Add Purchase Bill (PB)
3. Request Invoice (Invoice Request) - WITHOUT approving it!
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pages.login_page import LoginPage
from pages.purchase_orders_page import PurchaseOrdersPage
from pages.accounts_invoice_requests_page import AccountsInvoiceRequestsPage

BASE_URL = os.getenv("NUCLEUS_BASE_URL", "https://engg-2406.nucleus.te.poshn.app")
AUTH_FILE = ROOT / "auth" / ".auth_engg_2406.json"
FIXTURE_PDF = ROOT / "tests" / "fixtures" / "sample_document.pdf"

ts = int(time.time())
trade_data = {
    "customer": "Merabo Labs Private Limited",
    "customer_search": "06AAMCM0523D1ZW",
    "vendor": "Payables Vendor",
    "vendor_search": "07AAUFG7095F1ZT",
    "product": "Aashirvaad atta 10kg*3",
    "po_number": f"PO-2406-{ts}",
    "pb_number": f"PB-2406-{ts}",
    "po_rate": "250",
    "pb_rate": "200",
    "quantity": "10",
    "vehicle_number": "MH12AB1234",
}

print(f"[{time.strftime('%H:%M:%S')}] Starting test data creation on {BASE_URL}...")
print(f"  PO Number: {trade_data['po_number']}")
print(f"  PB Number: {trade_data['pb_number']}")
print(f"  Customer: {trade_data['customer']} ({trade_data['customer_search']})")
print(f"  Vendor: {trade_data['vendor']} ({trade_data['vendor_search']})")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(base_url=BASE_URL)
    page = context.new_page()

    # Step 0: Authenticate
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 0: Authenticating...")
    page.goto(f"{BASE_URL}/login")
    page.wait_for_timeout(2000)
    login_page = LoginPage(page)
    login_page.authenticate("8596896586", "9999")
    page.wait_for_timeout(2000)
    context.storage_state(path=str(AUTH_FILE))
    print(f"  Logged in successfully as tester. Current URL: {page.url}")

    # Step 1: Create Purchase Order
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 1: Creating Purchase Order {trade_data['po_number']}...")
    po_page = PurchaseOrdersPage(page)
    po_page.open(po_page.path)
    po_page.verify_page()

    created_po = po_page.create_purchase_order(
        customer=trade_data["customer"],
        product=trade_data["product"],
        rate=trade_data["po_rate"],
        quantity=trade_data["quantity"],
        po_number=trade_data["po_number"],
        customer_search=trade_data["customer_search"],
        file_path=FIXTURE_PDF,
    )
    print(f"  PO created: {created_po['po_number']}")
    page.wait_for_timeout(2000)

    # Step 2: Open PO Details
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 2: Opening PO Details for {trade_data['po_number']}...")
    po_page.open_po_details(trade_data["po_number"])
    po_detail_url = page.url
    print(f"  PO Detail URL: {po_detail_url}")

    # Step 3: Record Entry -> Add Purchase Bill
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 3: Recording Purchase Bill {trade_data['pb_number']}...")
    created_pb = po_page.record_entry_add_purchase_bill(
        vendor=trade_data["vendor"],
        rate=trade_data["pb_rate"],
        quantity=trade_data["quantity"],
        pb_number=trade_data["pb_number"],
        vehicle_number=trade_data["vehicle_number"],
        vendor_search=trade_data["vendor_search"],
    )
    print(f"  Purchase Bill recorded: {created_pb['pb_number']}")
    page.wait_for_timeout(2000)

    # Step 4: Request Invoice (DO NOT APPROVE!)
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 4: Requesting Invoice (Pending Approval)...")
    po_page.request_invoice()
    page.wait_for_timeout(3000)
    print("  Invoice requested successfully!")

    # Step 5: Verify Invoice Request in Accounts -> Invoice Requests
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 5: Verifying under Accounts -> Invoice Requests...")
    accounts_page = AccountsInvoiceRequestsPage(page)
    accounts_page.open(accounts_page.path)
    accounts_page.verify_page()
    accounts_page.search(trade_data["po_number"])
    page.wait_for_timeout(2000)

    row = page.locator("tbody tr:visible").first
    expect(row).to_be_visible(timeout=15000)
    row_text = row.inner_text().replace("\n", " | ")
    print(f"  Invoice Request found in Accounts: {row_text}")

    invoice_requests_url = f"{BASE_URL}/accounts/invoice-requests"

    browser.close()

print("\n" + "=" * 70)
print("🎉 ALL TEST DATA CREATED SUCCESSFULLY ON BRANCH 2406!")
print(f"• Purchase Order: {trade_data['po_number']}")
print(f"  URL: {po_detail_url}")
print(f"• Purchase Bill:  {trade_data['pb_number']}")
print(f"• Customer:       {trade_data['customer']}")
print(f"• Vendor:         {trade_data['vendor']}")
print(f"• Invoice Status: PENDING APPROVAL (Not Approved - ready for manual action)")
print(f"  Approval Page:  {invoice_requests_url}")
print("=" * 70)

# Alert user
os.system('afplay /System/Library/Sounds/Ping.aiff && say "Test data created successfully on branch 2406. PO, Bill, and Invoice Request are ready for your manual approval."')
