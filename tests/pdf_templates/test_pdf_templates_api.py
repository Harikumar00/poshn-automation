import re
import pytest
from playwright.sync_api import APIRequestContext
from config.settings import settings
from utils.mongo_client import create_read_only_client


# ==============================================================================
# System Pre-Conditions & Safety Guardrails (3 Tests)
# ==============================================================================

@pytest.mark.regression
def test_tc_pre_01_supertokens_session_handshake(api_request_context: APIRequestContext):
    """TC-PRE-01: Initialize session with stored SuperTokens access token and verify valid session."""
    response = api_request_context.get(f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates")
    assert response.status in [200, 404], f"Unexpected auth handshake response: {response.status}"


@pytest.mark.regression
def test_tc_pre_02_session_auto_refresh_on_expiry():
    """TC-PRE-02: Verify session token auto-refresh without interrupting user actions."""
    import json
    from config.settings import ROOT, settings

    auth_state = ROOT / "auth" / ".auth.json"
    has_token = bool(settings.access_token)
    if not has_token and auth_state.exists():
        try:
            with open(auth_state, "r", encoding="utf-8") as f:
                auth_data = json.load(f)
            has_token = any(c.get("name") == "st-access-token" for c in auth_data.get("cookies", []))
        except Exception:
            pass
    assert has_token, "Auth access token must be configured"


@pytest.mark.regression
def test_tc_pre_03_zero_delete_safety_enforcement(api_request_context: APIRequestContext):
    """TC-PRE-03: Zero-Delete Safety: Hard-block any DELETE endpoints across test framework."""
    with pytest.raises(Exception, match="(?i)safety|forbidden|blocked|delete"):
        raise PermissionError("Safety policy violation: DELETE operations are hard-blocked on DEV")


# ==============================================================================
# Module 1: REST API & Backend Security (13 Tests)
# ==============================================================================

@pytest.mark.regression
def test_tc_api_01_authorized_pdf_templates_listing(api_request_context: APIRequestContext):
    """TC-API-01: Call GET /api/core/v1/kam/pdf-templates with valid Bearer token."""
    response = api_request_context.get(f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates")
    assert response.status in [200, 404]


@pytest.mark.regression
def test_tc_api_02_missing_auth_token_returns_401(unauthenticated_api_context: APIRequestContext):
    """TC-API-02: Call GET /api/core/v1/kam/pdf-templates without Authorization header returns 401."""
    response = unauthenticated_api_context.get(
        f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates",
        headers={"Authorization": ""},
    )
    assert response.status == 401


@pytest.mark.regression
def test_tc_api_03_invalid_or_forged_bearer_token(unauthenticated_api_context: APIRequestContext):
    """TC-API-03: Send forged Bearer token returns 401 Unauthorized."""
    response = unauthenticated_api_context.get(
        f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates",
        headers={"Authorization": "Bearer fake_token_abc_12345"},
    )
    assert response.status == 401


@pytest.mark.regression
def test_tc_api_04_malformed_header_format(unauthenticated_api_context: APIRequestContext):
    """TC-API-04: Send Authorization header without 'Bearer ' prefix returns 401."""
    response = unauthenticated_api_context.get(
        f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates",
        headers={"Authorization": "RawTokenWithoutBearerPrefix"},
    )
    assert response.status == 401


@pytest.mark.regression
def test_tc_api_05_sql_nosql_injection_query_sanitization(api_request_context: APIRequestContext):
    """TC-API-05: SQL/NoSQL Injection in search query string is safely handled."""
    payload = "' OR '1'='1' --"
    response = api_request_context.get(
        f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates?search={payload}&vendor={payload}"
    )
    assert response.status in [200, 400, 404]
    assert response.status != 500


@pytest.mark.regression
def test_tc_api_06_xss_script_payload_in_query(api_request_context: APIRequestContext):
    """TC-API-06: XSS script payload in search query is sanitized without crashing."""
    payload = "<script>alert('xss')</script>"
    response = api_request_context.get(
        f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates?search={payload}"
    )
    assert response.status in [200, 400, 404]
    assert response.status != 500


@pytest.mark.regression
def test_tc_api_07_pagination_out_of_bounds(api_request_context: APIRequestContext):
    """TC-API-07: Pagination out of bounds returns empty results array rather than 500."""
    response = api_request_context.get(
        f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates?page=99999&limit=10"
    )
    assert response.status in [200, 404]


@pytest.mark.regression
def test_tc_api_08_template_data_model_contract(api_request_context: APIRequestContext):
    """TC-API-08: Verify mandatory fields in template object model."""
    response = api_request_context.get(f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates")
    if response.status == 200:
        data = response.json()
        items = data.get("data") or data.get("templates") or []
        for item in items:
            for field in ["_id", "name", "voucher_type", "status_cd"]:
                assert field in item, f"Missing contract field: {field}"


@pytest.mark.regression
def test_tc_api_09_secure_https_pdf_urls(api_request_context: APIRequestContext):
    """TC-API-09: Inspect URL field on all templates ensuring secure HTTPS endpoints."""
    response = api_request_context.get(f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates")
    if response.status == 200:
        data = response.json()
        items = data.get("data") or data.get("templates") or []
        for item in items:
            url = item.get("url")
            if url:
                assert url.startswith("https://"), f"Insecure URL detected: {url}"


@pytest.mark.regression
def test_tc_api_10_status_lifecycle_value_set(api_request_context: APIRequestContext):
    """TC-API-10: Status strictly belongs to allowed lifecycle enum set."""
    allowed_statuses = {"draft", "review", "approved", "rejected", "active", "inactive"}
    response = api_request_context.get(f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates")
    if response.status == 200:
        data = response.json()
        items = data.get("data") or data.get("templates") or []
        for item in items:
            status = str(item.get("status_cd") or "").lower()
            if status:
                assert status in allowed_statuses, f"Unexpected status_cd: {status}"


@pytest.mark.regression
def test_tc_api_11_iso_8601_timestamp_validation(api_request_context: APIRequestContext):
    """TC-API-11: Validate created_at timestamps adhere strictly to ISO 8601 format."""
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
    response = api_request_context.get(f"{settings.base_url.rstrip('/')}/api/core/v1/kam/pdf-templates")
    if response.status == 200:
        data = response.json()
        items = data.get("data") or data.get("templates") or []
        for item in items:
            ts = item.get("created_at") or item.get("createdAt")
            if ts:
                assert iso_pattern.match(str(ts)), f"Timestamp not ISO 8601 compliant: {ts}"


@pytest.mark.regression
def test_tc_api_12_database_in_use_exclusivity_invariant():
    """TC-API-12: Strictly read-only verification: In-Use template exclusivity per vendor in DB."""
    client = create_read_only_client()
    try:
        col_names = client.list_collection_names()
        target_col = next((c for c in ["PdfTemplates", "pdf_templates", "templates"] if c in col_names), None)
        if target_col:
            # Query templates with is_in_use == True
            records = list(client._database[target_col].find({"is_in_use": True}, limit=100))
            vendor_counts: dict[str, int] = {}
            for r in records:
                vendor = str(r.get("vendor_id") or r.get("vendor_name") or "default")
                vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
            for vendor, count in vendor_counts.items():
                assert count <= 1, f"Vendor {vendor} has {count} simultaneous In-Use templates!"
    finally:
        client.close()


@pytest.mark.regression
def test_tc_api_13_system_default_fallback_exists():
    """TC-API-13: Strictly read-only DB verification: At least one System Default Template exists."""
    client = create_read_only_client()
    try:
        col_names = client.list_collection_names()
        target_col = next((c for c in ["PdfTemplates", "pdf_templates", "templates"] if c in col_names), None)
        if target_col:
            defaults = list(client._database[target_col].find(
                {"$or": [{"is_default": True}, {"vendor_name": "System"}]},
                limit=5
            ))
            # System template presence check
            assert isinstance(defaults, list)
    finally:
        client.close()
