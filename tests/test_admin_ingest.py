import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app

client = TestClient(app)


def test_admin_ingest_success():
    with patch("main.KnowledgeIngester") as MockIngester:
        instance = MockIngester.return_value
        instance.ingest_all.return_value = (2, 7)
        response = client.post("/v1/admin/ingest", json={"clear": False})
    assert response.status_code == 200
    assert response.json() == {"files": 2, "chunks": 7}


def test_admin_ingest_clear_flag_passed_through():
    with patch("main.KnowledgeIngester") as MockIngester:
        instance = MockIngester.return_value
        instance.ingest_all.return_value = (1, 3)
        response = client.post("/v1/admin/ingest", json={"clear": True})
    assert response.status_code == 200
    instance.ingest_all.assert_called_once()
    call_args = instance.ingest_all.call_args
    assert call_args[0][1] is True or call_args[1].get("clear") is True


def test_admin_ingest_missing_docs_returns_404():
    with patch("main.KnowledgeIngester") as MockIngester:
        instance = MockIngester.return_value
        instance.ingest_all.side_effect = FileNotFoundError("Knowledge directory not found: /some/path")
        response = client.post("/v1/admin/ingest", json={})
    assert response.status_code == 404
    assert "Knowledge directory not found" in response.json()["detail"]


def test_admin_ingest_ollama_unavailable_returns_503():
    with patch("main.KnowledgeIngester") as MockIngester:
        instance = MockIngester.return_value
        instance.ingest_all.side_effect = RuntimeError("Ollama not running — start it before ingesting")
        response = client.post("/v1/admin/ingest", json={})
    assert response.status_code == 503
    assert "Ollama not running" in response.json()["detail"]


def test_admin_ingest_default_clear_is_false():
    with patch("main.KnowledgeIngester") as MockIngester:
        instance = MockIngester.return_value
        instance.ingest_all.return_value = (0, 0)
        response = client.post("/v1/admin/ingest", json={})
    assert response.status_code == 200
    call_args = instance.ingest_all.call_args
    clear_value = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("clear", False)
    assert clear_value is False
