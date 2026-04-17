import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_get_tool_schemas_returns_list_of_functions():
    from ai.tool_registry import get_tool_schemas
    schemas = get_tool_schemas()
    assert isinstance(schemas, list)
    assert len(schemas) > 0
    for schema in schemas:
        assert schema["type"] == "function"
        assert "name" in schema["function"]
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]
        assert "execute" not in schema["function"]


def test_get_tool_schemas_has_all_item_tools():
    from ai.tool_registry import get_tool_schemas
    schemas = get_tool_schemas()
    names = [s["function"]["name"] for s in schemas]
    assert "get_all_items" in names
    assert "search_items" in names
    assert "add_item" in names
    assert "edit_item" in names
    assert "toggle_item_status" in names
    assert "get_bulk_template" in names


async def test_execute_tool_routes_to_correct_tool():
    from ai.tool_registry import execute_tool

    with patch("modules.items.item_tools.search_items", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {"data": [{"name": "Cable"}]}
        result = await execute_tool("search_items", {"query": "Cable"}, "tok")

    mock_svc.assert_called_once_with({"searchQuery": "Cable"}, "tok")
    assert "Cable" in result


async def test_execute_tool_unknown_name_returns_error():
    from ai.tool_registry import execute_tool
    result = await execute_tool("nonexistent_tool", {}, "tok")
    assert "not found" in result


async def test_run_agent_loop_returns_reply_when_no_tool_calls():
    from ai.tool_registry import run_agent_loop

    mock_message = MagicMock()
    mock_message.tool_calls = None
    mock_message.content = "Here are your items."

    mock_response = MagicMock()
    mock_response.message = mock_message

    mock_ollama = AsyncMock()
    mock_ollama.chat.return_value = mock_response

    with patch("ai.tool_registry.OllamaAsyncClient", return_value=mock_ollama):
        result = await run_agent_loop([{"role": "user", "content": "show items"}], "tok")

    assert result == "Here are your items."
    assert mock_ollama.chat.call_count == 1


async def test_run_agent_loop_executes_tool_and_loops():
    from ai.tool_registry import run_agent_loop

    tool_call = MagicMock()
    tool_call.function.name = "get_bulk_template"
    tool_call.function.arguments = {}

    msg_with_tool = MagicMock()
    msg_with_tool.tool_calls = [tool_call]
    msg_with_tool.content = ""

    msg_final = MagicMock()
    msg_final.tool_calls = None
    msg_final.content = "Download link: http://example.com/template"

    mock_ollama = AsyncMock()
    mock_ollama.chat.side_effect = [
        MagicMock(message=msg_with_tool),
        MagicMock(message=msg_final),
    ]

    with patch("ai.tool_registry.OllamaAsyncClient", return_value=mock_ollama), \
         patch("ai.tool_registry.execute_tool", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = "http://example.com/template"
        result = await run_agent_loop([{"role": "user", "content": "give me template"}], "tok")

    assert mock_ollama.chat.call_count == 2
    mock_exec.assert_called_once_with("get_bulk_template", {}, "tok")
    assert result == "Download link: http://example.com/template"


async def test_run_agent_loop_stops_at_max_iterations():
    from ai.tool_registry import run_agent_loop, MAX_TOOL_ITERATIONS

    tool_call = MagicMock()
    tool_call.function.name = "get_all_items"
    tool_call.function.arguments = {}

    msg_with_tool = MagicMock()
    msg_with_tool.tool_calls = [tool_call]
    msg_with_tool.content = ""

    mock_ollama = AsyncMock()
    mock_ollama.chat.return_value = MagicMock(message=msg_with_tool)

    with patch("ai.tool_registry.OllamaAsyncClient", return_value=mock_ollama), \
         patch("ai.tool_registry.execute_tool", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = "data"
        result = await run_agent_loop([{"role": "user", "content": "loop"}], "tok")

    assert mock_ollama.chat.call_count == MAX_TOOL_ITERATIONS
    assert "maximum" in result.lower()
