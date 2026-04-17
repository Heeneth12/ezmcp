from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


def test_generate_returns_401_without_auth():
    from main import app
    client = TestClient(app)
    response = client.post("/v1/ai/generate", json={"message": "hello"})
    assert response.status_code == 401


def test_generate_returns_reply():
    from main import app
    client = TestClient(app)

    with patch("main.get_chat_history", new_callable=AsyncMock) as mock_hist, \
         patch("main.run_agent_loop", new_callable=AsyncMock) as mock_loop:
        mock_hist.return_value = []
        mock_loop.return_value = "Here are your items."
        response = client.post(
            "/v1/ai/generate",
            json={"message": "show all items"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 200
    assert response.json()["reply"] == "Here are your items."


def test_generate_includes_history_in_messages():
    from main import app
    client = TestClient(app)

    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]

    with patch("main.get_chat_history", new_callable=AsyncMock) as mock_hist, \
         patch("main.run_agent_loop", new_callable=AsyncMock) as mock_loop:
        mock_hist.return_value = history
        mock_loop.return_value = "Done."
        response = client.post(
            "/v1/ai/generate",
            json={"message": "show items", "conversationId": 5},
            headers={"Authorization": "Bearer tok"},
        )

    call_messages = mock_loop.call_args[0][0]
    assert call_messages[0] == {"role": "user", "content": "hi"}
    assert call_messages[-1] == {"role": "user", "content": "show items"}
    assert response.json()["reply"] == "Done."


def test_generate_returns_error_reply_on_exception():
    from main import app
    client = TestClient(app)

    with patch("main.get_chat_history", new_callable=AsyncMock) as mock_hist, \
         patch("main.run_agent_loop", new_callable=AsyncMock) as mock_loop:
        mock_hist.return_value = []
        mock_loop.side_effect = Exception("Ollama down")
        response = client.post(
            "/v1/ai/generate",
            json={"message": "hello"},
            headers={"Authorization": "Bearer tok"},
        )

    assert response.status_code == 200
    assert "error" in response.json()["reply"].lower()
