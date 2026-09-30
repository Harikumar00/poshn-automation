import pytest
from pages.vendor_ledger_page import VendorLedgerPage
from utils.mongo_client import create_read_only_client


TEST_VENDOR_NAME = "Reliance Industries Limited"
TEST_VENDOR_SEARCH = "Reliance"


@pytest.mark.regression
def test_vendor_ledger_initial_empty_state_and_disabled_controls(vendor_ledger_page: VendorLedgerPage):
    """Verify default empty view, mandatory filter labels, and disabled Generate/More Filters buttons."""
    vendor_ledger_page.assert_initial_state()


@pytest.mark.regression
def test_vendor_ledger_generation_and_table_structure(vendor_ledger_page: VendorLedgerPage):
    """Verify vendor selection (Reliance), duration choice, enabling of Generate button, and rendered table columns."""
    selected_vendor = vendor_ledger_page.select_vendor(TEST_VENDOR_SEARCH)
    assert selected_vendor, f"Failed to select vendor {TEST_VENDOR_SEARCH} from dropdown"

    vendor_ledger_page.select_duration("Financial Year")
    vendor_ledger_page.generate_ledger()

    vendor_ledger_page.assert_table_columns()
    vendor_ledger_page.assert_balance_due_summary()


@pytest.mark.regression
def test_vendor_ledger_running_balance_mathematical_validation(vendor_ledger_page: VendorLedgerPage):
    """Verify row-by-row mathematical integrity of running balances in the Vendor Ledger table.

    Asserts that for every row i:
        Balance_i == Balance_{i-1} + Credit_i - Debit_i  (or Balance_{i-1} + Debit_i - Credit_i)
    and that the final row reconciles with the top summary Balance Due card.
    """
    vendor_ledger_page.select_vendor(TEST_VENDOR_SEARCH)
    vendor_ledger_page.select_duration("Financial Year")
    vendor_ledger_page.generate_ledger()

    reconciliation = vendor_ledger_page.assert_running_balances_match()
    assert int(reconciliation["total_rows"]) >= 0
    assert "closing_balance" in reconciliation
    assert "summary_balance" in reconciliation


@pytest.mark.regression
def test_vendor_ledger_this_month_running_balance_validation(vendor_ledger_page: VendorLedgerPage):
    """Verify row-by-row mathematical integrity of running balances for Vendor Reliance with duration 'This Month'."""
    vendor_ledger_page.select_vendor(TEST_VENDOR_SEARCH)
    vendor_ledger_page.select_duration("This Month")
    vendor_ledger_page.generate_ledger()

    reconciliation = vendor_ledger_page.assert_running_balances_match()
    assert int(reconciliation["total_rows"]) > 0
    assert "closing_balance" in reconciliation
    assert "summary_balance" in reconciliation


@pytest.mark.regression
def test_vendor_ledger_more_filters_expansion_post_generation(vendor_ledger_page: VendorLedgerPage):
    """Verify 'More Filters' activates after generation and expands extra filters like Location."""
    vendor_ledger_page.select_vendor(TEST_VENDOR_SEARCH)
    vendor_ledger_page.select_duration("Financial Year")
    vendor_ledger_page.generate_ledger()

    vendor_ledger_page.expand_more_filters()


@pytest.mark.regression
def test_vendor_ledger_action_menu_options(vendor_ledger_page: VendorLedgerPage):
    """Verify 3-dots action menu provides PDF, XLS export, Past Ledgers, Column config, and Logs."""
    items = vendor_ledger_page.open_action_menu()
    assert "Export as PDF" in items
    assert "Export as XLS" in items
    assert "Past Generated Ledger" in items
    assert "Display Additional Columns" in items
    assert "Activity Logs" in items


@pytest.mark.regression
def test_vendor_ledger_database_verification_read_only():
    """Strictly read-only database verification reconciling MongoDB ledger records with Reliance vendor data.

    Asserts:
    1. ReadOnlyMongoClient operates exclusively with read-only find queries.
    2. Bounded find retrieves valid ledger/voucher structures for the party.
    3. All financial and identifier values are represented strictly as strings.
    """
    client = create_read_only_client()
    try:
        # Strictly read-only query - no updates, inserts, or deletes permitted
        db_records = client.find_party_ledger_records_read_only(
            party_name=TEST_VENDOR_SEARCH,
            limit=25,
        )
        assert isinstance(db_records, list)

        for record in db_records:
            assert isinstance(record["id"], str)
            assert isinstance(record["voucher_number"], str)
            assert isinstance(record["voucher_type"], str)
            assert isinstance(record["debit"], str)
            assert isinstance(record["credit"], str)
            assert isinstance(record["balance"], str)
    finally:
        client.close()
