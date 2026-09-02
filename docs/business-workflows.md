# Business workflows

Phase 2 covers read-only business surfaces and safe validation states in DEV. No seeded records are changed.

| Area | Coverage |
|---|---|
| Customers | list, search, status tabs, add-form required validation |
| Vendors | list, search, filters, add-form required validation |
| Invoices | listing/search/filter discovery and independent line calculation |
| Receivables/ledger | table/search/filter, balance-due parsing, independent closing-balance calculation |
| Credit/debit notes | sales and purchase listing/search/filter |
| Transactions/refunds | account transactions and customer/vendor payment surfaces |
| Purchase orders | listing, pagination, search, create-form required validation and empty-item rule |
| Exports | report/receivable export-control discovery without downloading |

UI creation/edit/persistence, refund ledger impact, and file-content downloads require a disposable tenant and supported cleanup/API contract; shared seeded DEV data is intentionally not mutated.
