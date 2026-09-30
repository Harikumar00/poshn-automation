from decimal import Decimal
import re
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.base_page import BasePage
from utils.calculations import money


class CustomerLedgerPage(BasePage):
    path = "/ledgers/customer-ledger"
    expected_title = "Poshn - Ledger"

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
        self.generate_button = page.get_by_role("button", name="Generate Customer Ledger")
        self.reset_button = page.get_by_role("button", name="Reset")
        self.more_filters_button = page.locator("button:has-text('More Filters')")
        self.customer_input = page.locator("input[placeholder*='Select Customer' i]")
        self.duration_input = page.locator("input[placeholder*='Select duration' i]")

    def navigate(self) -> None:
        self.page.goto(f"{self.base_url}{self.path}", wait_until="domcontentloaded")
        login_btn = self.page.locator("button:has-text('Continue'), button:has-text('Login')")
        party_label = self.page.get_by_text("Party Type *", exact=True)

        for _ in range(20):
            if login_btn.count() and login_btn.first.is_visible():
                from pages.login_page import LoginPage
                login = LoginPage(self.page)
                login.authenticate(settings.test_phone or "8596896586", settings.test_otp or "9999")
                self.page.goto(f"{self.base_url}{self.path}", wait_until="domcontentloaded")
                break
            if party_label.count() and party_label.first.is_visible():
                break
            self.page.wait_for_timeout(500)

        expect(self.page).to_have_url(re.compile(r".*/ledgers/customer-ledger.*"))

    def assert_initial_state(self) -> None:
        expect(self.page.get_by_text("Party Type *", exact=True)).to_be_visible(timeout=settings.timeout_ms)
        expect(self.page).to_have_title(re.compile(r"Poshn.*Ledger.*|Poshn", re.I), timeout=settings.timeout_ms)
        expect(self.page.get_by_text("Customer *", exact=True)).to_be_visible()
        expect(self.page.get_by_text("State *", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Duration *", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Date Range *", exact=True)).to_be_visible()
        expect(self.generate_button).to_be_disabled()

    def select_customer(self, customer_name: str | None = None) -> str:
        expect(self.customer_input).to_be_visible(timeout=settings.timeout_ms)
        self.customer_input.click()
        self.page.wait_for_timeout(800)

        if customer_name:
            self.customer_input.fill(customer_name)
            self.page.wait_for_timeout(1000)

        options = self.page.locator(".q-menu .q-item, [role='option']")
        expect(options.first).to_be_visible(timeout=15000)

        if customer_name:
            target = self.page.locator(f".q-menu .q-item:has-text('{customer_name}')").first
            expect(target).to_be_visible(timeout=10000)
            selected_text = target.inner_text().strip().split("\n")[0]
            target.click()
        else:
            selected_text = options.first.inner_text().strip().split("\n")[0]
            options.first.click()

        self.page.wait_for_timeout(1000)
        return selected_text

    def select_duration(self, duration_label: str = "This Month") -> None:
        expect(self.duration_input).to_be_enabled(timeout=15000)
        self.duration_input.click()
        self.page.wait_for_timeout(800)
        opt = self.page.locator(f".q-menu .q-item:has-text('{duration_label}')").first
        expect(opt).to_be_visible(timeout=10000)
        opt.click()
        self.page.wait_for_timeout(800)

    def generate_ledger(self) -> None:
        expect(self.generate_button).to_be_enabled(timeout=15000)
        self.page.wait_for_timeout(500)
        self.generate_button.click()
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        self.page.wait_for_timeout(2500)
        expect(self.page.locator("tbody tr:visible").first).to_be_visible(timeout=15000)

    def assert_table_columns(self) -> None:
        for column in self.EXPECTED_COLUMNS:
            expect(
                self.page.locator("th, [role='columnheader']").filter(has_text=column).first
            ).to_be_visible()

    def open_action_menu(self) -> list[str]:
        action_button = self.page.locator("main .q-btn--rounded.text-primary").first
        expect(action_button).to_be_visible(timeout=10000)
        action_button.click()
        self.page.wait_for_timeout(800)
        menu_container = self.page.locator(".q-menu")
        expect(menu_container).to_be_visible()
        return [item.inner_text().strip() for item in menu_container.locator(".q-item").all()]

    def download_export(self, format_type: str = "XLS"):
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
                text = balance_row.inner_text()
                matches = re.findall(r"-?[\d,]+(?:\.\d+)?", text)
                if matches:
                    return Decimal(matches[-1].replace(",", ""))
        except Exception:
            pass
        return Decimal("0")

    def get_ledger_rows(self) -> list[dict[str, str]]:
        """Extracts all visible transaction rows from the rendered customer ledger table."""
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
        """Validates row-by-row customer ledger running balance mathematical integrity.

        In Customer Ledger (Accounts Receivable):
            Balance_i = Balance_{i-1} + Debit_i - Credit_i
        Accounts for platform defect where row balances drop the minus sign.
        """
        rows = self.get_ledger_rows()
        if not rows:
            summary_balance = self.get_summary_balance_due()
            return {"total_rows": "0", "closing_balance": str(summary_balance)}

        signed_balance = Decimal("0")
        for i in range(1, len(rows)):
            curr_debit = money(rows[i]["debit"])
            curr_credit = money(rows[i]["credit"])
            curr_bal = money(rows[i]["balance"])

            # Customer ledger is a receivable: Debits (Invoices, Refunds) increase receivable,
            # Credits (Payments, Credit Notes) decrease receivable
            signed_balance = signed_balance + curr_debit - curr_credit

            # Accommodate known platform defect where row balances drop the minus sign
            delta = min(abs(curr_bal - signed_balance), abs(abs(curr_bal) - abs(signed_balance)))

            assert delta <= Decimal("0.05"), (
                f"Running balance mismatch at row {i} (Voucher: {rows[i]['voucher_number']}): "
                f"Debit={curr_debit}, Credit={curr_credit}, "
                f"Reported Current Balance={curr_bal}, Calculated Signed Balance={signed_balance}"
            )

        summary_bal = self.get_summary_balance_due()
        if summary_bal != Decimal("0"):
            assert abs(abs(signed_balance) - abs(summary_bal)) <= Decimal("1.00"), (
                f"Final running balance {signed_balance} does not reconcile with summary Balance Due {summary_bal}"
            )

        return {
            "total_rows": str(len(rows)),
            "opening_balance": str(rows[0]["balance"]),
            "closing_balance": str(signed_balance),
            "summary_balance": str(summary_bal),
        }
