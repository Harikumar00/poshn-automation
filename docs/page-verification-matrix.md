# Page verification matrix

Verified from the authenticated DEV UI using Playwright snapshots. Route tests assert scoped URL, title, visible main content, and a page identity token; dedicated page objects add control/table assertions.

| Page | URL | Title | Heading/content identity | Page-specific content | Verified |
|---|---|---|---|---|---|
| Home | `/home` | Poshn - Home | RFQ/Order dashboard | Create RFQ, Create Order | Yes |
| Customers | `/users#customers` | Poshn - Users | Customers | search, status filter, tabs, customer table, Add Customer | Yes |
| Vendors | `/users#vendors` | Poshn - Users | Vendors | search, status filter, tabs, vendor table, Add Vendor | Yes |
| Purchase Orders | `/sales/purchase-orders` | Poshn - Purchase Orders | Purchase Orders | Create PO, Status table column, pagination | Yes |
| Invoices | `/sales/invoices` | Poshn - Invoices | Invoices | listing/search/filter surface | Yes |
| Receivables | `/accounts/receivables` | Poshn - Receivables | Receivables | search, filters, balance-due table | Yes |
| Credit/Debit Notes | `/sales/*-notes`, `/purchases/*-notes` | Poshn - Credit/Debit Notes | note listing | search/filter surfaces | Yes |
| Transactions | `/accounts/transactions` | Poshn - Transactions | Transactions | listing/search/filter surface | Yes |
| Reports | `/reports/sales` | Poshn - Reports | Reports | report table and Request Report | Yes |
| Remaining modules | documented in `tests/smoke/test_navigation.py` | Poshn - * | route-specific identity token | main content and controls | Yes |
