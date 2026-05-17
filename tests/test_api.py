import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_optimize_basic():
    response = client.post("/optimize", json={"text": "Please provide me with information about Python."})
    assert response.status_code == 200
    data = response.json()
    assert "optimized_text" in data
    assert data["original_tokens"] > 0
    assert data["final_tokens"] > 0
    assert isinstance(data["savings_pct"], float)
    assert isinstance(data["strategies"], list)


def test_optimize_conservative():
    response = client.post("/optimize", json={
        "text": "In order to be able to provide you with information, I need to say that Python is great.",
        "conservative": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["final_tokens"] <= data["original_tokens"]


def test_optimize_portuguese():
    response = client.post("/optimize", json={
        "text": "Por favor, me forneça informações sobre Python.",
        "lang": "pt",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["lang"] == "pt"


def test_optimize_custom_model():
    response = client.post("/optimize", json={
        "text": "Explain the concept of recursion in programming.",
        "model": "gpt-4o",
    })
    assert response.status_code == 200
    assert response.json()["model"] == "gpt-4o"


def test_optimize_empty_text():
    response = client.post("/optimize", json={"text": ""})
    assert response.status_code == 422


def test_optimize_response_fields():
    response = client.post("/optimize", json={"text": "This is a test prompt."})
    assert response.status_code == 200
    data = response.json()
    expected_fields = {
        "original_text", "optimized_text", "original_tokens", "final_tokens",
        "tokens_saved", "savings_pct", "model", "lang",
        "original_cost", "final_cost", "cost_saved", "cost_savings_pct", "strategies",
    }
    assert expected_fields.issubset(data.keys())
