# Automation status

## Latest execution

Framework scaffold and test files are implemented and the complete suite has been executed against Nucleus DEV. The final run reused the securely stored Playwright auth state.

- Total tests implemented: 56 (32 smoke, 19 regression, 5 calculation/default-marker checks)
- Latest full run: 55 passed, 1 skipped
- Failed: 0
- Skipped/blocked: 1 (valid-login is intentionally skipped when credentials are not supplied; it passes with secure environment values)
- Modules covered: Home, Users, Roles Management, Catalogue, Trade, Sales, Purchases, Shipping, Accounts, Reports, Inbox, Cashflow Manager, File Manager, Utility
- Known application defects: none confirmed by this suite
- Known environment issues: DEV emitted an unauthenticated session-refresh 401 during discovery; OneSignal also reports a stage-environment mismatch. External Analytics is outside the internal smoke scope.
- Flaky tests: none observed; execution still required
- Remaining gaps: UI creation/edit/persistence, refund ledger impact, file-content downloads, negative OTP scenarios, and external Analytics require dedicated non-production fixtures/data
- Page verification: all 32 smoke routes now assert scoped URL, title, and route-specific main-content identity; dedicated page objects verify controls and tables for business modules.
