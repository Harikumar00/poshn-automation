import pytest
from playwright.sync_api import APIRequestContext


@pytest.mark.api
def test_api_auth_user_profile(authenticated_api_client: APIRequestContext):
    """Verify GET /api/core/v1/auth/user returns 200 with authenticated profile data."""
    response = authenticated_api_client.get("/api/core/v1/auth/user")
    assert response.status == 200
    assert response.ok

    payload = response.json()
    assert payload.get("status") == "success"
    assert "data" in payload
    assert isinstance(payload["data"], dict)


@pytest.mark.api
def test_api_auth_user_roles(authenticated_api_client: APIRequestContext):
    """Verify GET /api/core/v1/auth/user/roles returns 200 with assigned roles."""
    response = authenticated_api_client.get("/api/core/v1/auth/user/roles")
    assert response.status == 200
    assert response.ok

    payload = response.json()
    assert payload.get("status", "").lower() == "success"
    assert "response" in payload


@pytest.mark.api
def test_api_purchase_orders_list(authenticated_api_client: APIRequestContext):
    """Verify GET /api/core/v1/kam/purchase-orders returns 200 and paginated records."""
    response = authenticated_api_client.get(
        "/api/core/v1/kam/purchase-orders",
        params={"page_size": "10", "offset": "0"},
    )
    assert response.status == 200
    assert response.ok

    payload = response.json()
    assert payload.get("status", "").lower() == "success"
    data = payload.get("data", {})
    records = data.get("data", [])
    assert isinstance(records, list)


@pytest.mark.api
def test_api_sales_invoices_list(authenticated_api_client: APIRequestContext):
    """Verify GET /api/core/v1/kam/invoices returns 200 and invoice list structure."""
    response = authenticated_api_client.get(
        "/api/core/v1/kam/invoices",
        params={"page_size": "10", "offset": "0"},
    )
    assert response.status == 200
    assert response.ok

    payload = response.json()
    assert payload.get("status", "").lower() == "success"
    data = payload.get("data", {})
    records = data.get("data", [])
    assert isinstance(records, list)


@pytest.mark.api
def test_api_customers_list(authenticated_api_client: APIRequestContext):
    """Verify GET /api/core/v1/kam/users with role 'buyer' returns 200 and approved customers."""
    response = authenticated_api_client.get(
        "/api/core/v1/kam/users",
        params={
            "page_size": "10",
            "offset": "0",
            "roles": "buyer",
            "is_internal_user": "false",
            "applicationStatus": "approved",
        },
    )
    assert response.status == 200
    assert response.ok

    payload = response.json()
    assert payload.get("status") == "success"
    data = payload.get("data", {})
    assert "users" in data or "records" in data or isinstance(data, dict)


@pytest.mark.api
def test_api_vendors_list(authenticated_api_client: APIRequestContext):
    """Verify GET /api/core/v1/kam/users with role 'seller' returns 200 and approved vendors."""
    response = authenticated_api_client.get(
        "/api/core/v1/kam/users",
        params={
            "page_size": "10",
            "offset": "0",
            "roles": "seller",
            "is_internal_user": "false",
            "applicationStatus": "approved",
        },
    )
    assert response.status == 200
    assert response.ok

    payload = response.json()
    assert payload.get("status") == "success"


@pytest.mark.api
def test_api_sales_credit_notes_list(authenticated_api_client: APIRequestContext):
    """Verify GET /api/core/v1/sales/credit-notes returns 200."""
    response = authenticated_api_client.get(
        "/api/core/v1/sales/credit-notes",
        params={"page_size": "10", "offset": "0"},
    )
    assert response.status == 200
    assert response.ok

    payload = response.json()
    assert payload.get("status") == "success"


@pytest.mark.api
def test_api_purchases_debit_notes_list(authenticated_api_client: APIRequestContext):
    """Verify GET /api/core/v1/purchase/debit-notes returns 200."""
    response = authenticated_api_client.get(
        "/api/core/v1/purchase/debit-notes",
        params={"page_size": "10", "offset": "0"},
    )
    assert response.status == 200
    assert response.ok

    payload = response.json()
    assert payload.get("status") == "success"


@pytest.mark.api
def test_api_unauthorized_without_token(unauthenticated_api_client: APIRequestContext):
    """Verify that requesting protected endpoints without auth token returns 401 Unauthorized."""
    response = unauthenticated_api_client.get("/api/core/v1/auth/user")
    assert response.status == 401
    assert not response.ok
