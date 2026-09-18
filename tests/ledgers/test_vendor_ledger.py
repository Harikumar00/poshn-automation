import pytest
from pages.vendor_ledger_page import VendorLedgerPage


@pytest.mark.regression
def test_vendor_ledger_initial_empty_state_and_disabled_controls(vendor_ledger_page: VendorLedgerPage):
    """Verify default empty view, mandatory filter labels, and disabled Generate/More Filters buttons."""
    vendor_ledger_page.assert_initial_state()


@pytest.mark.regression
def test_vendor_ledger_generation_and_table_structure(vendor_ledger_page: VendorLedgerPage):
    """Verify vendor selection, duration choice, enabling of Generate button, and rendered table columns."""
    selected_vendor = vendor_ledger_page.select_vendor()
    assert selected_vendor, "Failed to select vendor from dropdown"

    vendor_ledger_page.select_duration("Financial Year")
    vendor_ledger_page.generate_ledger()

    vendor_ledger_page.assert_table_columns()
    vendor_ledger_page.assert_balance_due_summary()


@pytest.mark.regression
def test_vendor_ledger_more_filters_expansion_post_generation(vendor_ledger_page: VendorLedgerPage):
    """Verify 'More Filters' activates after generation and expands extra filters like Location."""
    vendor_ledger_page.select_vendor()
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
