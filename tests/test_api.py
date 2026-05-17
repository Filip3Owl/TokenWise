import os
import pytest
import httpx
from unittest.mock import patch
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


# --- POST /chat ---

# Reusable mock that bypasses the real Anthropic/OpenAI calls
MOCK_LLM_RESPONSE = "This is a mocked LLM response."


def test_chat_claude_returns_200(monkeypatch):
    # Mock call_llm so no real API call is made
    monkeypatch.setattr("api.main.call_llm", lambda prompt, model: MOCK_LLM_RESPONSE)
    response = client.post(
        "/chat",
        json={"text": "Please provide me with information about Python.", "model": "claude-sonnet-4-6"},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["llm_response"] == MOCK_LLM_RESPONSE
    assert data["original_tokens"] > 0
    assert data["tokens_saved"] >= 0


def test_chat_gpt_returns_200(monkeypatch):
    # Verify that GPT models are routed correctly through the same endpoint
    monkeypatch.setattr("api.main.call_llm", lambda prompt, model: MOCK_LLM_RESPONSE)
    response = client.post(
        "/chat",
        json={"text": "Explain recursion in simple terms.", "model": "gpt-4o"},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    assert response.json()["llm_response"] == MOCK_LLM_RESPONSE


def test_chat_no_token_returns_401():
    response = client.post("/chat", json={"text": "Hello world."})
    assert response.status_code == 401


def test_chat_empty_text_returns_422():
    response = client.post("/chat", json={"text": ""}, headers=AUTH_HEADER)
    assert response.status_code == 422


def test_chat_oversized_payload_returns_422():
    oversized_text = "a" * (MAX_PROMPT_CHARS + 1)
    response = client.post("/chat", json={"text": oversized_text}, headers=AUTH_HEADER)
    assert response.status_code == 422


def test_chat_unsupported_model_returns_400(monkeypatch):
    # call_llm raises HTTP 400 for unknown model prefixes
    def raise_400(prompt, model):
        raise httpx.HTTPStatusError(
            "unsupported model",
            request=None,
            response=None,
        )
    monkeypatch.setattr("api.main.call_llm", lambda prompt, model: (_ for _ in ()).throw(
        __import__("fastapi").HTTPException(status_code=400, detail="Unsupported model")
    ))
    response = client.post(
        "/chat",
        json={"text": "Hello.", "model": "unsupported-model-xyz"},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 400


def test_chat_timeout_returns_504(monkeypatch):
    # Simulate the upstream LLM timing out
    def raise_timeout(prompt, model):
        raise __import__("fastapi").HTTPException(status_code=504, detail="Timeout")
    monkeypatch.setattr("api.main.call_llm", raise_timeout)
    response = client.post(
        "/chat",
        json={"text": "Hello world.", "model": "claude-sonnet-4-6"},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 504


def test_chat_response_fields(monkeypatch):
    # Verify all expected fields are present in the response
    monkeypatch.setattr("api.main.call_llm", lambda prompt, model: MOCK_LLM_RESPONSE)
    response = client.post(
        "/chat",
        json={"text": "This is a test prompt."},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    data = response.json()
    expected_fields = {
        "llm_response", "original_tokens", "final_tokens", "tokens_saved",
        "savings_pct", "original_cost", "final_cost", "cost_saved",
        "cost_savings_pct", "model", "lang",
    }
    assert expected_fields.issubset(data.keys())


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
