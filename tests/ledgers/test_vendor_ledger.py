import os
from pathlib import Path
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, expect

from config.settings import ROOT, settings
from pages.login_page import LoginPage
from pages.vendor_ledger_page import VendorLedgerPage

TARGET_URL = os.getenv("VENDOR_LEDGER_URL", "https://engg-2406.nucleus.te.poshn.app")
AUTH_FILE = ROOT / "auth" / ".auth_engg_2406.json"


@pytest.fixture(scope="module")
def vendor_ledger_context(browser: Browser) -> BrowserContext:
    """Provides an authenticated browser context for the engg-2406 DEV/Staging environment."""
    ctx_kwargs = {"base_url": TARGET_URL}
    scratch_auth = Path("/Users/hari/.gemini/antigravity-cli/brain/1e325c61-0c95-4425-8d34-bc86da39afe8/scratch/auth_vendor_ledger.json")

    if AUTH_FILE.exists():
        ctx_kwargs["storage_state"] = str(AUTH_FILE)
    elif scratch_auth.exists():
        ctx_kwargs["storage_state"] = str(scratch_auth)

    context = browser.new_context(**ctx_kwargs)
    context.set_default_timeout(settings.timeout_ms)

    page = context.new_page()
    page.goto(f"{TARGET_URL}/ledgers/vendor-ledger", wait_until="networkidle")

    # If login screen appears, authenticate once for the module
    phone_input = page.locator("input[placeholder*='phone']")
    if phone_input.is_visible():
        login = LoginPage(page)
        login.authenticate(settings.test_phone or "8596896586", settings.test_otp or "9999")
        expect(page).not_to_have_title("Poshn - Login", timeout=15000)
        AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(AUTH_FILE))

    page.close()
    yield context
    context.close()


@pytest.fixture()
def vendor_ledger_page(vendor_ledger_context: BrowserContext) -> VendorLedgerPage:
    page = vendor_ledger_context.new_page()
    ledger_page = VendorLedgerPage(page, base_url=TARGET_URL)
    ledger_page.navigate()
    yield ledger_page
    page.close()


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
