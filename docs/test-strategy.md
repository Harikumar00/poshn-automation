# Test strategy

The suite uses Python Playwright with pytest and Page Object Model.

- Smoke tests cover authenticated dashboard and read-only route health across all discovered internal modules.
- Regression tests cover PO listing/search and required-form validation without submission.
- Authentication uses environment variables and a Playwright storage state at `auth/.auth.json`; the state is ignored by Git.
- Tests use role, label, placeholder, URL, and stable `data-test` selectors. No arbitrary sleeps are used in framework code.
- Destructive/financial workflows are intentionally gated until isolated test data and cleanup contracts are approved.
- HTML and JUnit reports, plus pytest failure output, are written under `reports/`.

