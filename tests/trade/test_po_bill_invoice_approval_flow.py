import time
import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.purchase_orders_page import PurchaseOrdersPage
from pages.accounts_invoice_requests_page import AccountsInvoiceRequestsPage
from pages.invoices_page import InvoicesPage
from pages.notes_page import NotesPage


@pytest.fixture(scope="module")
def trade_data():
    """Shared test data for the PO -> Bill -> Invoice -> Accounts Approval lifecycle."""
    ts = str(int(time.time()))
    return {
        "customer": settings.test_customer,
        "customer_search": "27AAACB3370K1ZP",
        "vendor": settings.test_vendor,
        "vendor_search": "AAACR5055K",
        "items": [
            {
                "product": settings.test_product,
                "po_rate": "250",
                "pb_rate": "200",
                "quantity": settings.test_quantity,
            },
            {
                "product": settings.test_product_2,
                "po_rate": "250",
                "pb_rate": "200",
                "quantity": settings.test_quantity,
            },
        ],
        "product": settings.test_product,
        "po_number": f"PO-BAJAJ-REL-{ts}",
        "pb_number": f"PB-BAJAJ-REL-{ts}",
        "invoice_number": f"INV-BAJAJ-REL-{ts}",
        "pod_number": f"POD-BAJAJ-REL-{ts}",
        "cn_number": f"CN-BAJAJ-REL-{ts}",
        "dn_number": f"DN-BAJAJ-REL-{ts}",
        "po_rate": "250",
        "pb_rate": "200",
        "quantity": settings.test_quantity,
        "cn_quantity": "10",
        "dn_quantity": "10",
        "vehicle_number": "MH12AB1234",
    }



@pytest.mark.regression
def test_create_purchase_order(authenticated_page: Page, trade_data: dict):
    """Verify creating a Purchase Order for Bajaj Holdings with both line items."""
    po_page = PurchaseOrdersPage(authenticated_page)
    po_page.open(po_page.path)
    po_page.verify_page()

    created = po_page.create_purchase_order(
        customer=trade_data["customer"],
        po_number=trade_data["po_number"],
        customer_search=trade_data["customer_search"],
        items=[
            {
                "product": item["product"],
                "rate": item["po_rate"],
                "quantity": item["quantity"],
            }
            for item in trade_data["items"]
        ],
    )

    assert created["po_number"] == trade_data["po_number"]
    authenticated_page.wait_for_timeout(2000)

    # Search for created PO and verify it appears in the list
    po_page.search(trade_data["po_number"])
    row = authenticated_page.locator("tbody tr:visible").first
    expect(row).to_be_visible(timeout=15000)
    expect(row).to_contain_text(trade_data["po_number"])
    expect(row).to_contain_text(trade_data["customer"])


@pytest.mark.regression
def test_create_and_link_purchase_bill(authenticated_page: Page, trade_data: dict):
    """Verify opening the PO detail and recording a Purchase Bill with Reliance Industries Limited."""
    po_page = PurchaseOrdersPage(authenticated_page)
    po_page.open(po_page.path)
    po_page.verify_page()

    # Open the created PO Detail page
    po_page.open_po_details(trade_data["po_number"])

    # Verify action buttons on PO Detail
    expect(authenticated_page.get_by_role("button", name="Record Entry")).to_be_visible()
    expect(authenticated_page.get_by_role("button", name="Request Invoice")).to_be_visible()

    # Record Purchase Bill against PO with both items
    created_pb = po_page.record_entry_add_purchase_bill(
        vendor=trade_data["vendor"],
        pb_number=trade_data["pb_number"],
        vehicle_number=trade_data["vehicle_number"],
        vendor_search=trade_data["vendor_search"],
        items=[
            {
                "rate": item["pb_rate"],
                "quantity": item["quantity"],
            }
            for item in trade_data["items"]
        ],
    )
    assert created_pb["pb_number"] == trade_data["pb_number"]

    # Verify the Purchase Bill is listed under PO's Bills & Invoices
    authenticated_page.wait_for_timeout(2000)
    expect(authenticated_page.get_by_text("Purchase Bills (1)", exact=False)).to_be_visible(timeout=15000)
    expect(authenticated_page.locator("main").get_by_text(trade_data["pb_number"])).to_be_visible()
    expect(authenticated_page.locator("main").get_by_text(trade_data["vendor"])).to_be_visible()


@pytest.mark.regression
def test_request_and_approve_invoice(authenticated_page: Page, trade_data: dict):
    """Verify requesting an invoice against the PO & PB and approving it in Accounts."""
    po_page = PurchaseOrdersPage(authenticated_page)
    # Ensure on PO detail page
    if "purchase-orders" not in authenticated_page.url or trade_data["po_number"] not in authenticated_page.locator("main").inner_text():
        po_page.open_po_details(trade_data["po_number"])

    # Request Invoice
    po_page.request_invoice()
    authenticated_page.wait_for_timeout(2000)

    # Navigate to Accounts Invoice Requests
    accounts_page = AccountsInvoiceRequestsPage(authenticated_page)
    accounts_page.open(accounts_page.path)
    accounts_page.verify_page()

    # Search for PO and approve invoice request
    approved = accounts_page.approve_invoice_request(
        po_number=trade_data["po_number"],
        invoice_number=trade_data["invoice_number"],
    )
    assert approved["invoice_number"] == trade_data["invoice_number"]
    authenticated_page.wait_for_timeout(2000)

    # Navigate to Sales Invoices and verify the newly approved invoice
    invoices_page = InvoicesPage(authenticated_page)
    invoices_page.verify_invoice_listed(
        invoice_number=trade_data["invoice_number"],
        customer=trade_data["customer"],
        expected_stage="POD Pending",
    )


@pytest.mark.regression
def test_add_and_approve_pod(authenticated_page: Page, trade_data: dict):
    """Verify adding Proof of Delivery (POD) against the PO and Invoice, and approving it from Accounts."""
    po_page = PurchaseOrdersPage(authenticated_page)

    # 1. Ensure on PO Detail page
    po_page.open_po_details(trade_data["po_number"])

    # 2. Record Entry -> Add Proof of Delivery
    pod_data = po_page.record_entry_add_pod(
        invoice_number=trade_data["invoice_number"],
        pod_number=trade_data["pod_number"],
        vehicle_number=trade_data["vehicle_number"],
    )
    assert pod_data["invoice_number"] == trade_data["invoice_number"]
    authenticated_page.wait_for_timeout(2000)

    # 3. Verify on Sales Invoices that invoice stage transitioned to 'POD Received'
    invoices_page = InvoicesPage(authenticated_page)
    invoices_page.verify_invoice_listed(
        invoice_number=trade_data["invoice_number"],
        customer=trade_data["customer"],
        expected_stage="POD Received",
    )

    # 4. Navigate to Accounts Invoice Requests -> PODs Received tab and approve POD
    accounts_page = AccountsInvoiceRequestsPage(authenticated_page)
    accounts_page.approve_pod(trade_data["po_number"])
    authenticated_page.wait_for_timeout(2000)

    # 5. Verify on Sales Invoices that invoice stage transitioned to 'POD Accepted'
    invoices_page.verify_invoice_listed(
        invoice_number=trade_data["invoice_number"],
        customer=trade_data["customer"],
        expected_stage="POD Accepted",
    )


@pytest.mark.regression
def test_request_and_approve_credit_note_on_invoice(authenticated_page: Page, trade_data: dict):
    """Verify requesting a Credit Note against the Invoice and approving it in Accounts."""
    po_page = PurchaseOrdersPage(authenticated_page)
    po_page.open_po_details(trade_data["po_number"])

    # 1. Request Credit Note against Invoice with both products
    po_page.request_credit_note(
        invoice_or_bill_number=trade_data["invoice_number"],
        against="invoice",
        items=[
            {"product": item["product"], "quantity": trade_data["cn_quantity"]}
            for item in trade_data["items"]
        ],
    )
    authenticated_page.wait_for_timeout(2000)

    # 2. Approve Credit Note from Accounts
    accounts_page = AccountsInvoiceRequestsPage(authenticated_page)
    approved_cn = accounts_page.approve_credit_note(
        po_or_ref=trade_data["po_number"],
        cn_number=trade_data["cn_number"],
    )
    assert approved_cn["cn_number"] == trade_data["cn_number"]
    authenticated_page.wait_for_timeout(2000)

    # 3. Verify on Sales Credit Notes list
    sales_cn_page = NotesPage(authenticated_page, "/sales/credit-notes", "Poshn - Credit Notes")
    sales_cn_page.verify_note_listed(
        note_number=trade_data["cn_number"],
        ref_number=trade_data["invoice_number"],
        party=trade_data["customer"],
        expected_status="Active",
    )


@pytest.mark.regression
def test_request_and_approve_debit_note_on_purchase_bill(authenticated_page: Page, trade_data: dict):
    """Verify requesting a Debit Note against the Purchase Bill and approving it in Accounts."""
    po_page = PurchaseOrdersPage(authenticated_page)
    po_page.open_po_details(trade_data["po_number"])

    # 1. Request Debit Note against Purchase Bill with both products
    po_page.request_debit_note(
        bill_or_invoice_number=trade_data["pb_number"],
        against="bill",
        items=[
            {"product": item["product"], "quantity": trade_data["dn_quantity"]}
            for item in trade_data["items"]
        ],
    )
    authenticated_page.wait_for_timeout(2000)

    # 2. Approve Debit Note from Accounts
    accounts_page = AccountsInvoiceRequestsPage(authenticated_page)
    approved_dn = accounts_page.approve_debit_note(
        po_or_ref=trade_data["pb_number"],
        dn_number=trade_data["dn_number"],
    )
    assert approved_dn["dn_number"] == trade_data["dn_number"]
    authenticated_page.wait_for_timeout(2000)

    # 3. Verify on Purchases Debit Notes list
    purchases_dn_page = NotesPage(authenticated_page, "/purchases/debit-notes", "Poshn - Debit Notes")
    purchases_dn_page.verify_note_listed(
        note_number=trade_data["dn_number"],
        ref_number=trade_data["pb_number"],
        party=trade_data["vendor"],
        expected_status="Active",
    )
