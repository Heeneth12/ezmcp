import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_logger):
    with patch("main.RequestLogger", return_value=mock_logger), \
         patch("main.run_agent_loop", new_callable=AsyncMock) as mock_loop, \
         patch("main.get_chat_history", new_callable=AsyncMock) as mock_history:
        mock_loop.return_value = "Here are your items."
        mock_history.return_value = []
        from main import app
        yield TestClient(app), mock_loop, mock_history, mock_logger


def test_generate_returns_reply(client):
    test_client, mock_loop, _, _ = client
    response = test_client.post(
        "/v1/ai/generate",
        json={"message": "show me items", "conversationId": 42},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert response.json()["reply"] == "Here are your items."


def test_generate_requires_auth(client):
    test_client, _, _, _ = client
    response = test_client.post("/v1/ai/generate", json={"message": "hello"})
    assert response.status_code == 401


def test_generate_creates_logger_with_conversation_id(mock_logger):
    with patch("main.RequestLogger", return_value=mock_logger) as mock_rl, \
         patch("main.run_agent_loop", new_callable=AsyncMock) as mock_loop, \
         patch("main.get_chat_history", new_callable=AsyncMock):
        mock_loop.return_value = "reply"
        from main import app
        test_client = TestClient(app)
        test_client.post(
            "/v1/ai/generate",
            json={"message": "hello", "conversationId": 99},
            headers={"Authorization": "Bearer tok"},
        )
    mock_rl.assert_called_once_with(99, "hello")


def test_generate_logs_final_reply(mock_logger):
    with patch("main.RequestLogger", return_value=mock_logger), \
         patch("main.run_agent_loop", new_callable=AsyncMock) as mock_loop, \
         patch("main.get_chat_history", new_callable=AsyncMock):
        mock_loop.return_value = "Here are your items."
        from main import app
        test_client = TestClient(app)
        test_client.post(
            "/v1/ai/generate",
            json={"message": "hello"},
            headers={"Authorization": "Bearer tok"},
        )
    mock_logger.info.assert_called_once()
    mock_logger.close.assert_called_once_with()


def test_generate_logs_error_and_closes_on_exception(mock_logger):
    with patch("main.RequestLogger", return_value=mock_logger), \
         patch("main.run_agent_loop", new_callable=AsyncMock) as mock_loop, \
         patch("main.get_chat_history", new_callable=AsyncMock):
        mock_loop.side_effect = Exception("Ollama is down")
        from main import app
        test_client = TestClient(app)
        response = test_client.post(
            "/v1/ai/generate",
            json={"message": "hello"},
            headers={"Authorization": "Bearer tok"},
        )
    assert "error" in response.json()["reply"].lower()
    mock_logger.error.assert_called_once()
    mock_logger.close.assert_called_once_with(error=True)
