# Nucleus DEV application map

Discovery was performed against `https://nucleus-dev.poshn.app/` with Playwright in an authenticated Admin session. No business records were created, edited, deleted, approved, or submitted.

## Routes and observed controls

| Area | Route(s) | Observed controls/data |
|---|---|---|
| Home | `/home` | Global search, Create RFQ, Create Order, module links |
| Users | `/users#customers`, `/users#vendors`, `/users#team-members`, `/users/organisations` | Search, filters, Add Customer/Vendor/Team member/Organisation, tables |
| Roles | `/roles-management` | Search, Activity logs, Add New Role, table |
| Catalogue | `/catalogue#products`, `#categories`, `#sub-categories`, `#brands` | Search/filter controls, Add Product/Category/Subcategory/Brand |
| Trade | `/trade/rfqs`, `/trade/vendor-orders` | Search by RFQ/order, status filters, Add RFQ |
| Sales | `/sales/purchase-orders`, `/sales/invoices`, `/sales/proof-of-deliveries`, `/sales/credit-notes`, `/sales/debit-notes` | Search/filter controls, tabular records, PO Create PO |
| Purchases | `/purchases/purchase-bills`, `/purchases/credit-notes`, `/purchases/debit-notes`, `/purchases/payments` | Search/filter controls, Add Purchase Bill, payment request/history |
| Shipping | `/shipping/e-way-bills` | Search by e-way/document number and filters |
| Accounts | `/accounts/invoice-requests`, `/accounts/payment-requests`, `/accounts/receivables`, `/accounts/transactions` | Search/filter controls, reconciliation/transaction controls |
| Reports | `/reports/sales`, `/reports/purchases`, `/reports/receivables`, `/reports/payables` | Request Report and report tables |
| Inbox | `/inbox` | Search name/phone/message and unread checkbox |
| Cashflow | `/cashflow-manager/customer-payments`, `/cashflow-manager/vendor-payments` | Search/filter controls and payment tables |
| Files | `/file-manager` | Search and Add File |
| Utility | `/utility/audit-logs`, `/utility/credit-score-check`, `/utility/ledger-requests`, `/utility/transaction-series`, `/utility/pdf-templates` | Search/filter/date controls and utility actions |
| Analytics | external `https://bi.poshn.app/` | External BI link; not exercised by internal smoke suite |

## Purchase order form discovery

Opening **Create PO** (without submitting) showed required fields: Select Customer, Delivery Type, Payment Terms, Issue Date, Expected Delivery Date, Bill To, Ship To, Account Owner, and at least one item. Optional fields observed: Expiry Date and Associate Agent. The Submit button is disabled until required data and an item are present. Totals show Tax Total and Grand Total.

## Common behaviors

All internal modules use the shared navigation shell, searchable tables, filters, and pagination where records exist. Empty/loaded table states vary by module. The authenticated Admin session exposes all listed navigation groups.

