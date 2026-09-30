# Automation status

## Latest execution

Framework scaffold and test files are implemented and the complete suite has been executed against Nucleus DEV. The final run reused the securely stored Playwright auth state.

- Total tests implemented: 163 (32 smoke, 107 regression, 9 backend REST API, 5 calculation/default-marker checks, 4 specialized suite checks, 6 trade end-to-end lifecycle checks)
- PDF Templates complete specification suite: Implemented in `tests/pdf_templates/` (76 tests across 8 modules + pre-conditions: API security, list view UI, add drawer, reference PDF uploads, in-use exclusivity invariants, template designer canvas & dynamic tokens, series rule numbering, view/edit lifecycle workflows) supported by `pages/pdf_templates_page.py`. *In development status: collected and statically compiled with zero execution pending user go-ahead.*
- Export reconciliation & download flows: Implemented in `tests/exports/test_exports.py` using `utils/export_parser.py` (PDF and XLSX parsers) and `pages/vendor_ledger_page.py`. Validates export downloads and reconciles data points across formats. Identified critical backend bug where XLSX vendor exports invert/swap billed and paid summary cards and use customer terminology.
- Ledger running balance & DB reconciliation: Complete implementation in `tests/ledgers/test_vendor_ledger.py` and `tests/ledgers/test_ledgers.py` validating row-by-row mathematical running balance invariants for vendor Reliance (`Reliance Industries Limited`) on branch `https://engg-2406.nucleus.te.poshn.app` and customer Bajaj (`Bajaj Holdings And Investment Limited`), backed by strictly read-only MongoDB database reconciliation (`ReadOnlyMongoClient`).
- Backend REST API flow: Complete API coverage implemented in `tests/api/test_core_apis.py` covering authenticated profile, user roles, purchase orders, sales invoices, buyers/customers, sellers/vendors, sales credit notes, purchases debit notes, and 401 unauthorized security guards.
- Customer lifecycle flow: Full end-to-end coverage implemented in `tests/customers/test_customer_creation_and_approval_flow.py` covering multi-step creation stepper, data verification in `In Review` tab, Customer Details profile verification, and Approval / Rejection modal flows.
- Trade lifecycle flow: Complete end-to-end coverage implemented in `tests/trade/test_po_bill_invoice_approval_flow.py` covering:
  1. PO creation (Customer: `Merabo Labs Private Limited` [`06AAMCM0523D1ZW`], Item: `Aashirvaad atta 10kg*3`, Rate: `"250"`, Qty: `"10"`)
  2. Purchase Bill creation & linking (Vendor: `Payables Vendor` [`07AAUFG7095F1ZT`], Rate: `"200"`, Qty: `"10"`)
  3. Invoice request & accounts E-invoice approval (`POD Pending`, verified in `/sales/invoices`)
  4. POD entry & accounts POD approval (`POD Accepted`, verified in `/sales/invoices`)
  5. Credit Note request on Invoice & accounts CN approval (`/sales/credit-notes`, invoice credit reconciliation)
  6. Debit Note request on Purchase Bill & accounts DN approval (`/purchases/debit-notes`)
  *All party names, identifiers, line items, rates, quantities, and document numbers are maintained strictly as strings.*

- Latest run: 80 passed cleanly in DEV (including 9/9 API tests and 6/6 trade stages)


- Modules covered: Home, Users, Roles Management, Catalogue, Trade, Sales, Purchases, Shipping, Accounts, Reports, Inbox, Cashflow Manager, File Manager, Utility
- Known application defects: none confirmed by this suite
- Known environment issues: DEV emitted an unauthenticated session-refresh 401 during discovery; OneSignal also reports a stage-environment mismatch. External Analytics is outside the internal smoke scope.
- Page verification: all 32 smoke routes assert scoped URL, title, and route-specific main-content identity; dedicated page objects verify controls and tables for business modules.
