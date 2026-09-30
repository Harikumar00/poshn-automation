# Business workflows

Phase 2 covers read-only business surfaces and safe validation states in DEV. No seeded records are changed.

| Area | Coverage |
|---|---|
| Customers | list, search, status tabs, add-form required validation, multi-step creation stepper, `In Review` data verification, and Approval / Rejection modal lifecycle |
| Vendors | list, search, filters, add-form required validation |
| Invoices | listing/search/filter discovery and independent line calculation |
| Receivables/ledger | table/search/filter, balance-due parsing, independent closing-balance calculation |
| Credit/debit notes | sales and purchase listing/search/filter |
| Transactions/refunds | account transactions and customer/vendor payment surfaces |
| Purchase orders | listing, pagination, search, create-form required validation and empty-item rule |
| Exports | report/receivable export-control discovery without downloading |

Customer creation, data verification, and approval flow is covered in `tests/customers/test_customer_creation_and_approval_flow.py`.

Trade End-to-End Flow is covered in `tests/trade/test_po_bill_invoice_approval_flow.py`:
- Purchase Order Creation (Customer: `Merabo Labs Private Limited` [`06AAMCM0523D1ZW`], Item: `Aashirvaad atta 10kg*3`, Rate: `"250"`, Qty: `"10"`)
- Purchase Bill Creation & Linking (Vendor: `Payables Vendor` [`07AAUFG7095F1ZT`], Rate: `"200"`, Qty: `"10"`)
- Invoice Request from PO & Accounts E-Invoice Approval
- Proof of Delivery (POD) Entry & Accounts POD Approval (`POD Pending` -> `POD Received` -> `POD Accepted`)
- Credit Note (CN) Request on Sales Invoice & Accounts CN Approval (`/sales/credit-notes` & invoice balance due reconciliation)
- Debit Note (DN) Request on Purchase Bill & Accounts DN Approval (`/purchases/debit-notes`)

*Note on VAS Debit Notes:* The platform features automated Value-Added Services (VAS) debit notes (`VDNSF/...`, type `Services`, remark `#Service_Fee`). Whenever any Purchase Bill is submitted, the backend automatically attaches applicable VAS items (e.g. `Service Fee`, `Test Service Fee - 1`) and generates system-issued debit notes under user `System`. User/test requested debit notes (`DN-...`, type `Returns`) are created independently and verified specifically by note number.
*Data standards:* All entity names, codes, line items, rates, quantities, and document numbers are maintained strictly as strings across page objects, fixtures, and assertions.

Backend REST API Testing is covered in `tests/api/test_core_apis.py`:
- Profile and session verification (`GET /api/core/v1/auth/user`)
- Role authorization and permissions (`GET /api/core/v1/auth/user/roles`)
- Purchase Orders listing and pagination (`GET /api/core/v1/kam/purchase-orders`)
- Sales Invoices listing and pagination (`GET /api/core/v1/kam/invoices`)
- Customers directory with role filter (`GET /api/core/v1/kam/users?roles=buyer`)
- Vendors directory with role filter (`GET /api/core/v1/kam/users?roles=seller`)
- Sales Credit Notes listing (`GET /api/core/v1/sales/credit-notes`)
- Purchases Debit Notes listing (`GET /api/core/v1/purchase/debit-notes`)
- Unauthenticated security guard checks returning HTTP 401 Unauthorized

Ledger Validation & Database Verification is covered in `tests/ledgers/`:
- **Branch Target:** `https://engg-2406.nucleus.te.poshn.app`
- **Vendor Statements (`/ledgers/vendor-ledger`):**
  - Vendor: `Reliance Industries Limited` (`Reliance`)
  - Row-by-row running balance invariant: asserts $\text{Balance}_i = \text{Balance}_{i-1} \pm (\text{Debit}_i - \text{Credit}_i)$ across every rendered table row.
  - Final row balance reconciliation against the summary `Balance Due` card.
  - **Read-Only Database Verification:** Uses `ReadOnlyMongoClient` (strictly bounded `find()` with projection, zero mutation methods) to query and reconcile MongoDB `Ledgers`/`Bills` vouchers against UI data.
- **Customer Receivables (`/accounts/receivables`):**
  - Customer: `Bajaj Holdings And Investment Limited` (`Bajaj`)
  - Row-by-row balance due validation: $\text{Balance Due} \le \text{Amount}$ and both non-negative.
  - Strictly read-only MongoDB database verification reconciling customer documents.
- **Data Standards:** All entity names, vouchers, numbers, debits, credits, and balances are handled strictly as strings.
