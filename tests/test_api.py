import os
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.config import MAX_PROMPT_CHARS

client = TestClient(app)

VALID_TOKEN = "test-secret-key"
AUTH_HEADER = {"Authorization": f"Bearer {VALID_TOKEN}"}


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("TOKENWISE_API_KEY", VALID_TOKEN)


# --- Health ---

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Authentication ---

def test_optimize_no_token_returns_401():
    response = client.post("/optimize", json={"text": "Hello world."})
    assert response.status_code == 401


def test_optimize_wrong_token_returns_401():
    response = client.post(
        "/optimize",
        json={"text": "Hello world."},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401


def test_optimize_valid_token_returns_200():
    response = client.post(
        "/optimize",
        json={"text": "Please provide me with information about Python."},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200


# --- Functional ---

def test_optimize_basic():
    response = client.post(
        "/optimize",
        json={"text": "Please provide me with information about Python."},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    data = response.json()
    assert "optimized_text" in data
    assert data["original_tokens"] > 0
    assert data["final_tokens"] > 0
    assert isinstance(data["savings_pct"], float)
    assert isinstance(data["strategies"], list)


def test_optimize_conservative():
    response = client.post(
        "/optimize",
        json={
            "text": "In order to be able to provide you with information, I need to say that Python is great.",
            "conservative": True,
        },
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    assert response.json()["final_tokens"] <= response.json()["original_tokens"]


def test_optimize_portuguese():
    response = client.post(
        "/optimize",
        json={"text": "Por favor, me forneça informações sobre Python.", "lang": "pt"},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    assert response.json()["lang"] == "pt"


def test_optimize_custom_model():
    response = client.post(
        "/optimize",
        json={"text": "Explain the concept of recursion in programming.", "model": "gpt-4o"},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    assert response.json()["model"] == "gpt-4o"


def test_optimize_empty_text():
    response = client.post("/optimize", json={"text": ""}, headers=AUTH_HEADER)
    assert response.status_code == 422


def test_optimize_oversized_payload_returns_422():
    # Generate a prompt that exceeds the character limit
    oversized_text = "a" * (MAX_PROMPT_CHARS + 1)
    response = client.post("/optimize", json={"text": oversized_text}, headers=AUTH_HEADER)
    assert response.status_code == 422


def test_optimize_response_fields():
    response = client.post(
        "/optimize",
        json={"text": "This is a test prompt."},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    data = response.json()
    expected_fields = {
        "original_text", "optimized_text", "original_tokens", "final_tokens",
        "tokens_saved", "savings_pct", "model", "lang",
        "original_cost", "final_cost", "cost_saved", "cost_savings_pct", "strategies",
    }
    assert expected_fields.issubset(data.keys())
