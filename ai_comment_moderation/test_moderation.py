from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_empty_comment():
    response = client.post("/moderate", json={"text": ""})
    assert response.status_code == 400


def test_only_spaces():
    response = client.post("/moderate", json={"text": "   "})
    assert response.status_code == 400


def test_too_long_comment():
    response = client.post("/moderate", json={"text": "a" * 6000})
    assert response.status_code == 400


def test_normal_comment():
    response = client.post("/moderate", json={"text": "Спасибо за отличную статью, было полезно!"})
    assert response.status_code == 200
    data = response.json()
    assert data["label"] in ["ok", "spam", "toxic", "needs_review"]


def test_obvious_spam():
    response = client.post(
        "/moderate",
        json={"text": "Заработай $5000 в день! Переходи по ссылке: http://scam.example/win"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] != "ok"


def test_history_endpoint():
    response = client.get("/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_index_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "<html" in response.text.lower()
