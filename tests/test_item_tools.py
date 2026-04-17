import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_logger():
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.error = MagicMock()
    return logger


def test_item_tools_has_six_tools():
    from modules.items.item_tools import ITEM_TOOLS
    assert len(ITEM_TOOLS) == 6


def test_each_tool_has_required_keys():
    from modules.items.item_tools import ITEM_TOOLS
    for tool in ITEM_TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
        assert "execute" in tool
        assert callable(tool["execute"])


def test_tool_names_are_correct():
    from modules.items.item_tools import ITEM_TOOLS
    names = [t["name"] for t in ITEM_TOOLS]
    assert names == [
        "get_all_items",
        "search_items",
        "add_item",
        "edit_item",
        "toggle_item_status",
        "get_bulk_template",
    ]


async def test_get_all_items_execute_calls_service(mock_logger):
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "get_all_items")

    with patch("modules.items.item_tools.get_all_items", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {"data": []}
        result = await tool["execute"]({"page": 0, "size": 10, "active": True}, "tok", mock_logger)

    mock_svc.assert_called_once_with(0, 10, {"active": True}, "tok", mock_logger)
    assert "data" in result


async def test_get_all_items_execute_handles_error(mock_logger):
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "get_all_items")

    with patch("modules.items.item_tools.get_all_items", new_callable=AsyncMock) as mock_svc:
        mock_svc.side_effect = Exception("Connection refused")
        result = await tool["execute"]({}, "tok", mock_logger)

    assert "Error" in result


async def test_search_items_execute_calls_service(mock_logger):
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "search_items")

    with patch("modules.items.item_tools.search_items", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {"data": [{"name": "Cable"}]}
        result = await tool["execute"]({"query": "Cable"}, "tok", mock_logger)

    mock_svc.assert_called_once_with({"searchQuery": "Cable"}, "tok", mock_logger)
    assert "Cable" in result


async def test_add_item_generates_code_when_missing(mock_logger):
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "add_item")

    with patch("modules.items.item_tools.create_item", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {"id": 1}
        result = await tool["execute"](
            {"name": "Widget", "category": "General", "unitOfMeasure": "PCS",
             "purchasePrice": 5.0, "sellingPrice": 10.0},
            "tok",
            mock_logger,
        )

    call_payload = mock_svc.call_args[0][0]
    assert call_payload["itemCode"].startswith("ITM-")
    assert "Success" in result


async def test_edit_item_execute_calls_service(mock_logger):
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "edit_item")

    with patch("modules.items.item_tools.update_item", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {}
        result = await tool["execute"]({"id": 7, "name": "Updated"}, "tok", mock_logger)

    mock_svc.assert_called_once_with(7, {"name": "Updated"}, "tok", mock_logger)
    assert "7" in result


async def test_toggle_item_status_execute_calls_service(mock_logger):
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "toggle_item_status")

    with patch("modules.items.item_tools.toggle_item_status_svc", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {}
        result = await tool["execute"]({"id": 3, "active": False}, "tok", mock_logger)

    mock_svc.assert_called_once_with(3, False, "tok", mock_logger)
    assert "Inactive" in result


async def test_get_bulk_template_execute_returns_url(mock_logger):
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "get_bulk_template")

    with patch("modules.items.item_tools.get_template_url") as mock_url:
        mock_url.return_value = "http://localhost:8080/v1/items/template"
        result = await tool["execute"]({}, "tok", mock_logger)

    assert "http://localhost:8080/v1/items/template" in result
    mock_logger.debug.assert_called_once()
