import pytest
from playwright.sync_api import expect

from config.settings import settings
from pages.login_page import LoginPage


@pytest.mark.auth
def test_valid_login_and_session_reuse(unauthenticated_page, unauthenticated_context):
    if not settings.test_phone or not settings.test_otp:
        pytest.skip("Set NUCLEUS_TEST_PHONE and NUCLEUS_TEST_OTP securely")
    # Start this case unauthenticated even when a reusable storage state exists.
    unauthenticated_page.goto("/", wait_until="domcontentloaded")
    LoginPage(unauthenticated_page).authenticate(settings.test_phone, settings.test_otp)
    expect(unauthenticated_page).not_to_have_title("Poshn - Login")
    state = unauthenticated_context.storage_state()
    assert state.get("cookies") is not None


@pytest.mark.auth
def test_invalid_phone_validation(unauthenticated_page):
    unauthenticated_page.goto("/", wait_until="domcontentloaded")
    field = unauthenticated_page.get_by_role("textbox", name="+")
    field.fill("123")
    unauthenticated_page.get_by_role("button", name="Continue").click()
    expect(unauthenticated_page.get_by_text("Phone number should be of 10 chars", exact=True)).to_be_visible()


@pytest.mark.auth
def test_logout(authenticated_page):
    logout = authenticated_page.get_by_role("button", name="Log Out")
    expect(logout).to_be_visible()
    logout.click()
    authenticated_page.get_by_role("button", name="Yes").click()
    expect(authenticated_page).to_have_url(f"{settings.base_url}/")
