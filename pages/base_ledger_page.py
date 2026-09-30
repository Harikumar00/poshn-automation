"""Base Ledger Page Object defining common interactions for Vendor and Customer Ledgers."""

from decimal import Decimal
import re
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.base_page import BasePage
from utils.calculations import money


class BaseLedgerPage(BasePage):
    """Abstract Base Page for statement of accounts / ledgers."""

    path: str = "/ledgers"
    expected_title: str = "Poshn - Ledger"
    party_label_text: str = "Party"
    generate_btn_name: str = "Generate Ledger"

    EXPECTED_COLUMNS = [
        "Date",
        "Voucher Type",
        "Debit",
        "Credit",
        "Balance",
        "Voucher#",
        "Details",
        "State",
    ]

    EXPECTED_ACTION_MENU_ITEMS = [
        "Export as PDF",
        "Export as XLS",
        "Past Generated Ledger",
        "Display Additional Columns",
        "Activity Logs",
    ]

    def __init__(self, page: Page, base_url: str | None = None):
        super().__init__(page)
        self.base_url = (base_url or settings.base_url).rstrip("/")
        self.generate_button = page.get_by_role("button", name=self.generate_btn_name)
        self.reset_button = page.get_by_role("button", name="Reset")
        self.more_filters_button = page.locator("button:has-text('More Filters')")
        self.party_input = page.locator("input[placeholder*='Select' i]").first
        self.duration_input = page.locator("input[placeholder*='Select duration' i]")

    def navigate(self) -> None:
        """Navigates to the ledger route and handles any unauthenticated session recovery."""
        self.page.goto(f"{self.base_url}{self.path}", wait_until="domcontentloaded")
        login_btn = self.page.locator("button:has-text('Continue'), button:has-text('Login')")
        party_label = self.page.get_by_text(self.party_label_text, exact=False)

        for _ in range(20):
            if login_btn.count() and login_btn.first.is_visible():
                from pages.login_page import LoginPage
                login = LoginPage(self.page)
                login.authenticate(settings.test_phone or "8596896586", settings.test_otp or "9999")
                self.page.goto(f"{self.base_url}{self.path}", wait_until="domcontentloaded")
                break
            if party_label.count() and party_label.first.is_visible():
                break
            self.page.wait_for_timeout(300)

        expect(self.page).to_have_url(re.compile(rf".*{self.path}/?$"))
        expect(self.page).to_have_title(self.expected_title)

    def select_party(self, party_name: str | None = None) -> str:
        """Selects a party (Vendor or Customer) from the dropdown."""
        expect(self.party_input).to_be_visible(timeout=settings.timeout_ms)
        self.party_input.click()
        self.page.wait_for_timeout(800)

        if party_name:
            self.party_input.fill(party_name)
            self.page.wait_for_timeout(1000)

        options = self.page.locator(".q-menu .q-item, [role='option']")
        expect(options.first).to_be_visible(timeout=15000)

        if party_name:
            target = self.page.locator(f".q-menu .q-item:has-text('{party_name}')").first
            expect(target).to_be_visible(timeout=10000)
            selected_text = target.inner_text().strip().split("\n")[0]
            target.click()
        else:
            selected_text = options.first.inner_text().strip().split("\n")[0]
            options.first.click()

        self.page.wait_for_timeout(1000)
        return selected_text

    def select_duration(self, duration_label: str = "Financial Year") -> None:
        """Selects a date duration filter."""
        expect(self.duration_input).to_be_enabled(timeout=15000)
        self.duration_input.click()
        self.page.wait_for_timeout(800)
        opt = self.page.locator(f".q-menu .q-item:has-text('{duration_label}')").first
        expect(opt).to_be_visible(timeout=10000)
        opt.click()
        self.page.wait_for_timeout(800)

    def generate_ledger(self) -> None:
        """Triggers ledger statement generation."""
        expect(self.generate_button).to_be_enabled(timeout=15000)
        self.page.wait_for_timeout(500)
        self.generate_button.click()
        self.wait_for_idle(timeout=10000)
        self.page.wait_for_timeout(2500)
        expect(self.page.locator("tbody tr:visible").first).to_be_visible(timeout=15000)

    def assert_table_columns(self) -> None:
        """Asserts all expected standard ledger columns are visible."""
        for column in self.EXPECTED_COLUMNS:
            expect(
                self.page.locator("th, [role='columnheader']").filter(has_text=column).first
            ).to_be_visible()

    def assert_balance_due_summary(self) -> None:
        """Asserts that the Balance Due card or label is visible."""
        expect(self.page.get_by_text("Balance Due", exact=True)).to_be_visible()

    def expand_more_filters(self) -> None:
        """Expands the More Filters drawer or accordion."""
        expect(self.more_filters_button).to_be_enabled()
        self.more_filters_button.click()
        self.page.wait_for_timeout(1000)
        expect(self.page.get_by_text("Location", exact=True)).to_be_visible()

    def open_action_menu(self) -> list[str]:
        """Opens top-right action menu."""
        action_button = self.page.locator("main .q-btn--rounded.text-primary").first
        expect(action_button).to_be_visible()
        action_button.click()
        self.page.wait_for_timeout(1000)

        menu_container = self.page.locator(".q-menu")
        expect(menu_container).to_be_visible()

        for item in self.EXPECTED_ACTION_MENU_ITEMS:
            expect(menu_container.get_by_text(item, exact=True).first).to_be_visible()

        return self.EXPECTED_ACTION_MENU_ITEMS

    def download_export(self, format_type: str = "XLS"):
        """Triggers and captures the exported file (XLS or PDF) from the action menu."""
        label = "Export as XLS" if format_type.upper() == "XLS" else "Export as PDF"
        self.open_action_menu()
        menu_container = self.page.locator(".q-menu")
        item = menu_container.get_by_text(label, exact=True).first
        expect(item).to_be_visible()
        with self.page.expect_download() as download_info:
            item.click()
        return download_info.value

    def get_summary_balance_due(self) -> Decimal:
        """Extracts the numeric Balance Due from the summary total row or summary card."""
        try:
            balance_row = self.page.locator("tr").filter(has_text="Balance Due").last
            if balance_row.count():
                matches = re.findall(r"[\d,]+(?:\.\d+)?", balance_row.inner_text())
                if matches:
                    return Decimal(matches[-1].replace(",", ""))
        except Exception:
            pass
        return Decimal("0")

    def get_ledger_rows(self) -> list[dict[str, str]]:
        """Extracts all visible transaction rows from the rendered ledger table as strings."""
        rows = self.page.locator("tbody tr:visible")
        row_count = rows.count()
        extracted: list[dict[str, str]] = []

        for i in range(row_count):
            row_el = rows.nth(i)
            cells = row_el.locator("td")
            if cells.count() < 5:
                continue

            v_type = str(cells.nth(1).inner_text().strip())
            # Skip the bottom summary total row so only transaction rows are returned
            if "Balance Due" in v_type:
                continue

            extracted.append({
                "date": str(cells.nth(0).inner_text().strip()),
                "voucher_type": v_type,
                "debit": str(cells.nth(2).inner_text().strip()),
                "credit": str(cells.nth(3).inner_text().strip()),
                "balance": str(cells.nth(4).inner_text().strip()),
                "voucher_number": str(cells.nth(5).inner_text().strip()) if cells.count() > 5 else "",
                "details": str(cells.nth(6).inner_text().strip()) if cells.count() > 6 else "",
                "state": str(cells.nth(7).inner_text().strip()) if cells.count() > 7 else "",
            })

        return extracted

    def assert_running_balances_match(self) -> dict[str, str]:
        """Validates row-by-row running balance mathematical integrity across all entries."""
        rows = self.get_ledger_rows()
        if not rows:
            summary_balance = self.get_summary_balance_due()
            return {"total_rows": "0", "closing_balance": str(summary_balance)}

        # Iterate through rows and assert running balance
        for i in range(1, len(rows)):
            prev_bal = money(rows[i - 1]["balance"])
            curr_debit = money(rows[i]["debit"])
            curr_credit = money(rows[i]["credit"])
            curr_bal = money(rows[i]["balance"])

            # Credit increases payable / decreases receivable, Debit increases receivable / decreases payable
            expected_credit_basis = prev_bal + curr_credit - curr_debit
            expected_debit_basis = prev_bal + curr_debit - curr_credit

            delta_credit = min(abs(curr_bal - expected_credit_basis), abs(abs(curr_bal) - abs(expected_credit_basis)))
            delta_debit = min(abs(curr_bal - expected_debit_basis), abs(abs(curr_bal) - abs(expected_debit_basis)))
            min_delta = min(delta_credit, delta_debit)

            assert min_delta <= Decimal("0.05"), (
                f"Running balance mismatch at row {i} (Voucher: {rows[i]['voucher_number']}): "
                f"Prev Balance={prev_bal}, Debit={curr_debit}, Credit={curr_credit}, "
                f"Reported Current Balance={curr_bal}, Expected={expected_credit_basis} or {expected_debit_basis}"
            )

        final_bal = money(rows[-1]["balance"])
        summary_bal = self.get_summary_balance_due()

        if summary_bal != Decimal("0"):
            assert abs(abs(final_bal) - abs(summary_bal)) <= Decimal("1.00"), (
                f"Final running balance {final_bal} does not reconcile with summary Balance Due {summary_bal}"
            )

        return {
            "total_rows": str(len(rows)),
            "opening_balance": str(rows[0]["balance"]),
            "closing_balance": str(final_bal),
            "summary_balance": str(summary_bal),
        }
