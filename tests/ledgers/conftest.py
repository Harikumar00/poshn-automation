import os
from pathlib import Path
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, expect

from config.settings import ROOT, settings
from pages.login_page import LoginPage
from pages.vendor_ledger_page import VendorLedgerPage

TARGET_URL = os.getenv("VENDOR_LEDGER_URL", "https://engg-2406.nucleus.te.poshn.app")
AUTH_FILE = ROOT / "auth" / ".auth_engg_2406.json"


@pytest.fixture(scope="package")
def ledger_context(browser: Browser) -> BrowserContext:
    """Provides an authenticated browser context scoped exclusively to feature branch 2406."""
    ctx_kwargs = {"base_url": TARGET_URL}
    if AUTH_FILE.exists():
        ctx_kwargs["storage_state"] = str(AUTH_FILE)

    context = browser.new_context(**ctx_kwargs)
    context.set_default_timeout(settings.timeout_ms)

    page = context.new_page()
    page.goto(f"{TARGET_URL}/ledgers/vendor-ledger", wait_until="networkidle")

    # If login screen appears, authenticate once for feature branch 2406
    if "login" in page.title().lower() or page.url.rstrip("/") == TARGET_URL:
        login = LoginPage(page)
        if login.phone.is_visible():
            login.phone.fill(settings.test_phone or "8596896586")
            login.continue_button.click()
            page.wait_for_timeout(1500)
        visible_otp = login.otp.filter(visible=True)
        if visible_otp.count():
            for idx, d in enumerate(settings.test_otp or "9999"):
                visible_otp.nth(idx).fill(d)
            login.login_button.click()
            page.wait_for_url(lambda u: "login" not in u.lower(), timeout=20000)
            page.goto(f"{TARGET_URL}/ledgers/vendor-ledger", wait_until="networkidle")
            AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(AUTH_FILE))

    page.close()
    yield context
    context.close()


@pytest.fixture()
def authenticated_page(ledger_context: BrowserContext) -> Page:
    """Overrides authenticated_page for tests/ledgers so it only uses feature branch 2406."""
    page = ledger_context.new_page()
    yield page
    page.close()


@pytest.fixture()
def vendor_ledger_page(ledger_context: BrowserContext) -> VendorLedgerPage:
    page = ledger_context.new_page()
    ledger_page = VendorLedgerPage(page, base_url=TARGET_URL)
    ledger_page.navigate()
    yield ledger_page
    page.close()
