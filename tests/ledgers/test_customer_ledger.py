import pytest
from pages.customer_ledger_page import CustomerLedgerPage


TEST_CUSTOMER_NAME = "Bajaj Holdings And Investment Limited"
TEST_CUSTOMER_SEARCH = "Bajaj Holdings"


@pytest.mark.regression
def test_customer_ledger_initial_empty_state_and_disabled_controls(customer_ledger_page: CustomerLedgerPage):
    """Verify default empty view, mandatory filter labels, and disabled Generate button."""
    customer_ledger_page.assert_initial_state()


@pytest.mark.regression
def test_customer_ledger_this_month_generation_and_table_structure(customer_ledger_page: CustomerLedgerPage):
    """Verify customer selection (Bajaj), duration choice (This Month), and rendered table columns."""
    selected_customer = customer_ledger_page.select_customer(TEST_CUSTOMER_SEARCH)
    assert selected_customer, f"Failed to select customer {TEST_CUSTOMER_SEARCH} from dropdown"

    customer_ledger_page.select_duration("This Month")
    customer_ledger_page.generate_ledger()

    customer_ledger_page.assert_table_columns()


@pytest.mark.regression
def test_customer_ledger_this_month_running_balance_mathematical_validation(customer_ledger_page: CustomerLedgerPage):
    """Verify row-by-row mathematical integrity of running balances for Customer Bajaj with duration 'This Month'.

    Asserts that for every row i:
        Balance_i == Balance_{i-1} + Debit_i - Credit_i
    and that the final row reconciles with the summary Balance Due card/row.
    """
    customer_ledger_page.select_customer(TEST_CUSTOMER_SEARCH)
    customer_ledger_page.select_duration("This Month")
    customer_ledger_page.generate_ledger()

    reconciliation = customer_ledger_page.assert_running_balances_match()
    assert int(reconciliation["total_rows"]) > 0
    assert "closing_balance" in reconciliation
    assert "summary_balance" in reconciliation
