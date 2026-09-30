from pathlib import Path
import pytest
from playwright.sync_api import Page
from pages.pdf_templates_page import PDFTemplatesPage


@pytest.fixture
def pdf_templates_page(authenticated_page: Page) -> PDFTemplatesPage:
    """Fixture providing initialized and navigated PDFTemplatesPage."""
    page_obj = PDFTemplatesPage(authenticated_page)
    page_obj.navigate()
    return page_obj


@pytest.fixture
def sample_pdf_fixture(tmp_path: Path) -> Path:
    """Fixture providing a standard valid 1-page sample PDF file."""
    pdf_file = tmp_path / "sample_invoice.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000102 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n162\n%%EOF")
    return pdf_file


@pytest.fixture
def sample_empty_pdf_fixture(tmp_path: Path) -> Path:
    """Fixture providing a zero-byte empty PDF file."""
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    return empty_file


@pytest.fixture()
def unauthenticated_api_context(playwright) -> "APIRequestContext":
    """Fixture providing an unauthenticated API request context."""
    from config.settings import settings
    context = playwright.request.new_context(
        base_url=settings.base_url,
        extra_http_headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    yield context
    context.dispose()


@pytest.fixture()
def api_request_context(playwright) -> "APIRequestContext":
    """Fixture providing an authenticated API request context."""
    import json
    from config.settings import ROOT, settings

    auth_state = ROOT / "auth" / ".auth.json"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if auth_state.exists():
        try:
            with open(auth_state, "r", encoding="utf-8") as f:
                auth_data = json.load(f)
            for cookie in auth_data.get("cookies", []):
                if cookie.get("name") == "st-access-token":
                    headers["Authorization"] = f"Bearer {cookie.get('value')}"
                    headers["st-auth-mode"] = "header"
                    break
        except Exception:
            pass
    elif settings.access_token:
        headers["Authorization"] = f"Bearer {settings.access_token}"
        headers["st-auth-mode"] = "header"

    context = playwright.request.new_context(
        base_url=settings.base_url,
        extra_http_headers=headers,
    )
    yield context
    context.dispose()
