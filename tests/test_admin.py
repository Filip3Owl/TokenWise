"""
Tests for the /admin/clients CRUD endpoints (Phase C).

The SQLite database is replaced with in-memory mocks so these tests are
self-contained and leave no files on disk.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

ADMIN_TOKEN = "master-admin-key"
ADMIN_HEADER = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

# Sample client records used as fixtures
_BASIC_CLIENT = {
    "id": 1,
    "name": "acme",
    "token": "tok_basic_abc",
    "plan": "basic",
    "rate_limit": 60,
    "is_active": True,
    "created_at": "2026-01-01 00:00:00",
}

_PRO_CLIENT = {
    "id": 2,
    "name": "bigcorp",
    "token": "tok_pro_xyz",
    "plan": "pro",
    "rate_limit": 300,
    "is_active": True,
    "created_at": "2026-01-02 00:00:00",
}


@pytest.fixture(autouse=True)
def set_admin_key(monkeypatch):
    monkeypatch.setenv("TOKENWISE_API_KEY", ADMIN_TOKEN)


# ---------------------------------------------------------------------------
# POST /admin/clients
# ---------------------------------------------------------------------------

def test_create_client_basic(monkeypatch):
    monkeypatch.setattr("api.admin.create_client", lambda name, plan, rate_limit: _BASIC_CLIENT)
    response = client.post("/admin/clients", json={"name": "acme"}, headers=ADMIN_HEADER)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "acme"
    assert data["plan"] == "basic"
    assert data["rate_limit"] == 60
    assert "token" in data


def test_create_client_pro(monkeypatch):
    monkeypatch.setattr("api.admin.create_client", lambda name, plan, rate_limit: _PRO_CLIENT)
    response = client.post("/admin/clients", json={"name": "bigcorp", "plan": "pro"}, headers=ADMIN_HEADER)
    assert response.status_code == 201
    data = response.json()
    assert data["plan"] == "pro"
    assert data["rate_limit"] == 300


def test_create_client_custom_rate_limit(monkeypatch):
    custom = {**_BASIC_CLIENT, "rate_limit": 120}
    monkeypatch.setattr("api.admin.create_client", lambda name, plan, rate_limit: custom)
    response = client.post(
        "/admin/clients",
        json={"name": "acme", "plan": "basic", "rate_limit": 120},
        headers=ADMIN_HEADER,
    )
    assert response.status_code == 201
    assert response.json()["rate_limit"] == 120


def test_create_client_invalid_plan():
    response = client.post(
        "/admin/clients",
        json={"name": "acme", "plan": "enterprise"},
        headers=ADMIN_HEADER,
    )
    assert response.status_code == 422


def test_create_client_no_auth():
    response = client.post("/admin/clients", json={"name": "acme"})
    assert response.status_code == 401


def test_create_client_wrong_token():
    response = client.post(
        "/admin/clients",
        json={"name": "acme"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /admin/clients
# ---------------------------------------------------------------------------

def test_list_clients(monkeypatch):
    monkeypatch.setattr("api.admin.list_clients", lambda: [_BASIC_CLIENT, _PRO_CLIENT])
    response = client.get("/admin/clients", headers=ADMIN_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "acme"
    assert data[1]["name"] == "bigcorp"


def test_list_clients_empty(monkeypatch):
    monkeypatch.setattr("api.admin.list_clients", lambda: [])
    response = client.get("/admin/clients", headers=ADMIN_HEADER)
    assert response.status_code == 200
    assert response.json() == []


def test_list_clients_no_auth():
    response = client.get("/admin/clients")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /admin/clients/{token}
# ---------------------------------------------------------------------------

def test_update_client_plan(monkeypatch):
    updated = {**_BASIC_CLIENT, "plan": "pro", "rate_limit": 300}
    monkeypatch.setattr("api.admin.update_client", lambda token, plan, rate_limit: updated)
    response = client.patch(
        f"/admin/clients/{_BASIC_CLIENT['token']}",
        json={"plan": "pro"},
        headers=ADMIN_HEADER,
    )
    assert response.status_code == 200
    assert response.json()["plan"] == "pro"
    assert response.json()["rate_limit"] == 300


def test_update_client_rate_limit(monkeypatch):
    updated = {**_BASIC_CLIENT, "rate_limit": 10}
    monkeypatch.setattr("api.admin.update_client", lambda token, plan, rate_limit: updated)
    response = client.patch(
        f"/admin/clients/{_BASIC_CLIENT['token']}",
        json={"rate_limit": 10},
        headers=ADMIN_HEADER,
    )
    assert response.status_code == 200
    assert response.json()["rate_limit"] == 10


def test_update_client_not_found(monkeypatch):
    monkeypatch.setattr("api.admin.update_client", lambda token, plan, rate_limit: None)
    response = client.patch(
        "/admin/clients/nonexistent-token",
        json={"plan": "pro"},
        headers=ADMIN_HEADER,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /admin/clients/{token}
# ---------------------------------------------------------------------------

def test_revoke_client(monkeypatch):
    monkeypatch.setattr("api.admin.revoke_client", lambda token: True)
    response = client.delete(f"/admin/clients/{_BASIC_CLIENT['token']}", headers=ADMIN_HEADER)
    assert response.status_code == 204


def test_revoke_client_not_found(monkeypatch):
    monkeypatch.setattr("api.admin.revoke_client", lambda token: False)
    response = client.delete("/admin/clients/nonexistent-token", headers=ADMIN_HEADER)
    assert response.status_code == 404


def test_revoke_client_no_auth():
    response = client.delete(f"/admin/clients/{_BASIC_CLIENT['token']}")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Rate limiting (per-client sliding window)
# ---------------------------------------------------------------------------

def test_rate_limit_exceeded(monkeypatch):
    """A client with rate_limit=1 should get 429 on the second request."""
    tight_client = {**_BASIC_CLIENT, "token": "tight-token", "rate_limit": 1}
    monkeypatch.setattr("api.auth.get_client_by_token", lambda token: tight_client if token == "tight-token" else None)

    headers = {"Authorization": "Bearer tight-token"}

    # First request succeeds
    r1 = client.post("/optimize", json={"text": "Hello world."}, headers=headers)
    assert r1.status_code == 200

    # Second request exceeds the 1 req/min limit
    r2 = client.post("/optimize", json={"text": "Hello world."}, headers=headers)
    assert r2.status_code == 429
    assert "Rate limit exceeded" in r2.json()["detail"]
