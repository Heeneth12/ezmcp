from fastapi.testclient import TestClient


def test_health_returns_up():
    from main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "UP"
    assert body["service"] == "mcp-ai-worker-python"
    assert body["model"] == "phi4-mini"
    assert "timestamp" in body
