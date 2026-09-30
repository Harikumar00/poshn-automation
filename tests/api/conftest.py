import json
from pathlib import Path
import pytest
from playwright.sync_api import APIRequestContext, Playwright

from config.settings import ROOT, settings


AUTH_STATE = ROOT / "auth" / ".auth.json"


@pytest.fixture(scope="session")
def api_auth_headers() -> dict[str, str]:
    """Extracts the SuperTokens access token from the saved session state."""
    if not AUTH_STATE.exists():
        pytest.skip("Auth state not found. Run authentication flow first.")

    with open(AUTH_STATE, "r", encoding="utf-8") as f:
        auth_data = json.load(f)

    token = None
    for cookie in auth_data.get("cookies", []):
        if cookie.get("name") == "st-access-token":
            token = cookie.get("value")
            break

    if not token:
        pytest.skip("st-access-token cookie not found in auth state.")

    return {
        "Authorization": f"Bearer {token}",
        "st-auth-mode": "header",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@pytest.fixture()
def authenticated_api_client(
    playwright: Playwright, api_auth_headers: dict[str, str]
) -> APIRequestContext:
    """Provides an authenticated Playwright APIRequestContext for backend REST testing."""
    context = playwright.request.new_context(
        base_url=settings.base_url,
        extra_http_headers=api_auth_headers,
    )
    yield context
    context.dispose()


@pytest.fixture()
def unauthenticated_api_client(playwright: Playwright) -> APIRequestContext:
    """Provides an unauthenticated Playwright APIRequestContext to test 401 guards."""
    context = playwright.request.new_context(
        base_url=settings.base_url,
        extra_http_headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    yield context
    context.dispose()
