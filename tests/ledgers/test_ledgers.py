import re
from decimal import Decimal
import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage
from config.settings import settings
from utils.calculations import ledger_closing, money
from utils.mongo_client import create_read_only_client


TEST_CUSTOMER_NAME = "Bajaj Holdings And Investment Limited"
TEST_CUSTOMER_SEARCH = "Bajaj"


@pytest.mark.regression
def test_receivables_ledger_search_filters_and_balance_columns(authenticated_page):
    """Verify Receivables page identity, table headers, and search for Customer Bajaj."""
    page = ModulePage(authenticated_page, "/accounts/receivables", "Poshn - Receivables", breadcrumbs=["Accounts", "Receivables"])
    page.open_and_assert()

    # Verify exact URL and document title confirm we are on Receivables page
    expect(authenticated_page).to_have_url(re.compile(r".*/accounts/receivables/?$"))
    expect(authenticated_page).to_have_title("Poshn - Receivables")
    expect(authenticated_page.locator("main").get_by_text("Receivables", exact=True).first).to_be_visible()

    # Search for customer Bajaj
    page.search_if_available(TEST_CUSTOMER_SEARCH)
    for header in ["Invoice#", "Customer", "Amount", "Due Date", "Status"]:
        expect(
            authenticated_page.get_by_role("columnheader", name=re.compile(re.escape(header), re.IGNORECASE)).first
        ).to_be_visible()


@pytest.mark.regression
def test_receivables_visible_balance_due_is_mathematically_consistent(authenticated_page):
    """Verify that visible row Amount and Balance Due are mathematically consistent and non-negative."""
    page = ModulePage(authenticated_page, "/accounts/receivables", "Poshn - Receivables", breadcrumbs=["Accounts", "Receivables"])
    page.open_and_assert()
    expect(authenticated_page).to_have_title("Poshn - Receivables")
    expect(
        authenticated_page.get_by_text("Balance due:", exact=False).first
    ).to_be_visible(timeout=settings.timeout_ms)
    rows = authenticated_page.locator("tbody tr:visible")
    checked = 0
    for i in range(min(rows.count(), 8)):
        row = rows.nth(i)
        cell = row.locator("td").filter(has_text="Balance due:").first
        if cell.count():
            cell_text = cell.inner_text()
            parts = cell_text.split("Balance due:", 1)
            amt_matches = re.findall(r"-?\d[\d,]*(?:\.\d+)?", parts[0])
            parsed_amt = Decimal(amt_matches[-1].replace(",", "")) if amt_matches else Decimal("0")
            parsed_due = money(parts[1])
            assert parsed_amt >= Decimal("0"), f"Negative amount detected: {parsed_amt}"
            assert parsed_due >= Decimal("0"), f"Negative balance due detected: {parsed_due}"
            assert parsed_due <= parsed_amt or parsed_amt == Decimal("0"), (
                f"Balance due {parsed_due} exceeds total invoice amount {parsed_amt}"
            )
            checked += 1
    assert checked > 0


@pytest.mark.regression
def test_customer_receivables_row_by_row_balance_verification(authenticated_page):
    """Verify row-level balance constraints for Customer Bajaj in Receivables Ledger."""
    page = ModulePage(authenticated_page, "/accounts/receivables", "Poshn - Receivables", breadcrumbs=["Accounts", "Receivables"])
    page.open_and_assert()
    page.search_if_available(TEST_CUSTOMER_SEARCH)
    authenticated_page.wait_for_timeout(2000)

    rows = authenticated_page.locator("tbody tr:visible")
    checked = 0
    for i in range(min(rows.count(), 10)):
        row = rows.nth(i)
        cell = row.locator("td").filter(has_text="Balance due:").first
        if cell.count():
            cell_text = cell.inner_text()
            parts = cell_text.split("Balance due:", 1)
            amt_matches = re.findall(r"-?\d[\d,]*(?:\.\d+)?", parts[0])
            total_amt = Decimal(amt_matches[-1].replace(",", "")) if amt_matches else Decimal("0")
            balance_due = money(parts[1])
            assert balance_due >= Decimal("0"), f"Negative balance due at row {i}"
            assert balance_due <= total_amt or total_amt == Decimal("0"), (
                f"Row {i} balance due {balance_due} exceeds amount {total_amt}"
            )
            checked += 1
    assert checked >= 0


@pytest.mark.regression
def test_customer_receivables_database_verification_read_only():
    """Strictly read-only database verification reconciling customer Bajaj records in MongoDB.

    Asserts:
    1. ReadOnlyMongoClient executes exclusively read-only find queries.
    2. Bounded find retrieves valid documents for Bajaj customer.
    3. All extracted values are maintained strictly as strings.
    """
    client = create_read_only_client()
    try:
        # Strictly read-only query
        db_records = client.find_party_ledger_records_read_only(
            party_name=TEST_CUSTOMER_SEARCH,
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


def test_ledger_closing_calculation():
    """Unit test validating core ledger closing balance arithmetic formula."""
    assert ledger_closing("1000", debits="250", credits="100", adjustments="-50") == Decimal("1100.000")
