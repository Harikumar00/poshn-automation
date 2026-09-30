from pathlib import Path
import re
import time
from playwright.sync_api import Page, expect

from pages.list_page import ListPage

DEFAULT_FIXTURE_DOC = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_document.pdf"


class PurchaseOrdersPage(ListPage):
    path = "/sales/purchase-orders"
    expected_title = "Poshn - Purchase Orders"

    def verify_page(self) -> None:
        expect(self.page).to_have_url(re.compile(r".*/sales/purchase-orders/?$"))
        expect(self.page).to_have_title(self.expected_title)
        expect(self.page.locator("main").get_by_text("Purchase Orders", exact=False).first).to_be_visible()
        expect(self.page.get_by_role("button", name="Create PO")).to_be_visible()
        expect(self.page.get_by_role("columnheader", name="Status")).to_be_visible()

    def open_create_form(self) -> None:
        self.page.get_by_role("button", name="Create PO").click()
        expect(self.page.get_by_text("Create Purchase Order", exact=True)).to_be_visible()

    def required_form_labels(self) -> list[str]:
        return [
            "Select Customer *", "Delivery Type *", "Payment Terms *",
            "Issue Date *", "Expect. Delivery Date *", "Bill To *",
            "Ship To *", "Account Owner *",
        ]

    def create_purchase_order(
        self,
        customer: str,
        product: str,
        rate: str = "250",
        quantity: str = "10",
        po_number: str | None = None,
        owner: str = "kam_kiran",
        file_path: Path | str | None = None,
        customer_search: str | None = None,
        items: list[dict[str, str]] | None = None,
    ) -> dict:
        """Creates a new Purchase Order via the UI drawer and submits it."""
        if po_number is None:
            po_number = f"PO-AUTO-{str(int(time.time()))}"

        if file_path is None:
            file_path = DEFAULT_FIXTURE_DOC

        self.open_create_form()
        drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last

        # 1. Customer Selection
        cust_inp = drawer.locator("input[placeholder='Select customer']")
        cust_inp.fill(customer_search or customer)
        self.page.wait_for_timeout(1000)
        self.page.locator(".q-menu .q-item").first.click()
        self.page.wait_for_timeout(1000)

        # 2. PO Number
        drawer.locator("input[placeholder='Enter PO number']").fill(po_number)

        # 3. Dates
        date_inps = drawer.locator("input[placeholder='DD-MM-YYYY']")
        # Issue Date (today)
        date_inps.nth(0).focus()
        self.page.wait_for_timeout(400)
        self.page.locator(".vc-day.is-today:visible").click(force=True)
        self.page.wait_for_timeout(400)

        # Expect. Delivery Date (future date)
        date_inps.nth(2).focus()
        self.page.wait_for_timeout(400)
        day_cell = self.page.locator(".vc-day:not(.is-not-in-month):visible").filter(has_text="25").first
        if day_cell.is_visible():
            day_cell.click(force=True)
        else:
            self.page.locator(".vc-day:not(.is-not-in-month):visible").last.click(force=True)
        self.page.wait_for_timeout(400)

        # 4. Bill To & Ship To
        bill_to = drawer.locator("input[placeholder='Select an address']").first
        bill_to.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").first.click()
        self.page.wait_for_timeout(500)

        ship_to = drawer.locator("input[placeholder='Select an address']").nth(1)
        ship_to.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").first.click()
        self.page.wait_for_timeout(500)

        # 5. Add Line Item(s) via ItemForm drawer
        items_to_add = items if items else [{"product": product, "rate": rate, "quantity": quantity}]
        for itm in items_to_add:
            drawer.get_by_role("button", name="Add Items to PO").click(force=True)
            self.page.wait_for_timeout(1000)

            item_drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last
            prod_inp = item_drawer.locator("input[placeholder='Select Product']")
            prod_inp.click(force=True)
            prod_inp.fill(itm["product"])
            self.page.wait_for_timeout(1200)
            target_item = self.page.locator(".q-menu .q-item").filter(has_text=re.compile(re.escape(itm["product"]), re.I)).first
            if target_item.count() > 0:
                target_item.click()
            else:
                self.page.locator(".q-menu .q-item").first.click()
            self.page.wait_for_timeout(500)

            item_drawer.locator("input[placeholder='Enter rate']").fill(str(itm.get("rate", rate)))
            item_drawer.locator("input[placeholder='Enter value']").first.fill(str(itm.get("quantity", quantity)))

            add_btn = item_drawer.get_by_role("button", name="Add")
            expect(add_btn).to_be_enabled()
            add_btn.click(force=True)
            self.page.wait_for_timeout(1000)

        # 6. Upload Proof Document
        file_inp = drawer.locator("input[type='file']")
        if file_inp.count() > 0:
            file_inp.set_input_files(str(file_path))
            self.page.wait_for_timeout(500)

        # 7. Account Owner
        owner_inp = drawer.locator("input[placeholder='Select an owner']")
        owner_inp.scroll_into_view_if_needed()
        owner_inp.click(force=True)
        owner_inp.type(owner)
        self.page.wait_for_timeout(1000)
        self.page.locator(".q-menu .q-item").first.click()
        self.page.wait_for_timeout(500)

        # 8. Submit Purchase Order
        submit_btn = drawer.get_by_role("button", name="Submit")
        expect(submit_btn).to_be_enabled()
        submit_btn.click()
        self.page.wait_for_timeout(3000)

        return {
            "po_number": po_number,
            "customer": customer,
            "product": product,
            "rate": rate,
            "quantity": quantity,
            "items": items_to_add,
        }

    def open_po_details(self, po_number: str) -> None:
        """Searches for the PO in the list and opens its Detail page by clicking the view detail link."""
        self.open(self.path)
        self.verify_page()
        self.search(po_number)
        row = self.page.locator("tbody tr:visible").first
        expect(row).to_be_visible(timeout=15000)
        # Click view details link in the Action column (last td)
        detail_link = row.locator("td").last.locator("a")
        expect(detail_link).to_be_visible(timeout=10000)
        detail_link.click()
        expect(self.page).to_have_url(re.compile(r".*/sales/purchase-orders/[a-f0-9]+/?$"))
        expect(self.page.locator("main")).to_be_visible()
        self.page.wait_for_timeout(1000)

    def record_entry_add_purchase_bill(
        self,
        vendor: str,
        rate: str = "200",
        quantity: str = "10",
        pb_number: str | None = None,
        vehicle_number: str = "MH12AB1234",
        vendor_search: str | None = None,
        items: list[dict[str, str]] | None = None,
    ) -> dict:
        """Records a Purchase Bill against the current Purchase Order."""
        if pb_number is None:
            pb_number = f"PB-AUTO-{str(int(time.time()))}"

        self.page.get_by_role("button", name="Record Entry").click()
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").filter(has_text="Add Purchase Bill").click()
        self.page.wait_for_timeout(1500)

        pb_drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last

        # 1. Vendor Selection
        vendor_inp = pb_drawer.locator("input[placeholder='Select Vendor']")
        vendor_inp.fill(vendor_search or vendor)
        self.page.wait_for_timeout(1000)
        self.page.locator(".q-menu .q-item").first.click()
        self.page.wait_for_timeout(1000)

        # 2. Purchase Bill Number
        pb_num_inp = pb_drawer.locator("input[placeholder='Enter value']").first
        pb_num_inp.fill(pb_number)
        self.page.wait_for_timeout(500)

        # 3. Purchase Bill Date
        date_inp = pb_drawer.locator("input[placeholder='DD-MM-YYYY']").first
        date_inp.focus()
        self.page.wait_for_timeout(400)
        self.page.locator(".vc-day.is-today:visible").click(force=True)
        self.page.wait_for_timeout(400)

        # 4. Vehicle No.
        veh_inp = pb_drawer.locator("input[placeholder='Enter value']").nth(1)
        veh_inp.fill(vehicle_number)
        self.page.wait_for_timeout(500)

        # 5. Bill To address
        bill_to = pb_drawer.locator("input[placeholder='Select an address']").first
        bill_to.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").first.click()
        self.page.wait_for_timeout(500)

        # 6. Update line item rate & quantity
        items_to_update = items if items else [{"rate": rate, "quantity": quantity}]
        data_rows = pb_drawer.locator("tbody tr")
        row_count = data_rows.count()
        for idx, itm in enumerate(items_to_update):
            target_row = data_rows.nth(idx + 1) if row_count > idx + 1 else data_rows.nth(idx)
            edit_btn = target_row.locator("button, .q-btn").first
            if edit_btn.is_visible():
                edit_btn.click(force=True)
                self.page.wait_for_timeout(1000)

                item_drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last
                item_drawer.locator("input[placeholder='Enter rate']").fill(str(itm.get("rate", rate)))
                item_drawer.locator("input[placeholder='Enter value']").first.fill(str(itm.get("quantity", quantity)))

                save_btn = item_drawer.get_by_role("button", name="Save").or_(item_drawer.get_by_role("button", name="Add"))
                save_btn.click(force=True)
                self.page.wait_for_timeout(1000)

        # 7. Submit Purchase Bill
        submit_btn = pb_drawer.get_by_role("button", name="Submit")
        expect(submit_btn).to_be_enabled()
        submit_btn.click()
        self.page.wait_for_timeout(1500)

        # Confirm dialog if presented
        dialog = self.page.locator(".q-dialog:visible")
        if dialog.is_visible():
            confirm_btn = dialog.get_by_role("button", name="Submit").or_(
                dialog.get_by_role("button", name="Yes")
            ).or_(dialog.get_by_role("button", name="OK")).or_(dialog.get_by_role("button", name="Confirm"))
            if confirm_btn.is_visible():
                confirm_btn.click()
        self.page.wait_for_timeout(3000)

        return {
            "pb_number": pb_number,
            "vendor": vendor,
            "rate": rate,
            "quantity": quantity,
            "vehicle_number": vehicle_number,
        }

    def request_invoice(self) -> None:
        """Requests an invoice against the current Purchase Order and Purchase Bill."""
        self.page.get_by_role("button", name="Request Invoice").click()
        self.page.wait_for_timeout(1500)

        drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last

        # Select Purchase Bill
        pb_select = drawer.locator("input[placeholder='Select purchase bill']")
        pb_select.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").first.click()
        self.page.wait_for_timeout(1000)

        # Select Dispatch From address
        dispatch_inp = drawer.locator("input[placeholder='Select an address']").nth(2)
        if dispatch_inp.is_visible():
            dispatch_inp.click(force=True)
            self.page.wait_for_timeout(500)
            self.page.locator(".q-menu .q-item").first.click()
            self.page.wait_for_timeout(500)

        # Submit in drawer
        submit_btn = drawer.get_by_role("button", name="Submit")
        expect(submit_btn).to_be_enabled()
        submit_btn.click()
        self.page.wait_for_timeout(1500)

        # Confirm in dialog
        dialog = self.page.locator(".q-dialog:visible")
        if dialog.is_visible():
            dialog_submit = dialog.get_by_role("button", name="Submit").or_(
                dialog.get_by_role("button", name="Send")
            )
            if dialog_submit.count() > 0:
                dialog_submit.first.click()
                self.page.wait_for_timeout(3000)

    def record_entry_add_pod(
        self,
        invoice_number: str,
        pod_number: str | None = None,
        vehicle_number: str = "MH12AB1234",
        file_path: Path | str | None = None,
    ) -> dict:
        """Records a Proof of Delivery (POD) against the current Purchase Order and Invoice."""
        if file_path is None:
            from pages.accounts_invoice_requests_page import DEFAULT_FIXTURE_DOC
            file_path = DEFAULT_FIXTURE_DOC

        if pod_number is None:
            pod_number = invoice_number

        self.page.get_by_role("button", name="Record Entry").click()
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").filter(has_text="Add Proof of Delivery").click()
        self.page.wait_for_timeout(1500)

        pod_drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last

        # 1. Select Invoice
        inv_select = pod_drawer.locator("input[placeholder*='Select invoice']").first
        inv_select.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").filter(has_text=invoice_number).first.click()
        self.page.wait_for_timeout(1000)

        # 2. Fill POD Number if provided/desired
        pod_num_inp = pod_drawer.locator("input[placeholder='Enter value']").first
        if pod_number and pod_num_inp.input_value() != pod_number:
            pod_num_inp.fill(pod_number)

        # 3. Select POD Stamp Date (Today)
        date_inp = pod_drawer.locator("input[placeholder='DD-MM-YYYY']").first
        date_inp.click(force=True)
        self.page.wait_for_timeout(500)
        today_cell = self.page.locator(".vc-container:visible .vc-day.is-today:visible").first
        if today_cell.is_visible():
            today_cell.click(force=True)
            self.page.wait_for_timeout(400)

        # 4. Fill Vehicle Number if not pre-populated
        veh_inp = pod_drawer.locator("input[placeholder='Enter value']").nth(1)
        if not veh_inp.input_value():
            veh_inp.fill(vehicle_number)

        # 5. Attach Proof of Document (POD)
        file_inp = pod_drawer.locator("input[type='file']")
        file_inp.set_input_files(str(file_path))
        self.page.wait_for_timeout(500)

        # 6. Submit POD
        submit_btn = pod_drawer.get_by_role("button", name="Submit")
        expect(submit_btn).to_be_enabled()
        submit_btn.click()
        self.page.wait_for_timeout(3000)

        # Confirm dialog if presented
        dialog = self.page.locator(".q-dialog:visible")
        if dialog.is_visible():
            confirm_btn = dialog.get_by_role("button", name="Submit").or_(
                dialog.get_by_role("button", name="Yes")
            ).or_(dialog.get_by_role("button", name="OK")).or_(dialog.get_by_role("button", name="Confirm"))
            if confirm_btn.is_visible():
                confirm_btn.click()
                self.page.wait_for_timeout(2000)

        return {
            "pod_number": pod_number,
            "invoice_number": invoice_number,
            "vehicle_number": vehicle_number,
        }

    def request_credit_note(
        self,
        invoice_or_bill_number: str,
        product_name: str,
        quantity: str = "1",
        against: str = "invoice",
        cn_type: str = "Returns",
    ) -> dict:
        """Requests a Credit Note against an Invoice or Purchase Bill from the PO detail page."""
        # 1. Navigate to Bills & Invoices -> Credit Notes
        self.page.locator(".q-tab").filter(has_text="Bills & Invoices").first.click()
        self.page.wait_for_timeout(1000)
        self.page.locator(".q-tab").filter(has_text="Credit Notes").first.click()
        self.page.wait_for_timeout(1000)

        # 2. Click Request Credit Note button
        req_btn = self.page.get_by_role("button", name="Request Credit Note")
        expect(req_btn).to_be_visible(timeout=10000)
        req_btn.click()
        self.page.wait_for_timeout(1500)

        drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last

        # 3. Select radio 'Invoice' or 'Purchase Bill'
        if against.lower() in ("bill", "purchase bill", "purchase_bill"):
            drawer.get_by_text("Purchase Bill", exact=False).first.click()
            self.page.wait_for_timeout(500)
            select_inp = drawer.locator("input[placeholder*='Select purchase bill']").first
        else:
            select_inp = drawer.locator("input[placeholder*='Select invoice']").first

        select_inp.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").filter(has_text=invoice_or_bill_number).first.click()
        self.page.wait_for_timeout(1500)

        # 4. Choose type if needed
        if cn_type:
            type_option = drawer.get_by_text(cn_type, exact=False)
            if type_option.count() > 0:
                type_option.first.click()
                self.page.wait_for_timeout(500)

        # 5. Add items to Credit Note
        add_items_btn = drawer.get_by_role("button", name="Add items to Credit Note")
        expect(add_items_btn).to_be_visible(timeout=10000)
        add_items_btn.click()
        self.page.wait_for_timeout(1500)

        item_drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last

        # Select Product
        prod_inp = item_drawer.locator("input[placeholder*='Select Product']").first
        prod_inp.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").filter(has_text=product_name).first.click()
        self.page.wait_for_timeout(500)

        # Quantity
        qty_inp = item_drawer.locator("input[placeholder='Enter value']").first
        qty_inp.fill(quantity)
        self.page.wait_for_timeout(500)

        # Click Add in item drawer
        add_btn = item_drawer.get_by_role("button", name="Add")
        expect(add_btn).to_be_enabled()
        add_btn.click(force=True)
        self.page.wait_for_timeout(1500)

        # 6. Submit Credit Note Request
        submit_btn = drawer.get_by_role("button", name="Submit")
        expect(submit_btn).to_be_enabled()
        submit_btn.click()
        self.page.wait_for_timeout(3000)

        return {
            "ref_number": invoice_or_bill_number,
            "against": against,
            "product": product_name,
            "quantity": quantity,
        }

    def request_debit_note(
        self,
        bill_or_invoice_number: str,
        product_name: str,
        quantity: str = "1",
        against: str = "bill",
        dn_type: str = "Returns",
    ) -> dict:
        """Requests a Debit Note against a Purchase Bill or Invoice from the PO detail page."""
        # 1. Navigate to Bills & Invoices -> Debit Notes
        self.page.locator(".q-tab").filter(has_text="Bills & Invoices").first.click()
        self.page.wait_for_timeout(1000)
        self.page.locator(".q-tab").filter(has_text="Debit Notes").first.click()
        self.page.wait_for_timeout(1000)

        # 2. Click Request Debit Note button
        req_btn = self.page.get_by_role("button", name="Request Debit Note")
        expect(req_btn).to_be_visible(timeout=10000)
        req_btn.click()
        self.page.wait_for_timeout(1500)

        drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last

        # 3. Select radio 'Purchase Bill' or 'Invoice'
        if against.lower() in ("invoice", "sales_invoice"):
            drawer.get_by_text("Invoice", exact=False).first.click()
            self.page.wait_for_timeout(500)
            select_inp = drawer.locator("input[placeholder*='Select invoice']").first
        else:
            select_inp = drawer.locator("input[placeholder*='Select purchase bill']").first

        select_inp.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").filter(has_text=bill_or_invoice_number).first.click()
        self.page.wait_for_timeout(1500)

        # 4. Choose type if needed
        if dn_type:
            type_option = drawer.get_by_text(dn_type, exact=False)
            if type_option.count() > 0:
                type_option.first.click()
                self.page.wait_for_timeout(500)

        # 5. Add items to Debit Note
        add_items_btn = drawer.get_by_role("button", name="Add items to Debit Note")
        expect(add_items_btn).to_be_visible(timeout=10000)
        add_items_btn.click()
        self.page.wait_for_timeout(1500)

        item_drawer = self.page.locator(".q-drawer.q-drawer--right:visible").last

        # Select Product
        prod_inp = item_drawer.locator("input[placeholder*='Select Product']").first
        prod_inp.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.locator(".q-menu .q-item").filter(has_text=product_name).first.click()
        self.page.wait_for_timeout(500)

        # Quantity
        qty_inp = item_drawer.locator("input[placeholder='Enter value']").first
        qty_inp.fill(quantity)
        self.page.wait_for_timeout(500)

        # Click Add in item drawer
        add_btn = item_drawer.get_by_role("button", name="Add")
        expect(add_btn).to_be_enabled()
        add_btn.click(force=True)
        self.page.wait_for_timeout(1500)

        # 6. Submit Debit Note Request
        submit_btn = drawer.get_by_role("button", name="Submit")
        expect(submit_btn).to_be_enabled()
        submit_btn.click()
        self.page.wait_for_timeout(3000)

        return {
            "ref_number": bill_or_invoice_number,
            "against": against,
            "product": product_name,
            "quantity": quantity,
        }
