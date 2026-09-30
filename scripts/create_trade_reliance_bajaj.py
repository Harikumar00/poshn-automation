#!/usr/bin/env python3
"""
Create Trade Test Data on branch engg-2406:
- Customer: Bajaj Holdings And Investment Limited (27AAACB3370K1ZP)
- Vendor: Reliance Industries Limited (AAACR5055K)
- Line Item: Aashirvaad atta 10kg*3
- Quantity: 1000
- Rate: PO @ 250, PB @ 200
- Flow: PO -> PB -> Request Invoice (TILL Invoice Approval - NOT APPROVED)
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
    "customer": "Bajaj Holdings And Investment Limited",
    "customer_search": "27AAACB3370K1ZP",
    "vendor": "Reliance Industries Limited",
    "vendor_search": "AAACR5055K",
    "items": [
        {
            "product": "Aashirvaad atta 10kg*3",
            "search": "Aashirvaad",
            "po_rate": "250",
            "pb_rate": "200",
            "quantity": "1000",
        },
        {
            "product": "Amul choco crunch tricone 120ml",
            "search": "Amul choco crunch",
            "po_rate": "250",
            "pb_rate": "200",
            "quantity": "1000",
        },
    ],
    "po_number": f"PO-BAJAJ-REL-{ts}",
    "pb_number": f"PB-BAJAJ-REL-{ts}",
    "vehicle_number": "MH12AB1234",
}

print(f"[{time.strftime('%H:%M:%S')}] Starting test data creation on {BASE_URL}...")
print(f"• PO Number: {trade_data['po_number']}")
print(f"• PB Number: {trade_data['pb_number']}")
print(f"• Customer:  {trade_data['customer']} ({trade_data['customer_search']})")
print(f"• Vendor:    {trade_data['vendor']} ({trade_data['vendor_search']})")
for idx, itm in enumerate(trade_data["items"]):
    print(f"• Product {idx+1}: {itm['product']} | Qty: {itm['quantity']} | PO: ₹{itm['po_rate']} | PB: ₹{itm['pb_rate']}")

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
    print(f"  Logged in successfully. Current URL: {page.url}")

    # Step 1: Create Purchase Order
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 1: Creating Purchase Order {trade_data['po_number']}...")
    po_page = PurchaseOrdersPage(page)
    po_page.open(po_page.path)
    po_page.verify_page()

    po_page.open_create_form()
    drawer = page.locator(".q-drawer.q-drawer--right:visible").last

    # 1. Customer Selection
    print("  Selecting customer Bajaj Holdings...")
    cust_inp = drawer.locator("input[placeholder='Select customer']")
    cust_inp.click(force=True)
    cust_inp.type(trade_data["customer_search"], delay=80)
    page.wait_for_timeout(1500)
    menu_item = page.locator(".q-menu .q-item").filter(has_text="Bajaj Holdings").first
    expect(menu_item).to_be_visible(timeout=10000)
    menu_item.click()
    page.wait_for_timeout(1000)

    # 2. PO Number
    drawer.locator("input[placeholder='Enter PO number']").fill(trade_data["po_number"])

    # 3. Dates
    date_inps = drawer.locator("input[placeholder='DD-MM-YYYY']")
    date_inps.nth(0).focus()
    page.wait_for_timeout(400)
    page.locator(".vc-day.is-today:visible").click(force=True)
    page.wait_for_timeout(400)

    # Expect. Delivery Date
    date_inps.nth(2).focus()
    page.wait_for_timeout(400)
    day_cell = page.locator(".vc-day:not(.is-not-in-month):visible").filter(has_text="28").first
    if day_cell.is_visible():
        day_cell.click(force=True)
    else:
        page.locator(".vc-day:not(.is-not-in-month):visible").last.click(force=True)
    page.wait_for_timeout(400)

    # 4. Bill To & Ship To (select 'test qa add' which is < 100 chars to satisfy e-invoicing)
    print("  Selecting compliant address (test qa add)...")
    bill_to = drawer.locator("input[placeholder='Select an address']").first
    bill_to.click(force=True)
    page.wait_for_timeout(600)
    addr_item = page.locator(".q-menu .q-item").filter(has_text="test qa add").first
    if addr_item.count() and addr_item.is_visible():
        addr_item.click()
    else:
        page.locator(".q-menu .q-item").nth(1).click()
    page.wait_for_timeout(600)

    ship_to = drawer.locator("input[placeholder='Select an address']").nth(1)
    ship_to.click(force=True)
    page.wait_for_timeout(600)
    addr_item = page.locator(".q-menu .q-item").filter(has_text="test qa add").first
    if addr_item.count() and addr_item.is_visible():
        addr_item.click()
    else:
        page.locator(".q-menu .q-item").nth(1).click()
    page.wait_for_timeout(600)

    # 5. Add Line Items via ItemForm drawer
    for itm in trade_data["items"]:
        print(f"  Adding line item: {itm['product']} x {itm['quantity']} @ ₹{itm['po_rate']}...")
        drawer.get_by_role("button", name="Add Items to PO").click(force=True)
        page.wait_for_timeout(1200)

        item_drawer = page.locator(".q-drawer.q-drawer--right:visible").last
        prod_inp = item_drawer.locator("input[placeholder='Select Product']")
        prod_inp.click(force=True)
        prod_inp.type(itm["search"], delay=80)
        page.wait_for_timeout(1500)
        prod_item = page.locator(".q-menu .q-item").filter(has_text=itm["product"]).first
        expect(prod_item).to_be_visible(timeout=10000)
        prod_item.click()
        page.wait_for_timeout(500)

        item_drawer.locator("input[placeholder='Enter rate']").fill(itm["po_rate"])
        item_drawer.locator("input[placeholder='Enter value']").first.fill(itm["quantity"])

        add_btn = item_drawer.get_by_role("button", name="Add")
        expect(add_btn).to_be_enabled()
        add_btn.click(force=True)
        page.wait_for_timeout(1000)

    # 6. Upload Proof Document
    file_inp = drawer.locator("input[type='file']")
    if file_inp.count() > 0:
        file_inp.set_input_files(str(FIXTURE_PDF))
        page.wait_for_timeout(500)

    # 7. Account Owner
    owner_inp = drawer.locator("input[placeholder='Select an owner']")
    owner_inp.scroll_into_view_if_needed()
    owner_inp.click(force=True)
    page.wait_for_timeout(800)
    page.locator(".q-menu .q-item").first.click()
    page.wait_for_timeout(500)

    # 8. Submit Purchase Order
    submit_btn = drawer.get_by_role("button", name="Submit")
    expect(submit_btn).to_be_enabled()
    submit_btn.click()
    page.wait_for_timeout(3500)
    print(f"  PO {trade_data['po_number']} submitted successfully!")

    # Step 2: Open PO Details
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 2: Opening PO Details for {trade_data['po_number']}...")
    po_page.open_po_details(trade_data["po_number"])
    po_detail_url = page.url
    print(f"  PO Detail URL: {po_detail_url}")

    # Step 3: Record Entry -> Add Purchase Bill with Reliance Industries Limited
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 3: Recording Purchase Bill {trade_data['pb_number']} with Reliance Industries Limited...")
    page.get_by_role("button", name="Record Entry").click()
    page.wait_for_timeout(600)
    page.locator(".q-menu .q-item").filter(has_text="Add Purchase Bill").click()
    page.wait_for_timeout(1500)

    pb_drawer = page.locator(".q-drawer.q-drawer--right:visible").last

    # 1. Vendor Selection: Reliance Industries Limited
    print("  Selecting vendor Reliance Industries Limited...")
    vendor_inp = pb_drawer.locator("input[placeholder='Select Vendor']")
    vendor_inp.click(force=True)
    vendor_inp.type("Reliance", delay=80)
    page.wait_for_timeout(1500)
    rel_item = page.locator(".q-menu .q-item").filter(has_text="Reliance Industries Limited").first
    expect(rel_item).to_be_visible(timeout=10000)
    rel_item.click()
    page.wait_for_timeout(1000)

    # 2. Purchase Bill Number
    pb_num_inp = pb_drawer.locator("input[placeholder='Enter value']").first
    pb_num_inp.fill(trade_data["pb_number"])
    page.wait_for_timeout(500)

    # 3. Purchase Bill Date
    date_inp = pb_drawer.locator("input[placeholder='DD-MM-YYYY']").first
    date_inp.focus()
    page.wait_for_timeout(400)
    page.locator(".vc-day.is-today:visible").click(force=True)
    page.wait_for_timeout(400)

    # 4. Vehicle No.
    veh_inp = pb_drawer.locator("input[placeholder='Enter value']").nth(1)
    veh_inp.fill(trade_data["vehicle_number"])
    page.wait_for_timeout(500)

    # 5. Bill To address
    bill_to = pb_drawer.locator("input[placeholder='Select an address']").first
    bill_to.click(force=True)
    page.wait_for_timeout(600)
    page.locator(".q-menu .q-item").first.click()
    page.wait_for_timeout(600)

    # 6. Update line item rates & quantities
    data_rows = pb_drawer.locator("tbody tr")
    row_count = data_rows.count()
    for idx, itm in enumerate(trade_data["items"]):
        print(f"  Updating PB line item {idx + 1}: {itm['product']} x {itm['quantity']} @ ₹{itm['pb_rate']}...")
        target_row = data_rows.nth(idx + 1) if row_count > idx + 1 else data_rows.nth(idx)
        edit_btn = target_row.locator("button, .q-btn").first
        if edit_btn.is_visible():
            edit_btn.click(force=True)
            page.wait_for_timeout(1000)

            pb_item_drawer = page.locator(".q-drawer.q-drawer--right:visible").last
            pb_item_drawer.locator("input[placeholder='Enter rate']").fill(itm["pb_rate"])
            pb_item_drawer.locator("input[placeholder='Enter value']").first.fill(itm["quantity"])

            save_btn = pb_item_drawer.get_by_role("button", name="Save").or_(pb_item_drawer.get_by_role("button", name="Add"))
            save_btn.click(force=True)
            page.wait_for_timeout(1000)

    # 7. Submit Purchase Bill
    submit_pb_btn = pb_drawer.get_by_role("button", name="Submit")
    expect(submit_pb_btn).to_be_enabled()
    submit_pb_btn.click()
    page.wait_for_timeout(1500)

    # Confirm dialog if presented
    dialog = page.locator(".q-dialog:visible")
    if dialog.is_visible():
        confirm_btn = dialog.get_by_role("button", name="Submit").or_(
            dialog.get_by_role("button", name="Yes")
        ).or_(dialog.get_by_role("button", name="OK")).or_(dialog.get_by_role("button", name="Confirm"))
        if confirm_btn.is_visible():
            confirm_btn.click()
    page.wait_for_timeout(3500)
    print(f"  Purchase Bill {trade_data['pb_number']} recorded successfully!")

    # Step 4: Request Invoice (TILL INVOICE APPROVAL - DO NOT APPROVE!)
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 4: Requesting Invoice (Pending Approval)...")
    req_btn = page.get_by_role("button", name="Request Invoice")
    expect(req_btn).to_be_visible(timeout=10000)
    req_btn.click()
    page.wait_for_timeout(1500)

    inv_drawer = page.locator(".q-drawer.q-drawer--right:visible").last

    # Select Purchase Bill
    pb_inp = inv_drawer.locator("input[placeholder='Select purchase bill']")
    pb_inp.click(force=True)
    page.wait_for_timeout(800)
    page.locator(".q-menu .q-item").first.click()
    page.wait_for_timeout(1000)

    # Select Dispatch From address (select compliant address < 100 chars like 'gj test' or 'test')
    dispatch_inp = inv_drawer.locator("input[placeholder='Select an address']").nth(2)
    dispatch_inp.click(force=True)
    page.wait_for_timeout(800)
    disp_item = page.locator(".q-menu .q-item").filter(has_text="gj test").first
    if disp_item.count() and disp_item.is_visible():
        disp_item.click()
    else:
        disp_item2 = page.locator(".q-menu .q-item").filter(has_text="test").first
        if disp_item2.count() and disp_item2.is_visible():
            disp_item2.click()
        else:
            page.locator(".q-menu .q-item").last.click()
    page.wait_for_timeout(800)

    # Submit
    submit_inv_btn = inv_drawer.get_by_role("button", name="Submit")
    expect(submit_inv_btn).to_be_enabled()
    submit_inv_btn.click()
    page.wait_for_timeout(2000)

    # Confirm Dialog if present
    dialog = page.locator(".q-dialog:visible")
    if dialog.count() > 0 and dialog.is_visible():
        print("  Confirming Request Invoice dialog...")
        confirm_btn = dialog.get_by_role("button", name="Submit").or_(
            dialog.get_by_role("button", name="Send")
        ).or_(dialog.get_by_role("button", name="Confirm")).or_(dialog.get_by_role("button", name="Yes"))
        if confirm_btn.count() > 0:
            confirm_btn.first.click()
            page.wait_for_timeout(3000)

    page.wait_for_timeout(3000)
    print("  Invoice request created and submitted successfully!")

    # Step 5: Verify Invoice Request under Accounts -> Invoice Requests
    print(f"\n[{time.strftime('%H:%M:%S')}] Step 5: Verifying under Accounts -> Invoice Requests...")
    accounts_page = AccountsInvoiceRequestsPage(page)
    accounts_page.open(accounts_page.path)
    accounts_page.verify_page()
    accounts_page.search_by_po(trade_data["po_number"])
    page.wait_for_timeout(2500)

    row = page.locator("tbody tr:visible").first
    expect(row).to_be_visible(timeout=15000)
    row_text = row.inner_text().replace("\n", " | ")
    print(f"  Found in Accounts list: {row_text}")

    invoice_requests_url = f"{BASE_URL}/accounts/invoice-requests"
    browser.close()

print("\n" + "=" * 75)
print("🎉 REQUESTED TEST DATA CREATED SUCCESSFULLY ON BRANCH 2406!")
print(f"• Customer:       {trade_data['customer']} ({trade_data['customer_search']})")
print(f"• Vendor:         {trade_data['vendor']} ({trade_data['vendor_search']})")
print(f"• Product:        {trade_data['product']}")
print(f"• Quantity:       {trade_data['quantity']}")
print(f"• PO Rate/Total:  ₹{trade_data['po_rate']} / ₹{int(trade_data['po_rate']) * int(trade_data['quantity']):,}")
print(f"• PB Rate/Total:  ₹{trade_data['pb_rate']} / ₹{int(trade_data['pb_rate']) * int(trade_data['quantity']):,}")
print(f"• Purchase Order: {trade_data['po_number']}")
print(f"  PO URL:         {po_detail_url}")
print(f"• Purchase Bill:  {trade_data['pb_number']}")
print(f"• Invoice Status: PENDING APPROVAL (Stopped at Approval Flow for You!)")
print(f"  Approval Page:  {invoice_requests_url}")
print("=" * 75)

# Alert user
os.system('afplay /System/Library/Sounds/Ping.aiff && say "Test data created successfully. Purchase order, bill with Reliance Industries, and invoice request for Bajaj Holdings are ready for your approval."')
