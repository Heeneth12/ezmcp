import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_get_all_items_posts_to_correct_url(mock_logger):
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [], "total": 0}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("modules.items.item_service.httpx.AsyncClient", return_value=mock_client):
        from modules.items.item_service import get_all_items
        result = await get_all_items(0, 10, {"active": True}, "tok123", mock_logger)

    call_url = mock_client.post.call_args[0][0]
    assert "page=0&size=10" in call_url
    assert mock_client.post.call_args[1]["headers"]["Authorization"] == "Bearer tok123"
    assert result == {"data": [], "total": 0}


@pytest.mark.asyncio
async def test_get_all_items_logs_request_and_response(mock_logger):
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": []}
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("modules.items.item_service.httpx.AsyncClient", return_value=mock_client):
        from modules.items.item_service import get_all_items
        await get_all_items(0, 10, {}, "tok", mock_logger)

    assert mock_logger.debug.call_count >= 2
    first_call_kwargs = mock_logger.debug.call_args_list[0][1]
    assert first_call_kwargs["layer"] == "http"
    assert first_call_kwargs["event"] == "http_request"


@pytest.mark.asyncio
async def test_search_items_posts_filter(mock_logger):
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"name": "Cable"}]}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("modules.items.item_service.httpx.AsyncClient", return_value=mock_client):
        from modules.items.item_service import search_items
        result = await search_items({"searchQuery": "Cable"}, "tok123", mock_logger)

    assert mock_client.post.call_args[1]["json"] == {"searchQuery": "Cable"}
    assert result == {"data": [{"name": "Cable"}]}


@pytest.mark.asyncio
async def test_create_item_posts_payload(mock_logger):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 1, "name": "Widget"}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    payload = {"name": "Widget", "itemCode": "ITM-001", "category": "General",
               "unitOfMeasure": "PCS", "purchasePrice": 5.0, "sellingPrice": 10.0, "isActive": True}

    with patch("modules.items.item_service.httpx.AsyncClient", return_value=mock_client):
        from modules.items.item_service import create_item
        result = await create_item(payload, "tok123", mock_logger)

    assert mock_client.post.call_args[1]["json"] == payload
    assert result == {"id": 1, "name": "Widget"}


@pytest.mark.asyncio
async def test_toggle_item_status_encodes_bool_lowercase(mock_logger):
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("modules.items.item_service.httpx.AsyncClient", return_value=mock_client):
        from modules.items.item_service import toggle_item_status
        await toggle_item_status(42, False, "tok123", mock_logger)

    call_url = mock_client.post.call_args[0][0]
    assert "active=false" in call_url


def test_get_template_url_returns_correct_url():
    from modules.items.item_service import get_template_url
    url = get_template_url()
    assert url.endswith("/v1/items/template")
