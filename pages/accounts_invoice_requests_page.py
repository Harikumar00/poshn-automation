from pathlib import Path
import re
import time
from playwright.sync_api import Locator, Page, expect

from pages.list_page import ListPage

DEFAULT_FIXTURE_DOC = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_document.pdf"


class AccountsInvoiceRequestsPage(ListPage):
    path = "/accounts/invoice-requests"
    expected_title = "Poshn - Invoice Requests"

    def verify_page(self) -> None:
        expect(self.page).to_have_url(re.compile(r".*/accounts/invoice-requests/?$"))
        expect(self.page).to_have_title(self.expected_title)
        expect(self.page.locator("main").get_by_text("Invoice Requests", exact=False).first).to_be_visible()

    def search_by_po(self, po_number: str) -> Locator:
        """Searches for invoice requests associated with a PO number and returns the first row."""
        search_inp = self.page.locator("input[placeholder*='PO number']").first
        search_inp.fill(po_number)
        self.page.wait_for_timeout(2000)
        return self.page.locator("tbody tr:visible").first

    def approve_invoice_request(
        self,
        po_number: str,
        invoice_number: str | None = None,
        file_path: Path | str | None = None,
    ) -> dict:
        """Approves and adds E-Invoice details for the given PO's invoice request."""
        if invoice_number is None:
            invoice_number = f"INV-AUTO-{int(time.time())}"

        if file_path is None:
            file_path = DEFAULT_FIXTURE_DOC

        row = self.search_by_po(po_number)
        expect(row).to_be_visible(timeout=15000)

        # Click Add Invoice button (first action button in row)
        row.locator("button, .q-btn").first.click()
        self.page.wait_for_timeout(2000)

        drawer = self.page.locator(".q-drawer.q-drawer--right:visible, .q-dialog:visible").last
        expect(drawer.get_by_text("Add E-invoice", exact=False).first).to_be_visible(timeout=10000)

        # 1. Enter Invoice Number
        inv_inp = drawer.locator("input[placeholder='Enter value']").first
        inv_inp.fill(invoice_number)
        self.page.wait_for_timeout(500)

        # 2. Upload E-Invoice Proof File
        file_inp = drawer.locator("input[type='file']")
        if file_inp.count() > 0:
            file_inp.set_input_files(str(file_path))
            self.page.wait_for_timeout(500)

        # 3. Submit
        submit_btn = drawer.get_by_role("button", name="Submit")
        expect(submit_btn).to_be_enabled()
        submit_btn.click()
        self.page.wait_for_timeout(2000)

        # Confirm dialog if presented
        dialog = self.page.locator(".q-dialog:visible")
        if dialog.is_visible():
            confirm_btn = dialog.get_by_role("button", name="Submit").or_(
                dialog.get_by_role("button", name="Yes")
            ).or_(dialog.get_by_role("button", name="Confirm"))
            if confirm_btn.is_visible():
                confirm_btn.click()
        self.page.wait_for_timeout(3000)

        return {
            "invoice_number": invoice_number,
            "po_number": po_number,
        }

    def approve_pod(self, po_number: str) -> None:
        """Approves the Proof of Delivery (POD) for a given PO from the PODs Received tab."""
        self.open(self.path)
        self.verify_page()

        # Switch to PODs Received tab
        pods_received_tab = self.page.locator(".q-tab, button").filter(has_text="PODs Received").first
        pods_received_tab.click()
        self.page.wait_for_timeout(1500)

        # Search by PO Number (using editable search input)
        search_inp = self.page.locator("input[placeholder*='Search by PO number']")
        search_inp.fill(po_number)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(2000)

        row = self.page.locator("tbody tr:visible").first
        expect(row).to_be_visible(timeout=15000)

        # Click the View button (first button in last td)
        row.locator("td").last.locator("button").first.click()
        self.page.wait_for_timeout(2000)

        # In drawer, click "Accept proof of delivery"
        drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last
        accept_btn = drawer.get_by_role("button", name="Accept proof of delivery")
        expect(accept_btn).to_be_visible(timeout=10000)
        expect(accept_btn).to_be_enabled(timeout=10000)
        accept_btn.click()
        self.page.wait_for_timeout(1000)

        # In confirmation dialog, click "Accept POD"
        dialog = self.page.locator(".q-dialog:visible")
        expect(dialog).to_be_visible(timeout=10000)
        accept_pod_dialog_btn = dialog.get_by_role("button", name="Accept POD")
        expect(accept_pod_dialog_btn).to_be_visible()
        accept_pod_dialog_btn.click()
        self.page.wait_for_timeout(3000)

    def approve_credit_note(
        self,
        po_or_ref: str,
        cn_number: str | None = None,
        file_path: Path | str | None = None,
    ) -> dict:
        """Approves and adds Credit Note details from Pending Credit Notes tab."""
        if cn_number is None:
            cn_number = f"CN-AUTO-{int(time.time())}"
        if file_path is None:
            file_path = DEFAULT_FIXTURE_DOC

        self.open(self.path)
        self.verify_page()

        # Switch to Pending Credit Notes tab
        cn_tab = self.page.locator(".q-tab, button").filter(has_text="Pending Credit Notes").first
        cn_tab.click()
        self.page.wait_for_timeout(1500)

        # Search
        search_inp = self.page.locator("input[placeholder*='Credit Note number']").first
        search_inp.fill(po_or_ref)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(2000)

        row = self.page.locator("tbody tr:visible").first
        expect(row).to_be_visible(timeout=15000)

        # Click Add Credit Note button (first button in last td)
        row.locator("td").last.locator("button").first.click()
        self.page.wait_for_timeout(2000)

        drawer = self.page.locator(".q-drawer.q-drawer--right:visible, .q-dialog:visible").last
        expect(drawer.get_by_text("Add Credit Note", exact=False).first).to_be_visible(timeout=10000)

        # 1. Fill Credit Note No.
        cn_num_inp = drawer.locator("input[placeholder='Enter value']").first
        cn_num_inp.fill(cn_number)
        self.page.wait_for_timeout(500)

        # 2. Attach Proof Document
        file_inp = drawer.locator("input[type='file']")
        if file_inp.count() > 0:
            file_inp.set_input_files(str(file_path))
            self.page.wait_for_timeout(500)

        # 3. Submit
        submit_btn = drawer.get_by_role("button", name="Submit")
        expect(submit_btn).to_be_enabled()
        submit_btn.click()
        self.page.wait_for_timeout(3000)

        return {
            "cn_number": cn_number,
            "ref_number": po_or_ref,
        }

    def approve_debit_note(
        self,
        po_or_ref: str,
        dn_number: str | None = None,
        file_path: Path | str | None = None,
    ) -> dict:
        """Approves and adds Debit Note details from Pending Debit Notes tab."""
        if dn_number is None:
            dn_number = f"DN-AUTO-{int(time.time())}"
        if file_path is None:
            file_path = DEFAULT_FIXTURE_DOC

        self.open(self.path)
        self.verify_page()

        # Switch to Pending Debit Notes tab
        dn_tab = self.page.locator(".q-tab, button").filter(has_text="Pending Debit Notes").first
        dn_tab.click()
        self.page.wait_for_timeout(1500)

        # Search
        search_inp = self.page.locator("input[placeholder*='Debit Note number'], input[placeholder*='PB Number']").first
        search_inp.fill(po_or_ref)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(2000)

        row = self.page.locator("tbody tr:visible").first
        expect(row).to_be_visible(timeout=15000)

        # Click Add Debit Note button (first button in last td)
        row.locator("td").last.locator("button").first.click()
        self.page.wait_for_timeout(2000)

        drawer = self.page.locator(".q-drawer.q-drawer--right:visible, .q-dialog:visible").last
        expect(drawer.get_by_text("Add Debit Note", exact=False).first).to_be_visible(timeout=10000)

        # 1. Fill Debit Note No.
        dn_num_inp = drawer.locator("input[placeholder='Enter value']").first
        dn_num_inp.fill(dn_number)
        self.page.wait_for_timeout(500)

        # 2. Attach Proof Document
        file_inp = drawer.locator("input[type='file']")
        if file_inp.count() > 0:
            file_inp.set_input_files(str(file_path))
            self.page.wait_for_timeout(500)

        # 3. Submit
        submit_btn = drawer.get_by_role("button", name="Submit")
        expect(submit_btn).to_be_enabled()
        submit_btn.click()
        self.page.wait_for_timeout(3000)

        return {
            "dn_number": dn_number,
            "ref_number": po_or_ref,
        }
