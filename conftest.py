from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, TimeoutError, sync_playwright

from config.settings import ROOT, settings
from pages.login_page import LoginPage


AUTH_STATE = ROOT / "auth" / ".auth.json"


@pytest.fixture(scope="session")
def playwright() -> Playwright:
    with sync_playwright() as instance:
        yield instance


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Browser:
    browser = playwright.chromium.launch(headless=settings.headless)
    yield browser
    browser.close()


@pytest.fixture()
def context(browser: Browser, request: pytest.FixtureRequest) -> BrowserContext:
    kwargs = {"base_url": settings.base_url, "ignore_https_errors": False}
    if AUTH_STATE.exists():
        kwargs["storage_state"] = str(AUTH_STATE)
    context = browser.new_context(**kwargs)
    context.set_default_timeout(settings.timeout_ms)
    context.set_default_navigation_timeout(settings.timeout_ms)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context
    report = getattr(request.node, "rep_call", None)
    if report and report.failed:
        Path("test-results").mkdir(exist_ok=True)
        for index, open_page in enumerate(context.pages):
            if not open_page.is_closed():
                open_page.screenshot(path=f"test-results/{request.node.name}-{index}.png", full_page=True)
        context.tracing.stop(path=f"test-results/{request.node.name}.zip")
    else:
        context.tracing.stop()
    context.close()


@pytest.fixture()
def page(context: BrowserContext) -> Page:
    page = context.new_page()
    yield page
    page.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture()
def unauthenticated_context(browser: Browser) -> BrowserContext:
    context = browser.new_context(base_url=settings.base_url)
    context.set_default_timeout(settings.timeout_ms)
    context.set_default_navigation_timeout(settings.timeout_ms)
    yield context
    context.close()


@pytest.fixture()
def unauthenticated_page(unauthenticated_context: BrowserContext) -> Page:
    page = unauthenticated_context.new_page()
    yield page
    page.close()


@pytest.fixture()
def authenticated_page(context: BrowserContext) -> Page:
    page = context.new_page()
    page.goto("/home", wait_until="domcontentloaded")
    continue_button = page.get_by_role("button", name="Continue")
    if not AUTH_STATE.exists():
        try:
            continue_button.wait_for(state="visible", timeout=min(settings.timeout_ms, 10000))
        except TimeoutError:
            pass
    if "login" in page.title().lower() or continue_button.count():
        if not settings.test_phone or not settings.test_otp:
            pytest.skip("Authentication state absent; set NUCLEUS_TEST_PHONE and NUCLEUS_TEST_OTP securely")
        login = LoginPage(page)
        login.authenticate(settings.test_phone, settings.test_otp)
        page.wait_for_function(
            "() => !document.title.toLowerCase().includes('login')",
            timeout=settings.timeout_ms,
        )
        AUTH_STATE.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(AUTH_STATE))
    yield page
    page.close()
