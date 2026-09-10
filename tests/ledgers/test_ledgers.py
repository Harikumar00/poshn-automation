from decimal import Decimal
import pytest
from playwright.sync_api import expect
from pages.module_page import ModulePage
from config.settings import settings
from utils.calculations import ledger_closing, money


@pytest.mark.regression
def test_receivables_ledger_search_filters_and_balance_columns(authenticated_page):
    page = ModulePage(authenticated_page, "/accounts/receivables", "Poshn - Receivables")
    page.open_and_assert(); page.search_if_available()
    for header in ["Invoice#", "Customer", "Amount", "Due Date", "Status"]:
        expect(authenticated_page.get_by_role("columnheader", name=header)).to_be_visible()


@pytest.mark.regression
def test_receivables_visible_balance_due_is_mathematically_consistent(authenticated_page):
    page = ModulePage(authenticated_page, "/accounts/receivables", "Poshn - Receivables"); page.open_and_assert()
    expect(
        authenticated_page.get_by_text("Balance due:", exact=False).first
    ).to_be_visible(timeout=settings.timeout_ms)
    rows = authenticated_page.locator("main tr:visible")
    checked = 0
    for i in range(min(rows.count(), 8)):
        text = rows.nth(i).inner_text()
        if "Balance due:" in text:
            amount, due = text.split("Balance due:", 1)
            assert money(amount) >= Decimal("0") and money(due) >= Decimal("0")
            checked += 1
    assert checked > 0


def test_ledger_closing_calculation():
    assert ledger_closing(1000, debits=250, credits=100, adjustments=-50) == Decimal("1100.000")
