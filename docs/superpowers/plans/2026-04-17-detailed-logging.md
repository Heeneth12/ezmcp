# Detailed Logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add full-debug, layer-by-layer logging to every request — console gets human-readable banners, each request gets its own JSON log file in `logs/`.

**Architecture:** A `RequestLogger` class (created once per request in `main.py`) owns a Python `logging.Logger` with two handlers: a `StreamHandler` (banner-style console) and a `FileHandler` (JSON-per-line file at `logs/<conversationId>-<timestamp>.log`). The instance is passed as a parameter down through `run_agent_loop → execute_tool → item_service functions`.

**Tech Stack:** Python standard library `logging`, `json`, `os`, `traceback`; pytest + unittest.mock for tests.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `logger.py` | **Create** | `RequestLogger` class — handlers, formatters, `log()` methods |
| `tests/test_logger.py` | **Create** | Tests for `RequestLogger` |
| `main.py` | **Modify** | Instantiate `RequestLogger` per request; pass to `run_agent_loop`; log request/reply/errors |
| `tests/test_generate.py` | **Modify** | Pass mock logger in existing tests |
| `ai/tool_registry.py` | **Modify** | Accept `logger` in `run_agent_loop` and `execute_tool`; log Ollama iterations |
| `tests/test_tool_registry.py` | **Modify** | Pass mock logger in all existing calls |
| `modules/items/item_tools.py` | **Modify** | Accept `logger` in all `_execute_*` functions; pass to service |
| `tests/test_item_tools.py` | **Modify** | Pass mock logger in all existing calls |
| `modules/items/item_service.py` | **Modify** | Accept `logger` in all service functions; log HTTP request + response |
| `tests/test_item_service.py` | **Modify** | Pass mock logger in all existing calls |

---

## Task 1: Create `logger.py` with `RequestLogger`

**Files:**
- Create: `logger.py`
- Create: `tests/test_logger.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_logger.py`:

```python
import os
import json
import pytest
from unittest.mock import patch
from logger import RequestLogger


def test_request_logger_creates_log_file(tmp_path):
    with patch("logger.os.makedirs") as mock_mkdir, \
         patch("logger.logging.FileHandler") as mock_fh, \
         patch("logger.logging.StreamHandler"):
        mock_fh.return_value.level = 0
        mock_fh.return_value.setFormatter = lambda x: None
        logger = RequestLogger(42, "show me items")
        mock_mkdir.assert_called_once_with("logs", exist_ok=True)
        assert "42" in logger.log_file
    logger.close()


def test_request_logger_no_conversation_id(tmp_path):
    with patch("logger.os.makedirs"), \
         patch("logger.logging.FileHandler"), \
         patch("logger.logging.StreamHandler"):
        logger = RequestLogger(None, "hello")
        assert "no-conv" in logger.log_file
    logger.close()


def test_request_logger_debug_calls_underlying_logger():
    with patch("logger.os.makedirs"), \
         patch("logger.logging.FileHandler"), \
         patch("logger.logging.StreamHandler"):
        logger = RequestLogger(1, "test")

    with patch.object(logger._logger, "debug") as mock_debug:
        logger.debug("test message", layer="main", event="test_event", data={"k": "v"})
        mock_debug.assert_called_once()
        call_kwargs = mock_debug.call_args
        assert call_kwargs[1]["extra"]["layer"] == "main"
        assert call_kwargs[1]["extra"]["event"] == "test_event"
        assert call_kwargs[1]["extra"]["data"] == {"k": "v"}
    logger.close()


def test_request_logger_error_calls_underlying_logger():
    with patch("logger.os.makedirs"), \
         patch("logger.logging.FileHandler"), \
         patch("logger.logging.StreamHandler"):
        logger = RequestLogger(1, "test")

    with patch.object(logger._logger, "error") as mock_error:
        logger.error("boom", layer="main", event="err", data={"error": "oops"})
        mock_error.assert_called_once()
    logger.close()


def test_json_formatter_produces_valid_json():
    import logging
    from logger import JsonFormatter
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test", level=logging.DEBUG,
        pathname="", lineno=0, msg="hello",
        args=(), exc_info=None
    )
    record.layer = "http"
    record.event = "http_request"
    record.data = {"url": "http://example.com"}
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["layer"] == "http"
    assert parsed["event"] == "http_request"
    assert parsed["data"] == {"url": "http://example.com"}
    assert "ts" in parsed
    assert "level" in parsed


def test_banner_formatter_includes_layer_and_message():
    import logging
    from logger import BannerFormatter
    formatter = BannerFormatter()
    record = logging.LogRecord(
        name="test", level=logging.DEBUG,
        pathname="", lineno=0, msg="fetching items",
        args=(), exc_info=None
    )
    record.layer = "main"
    output = formatter.format(record)
    assert "[main]" in output
    assert "fetching items" in output
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest tests/test_logger.py -v
```

Expected: `ModuleNotFoundError: No module named 'logger'`

- [ ] **Step 3: Create `logger.py`**

```python
import logging
import json
import os
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "layer": getattr(record, "layer", "app"),
            "event": getattr(record, "event", record.getMessage()),
            "data": getattr(record, "data", {}),
        })


class BannerFormatter(logging.Formatter):
    def format(self, record):
        layer = getattr(record, "layer", "app")
        return f"  [{layer}] {record.getMessage()}"


class RequestLogger:
    def __init__(self, conversation_id, message: str):
        self.conversation_id = conversation_id
        self.start_time = datetime.now(timezone.utc)

        os.makedirs("logs", exist_ok=True)
        timestamp = self.start_time.strftime("%Y%m%d-%H%M%S")
        conv_label = str(conversation_id) if conversation_id is not None else "no-conv"
        self.log_file = f"logs/{conv_label}-{timestamp}.log"

        self._logger = logging.getLogger(f"request.{conv_label}.{timestamp}")
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(BannerFormatter())

        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JsonFormatter())

        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)

        self._print_banner(f"REQUEST  conversationId={conv_label}  msg=\"{message[:80]}\"")

    def _print_banner(self, text: str):
        line = "═" * 48
        print(f"\n{line}")
        print(f" {text}")
        print(f"{line}")

    def section(self, title: str):
        print(f"\n=== {title} ===")

    def debug(self, msg: str, layer: str = "app", event: str = "", data: dict = None):
        self._logger.debug(msg, extra={"layer": layer, "event": event or msg, "data": data or {}})

    def info(self, msg: str, layer: str = "app", event: str = "", data: dict = None):
        self._logger.info(msg, extra={"layer": layer, "event": event or msg, "data": data or {}})

    def error(self, msg: str, layer: str = "app", event: str = "", data: dict = None):
        self._logger.error(msg, extra={"layer": layer, "event": event or msg, "data": data or {}})

    def close(self, error: bool = False):
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        status = "REQUEST ERROR" if error else "REQUEST COMPLETE"
        self._print_banner(f"{status}  duration={elapsed:.2f}s")
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest tests/test_logger.py -v
```

Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
cd C:/Users/heene/Desktop/ez-mcp && git add logger.py tests/test_logger.py && git commit -m "feat: add RequestLogger with console banner + JSON file handlers"
```

---

## Task 2: Update `item_service.py` to accept and use logger

**Files:**
- Modify: `modules/items/item_service.py`
- Modify: `tests/test_item_service.py`

- [ ] **Step 1: Update `tests/test_item_service.py` to pass a mock logger**

Replace the entire file with:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_logger():
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.error = MagicMock()
    return logger


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
```

- [ ] **Step 2: Run updated tests to confirm they fail (missing logger param)**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest tests/test_item_service.py -v
```

Expected: `TypeError: get_all_items() takes 4 positional arguments but 5 were given`

- [ ] **Step 3: Update `modules/items/item_service.py`**

Replace entire file with:

```python
import httpx
from config import ITEMS_BASE_URL, TIMEOUT


async def get_all_items(page: int, size: int, filter_data: dict, token: str, logger) -> dict:
    url = f"{ITEMS_BASE_URL}/all?page={page}&size={size}"
    payload = {"active": True, **filter_data}
    logger.debug(f"POST {url}", layer="http", event="http_request", data={"method": "POST", "url": url, "payload": payload})
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        body = response.json()
        logger.debug(f"Response {response.status_code}", layer="http", event="http_response", data={"status": response.status_code, "body": body})
        return body


async def search_items(search_filter: dict, token: str, logger) -> dict:
    url = f"{ITEMS_BASE_URL}/search"
    logger.debug(f"POST {url}", layer="http", event="http_request", data={"method": "POST", "url": url, "payload": search_filter})
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json=search_filter, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        body = response.json()
        logger.debug(f"Response {response.status_code}", layer="http", event="http_response", data={"status": response.status_code, "body": body})
        return body


async def create_item(item: dict, token: str, logger) -> dict:
    url = ITEMS_BASE_URL
    logger.debug(f"POST {url}", layer="http", event="http_request", data={"method": "POST", "url": url, "payload": item})
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json=item, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        body = response.json()
        logger.debug(f"Response {response.status_code}", layer="http", event="http_response", data={"status": response.status_code, "body": body})
        return body


async def update_item(item_id: int, updates: dict, token: str, logger) -> dict:
    url = f"{ITEMS_BASE_URL}/{item_id}/update"
    logger.debug(f"POST {url}", layer="http", event="http_request", data={"method": "POST", "url": url, "payload": updates})
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json=updates, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        body = response.json()
        logger.debug(f"Response {response.status_code}", layer="http", event="http_response", data={"status": response.status_code, "body": body})
        return body


async def toggle_item_status(item_id: int, is_active: bool, token: str, logger) -> dict:
    active_str = "true" if is_active else "false"
    url = f"{ITEMS_BASE_URL}/{item_id}/status?active={active_str}"
    logger.debug(f"POST {url}", layer="http", event="http_request", data={"method": "POST", "url": url})
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json={}, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        body = response.json()
        logger.debug(f"Response {response.status_code}", layer="http", event="http_response", data={"status": response.status_code, "body": body})
        return body


def get_template_url() -> str:
    return f"{ITEMS_BASE_URL}/template"
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest tests/test_item_service.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
cd C:/Users/heene/Desktop/ez-mcp && git add modules/items/item_service.py tests/test_item_service.py && git commit -m "feat: add HTTP request/response logging to item_service"
```

---

## Task 3: Update `item_tools.py` to accept and pass logger

**Files:**
- Modify: `modules/items/item_tools.py`
- Modify: `tests/test_item_tools.py`

- [ ] **Step 1: Update `tests/test_item_tools.py` to pass a mock logger**

Replace entire file with:

```python
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
```

- [ ] **Step 2: Run updated tests to confirm they fail**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest tests/test_item_tools.py -v
```

Expected: `TypeError: _execute_get_all_items() takes 2 positional arguments but 3 were given`

- [ ] **Step 3: Update `modules/items/item_tools.py`**

Replace only the `_execute_*` function definitions (keep `ITEM_TOOLS` list unchanged, only function signatures change):

```python
import random
from modules.items.item_service import (
    get_all_items,
    search_items,
    create_item,
    update_item,
    toggle_item_status as toggle_item_status_svc,
    get_template_url,
)


async def _execute_get_all_items(args: dict, token: str, logger) -> str:
    try:
        filter_data = {
            k: v for k, v in {
                "itemType": args.get("itemType"),
                "brand": args.get("brand"),
                "category": args.get("category"),
                "active": args.get("active", True),
            }.items() if v is not None
        }
        data = await get_all_items(args.get("page", 0), args.get("size", 10), filter_data, token, logger)
        return str(data)
    except Exception as e:
        return f"Error fetching items: {str(e)}"


async def _execute_search_items(args: dict, token: str, logger) -> str:
    try:
        data = await search_items({"searchQuery": args["query"]}, token, logger)
        return str(data)
    except Exception as e:
        return f"Search failed: {str(e)}"


async def _execute_add_item(args: dict, token: str, logger) -> str:
    try:
        item_code = args.get("itemCode") or f"ITM-{random.randint(1000, 9999)}"
        payload = {**args, "itemCode": item_code, "isActive": True}
        await create_item(payload, token, logger)
        return f"Success! Created Item '{args['name']}' with Code: {item_code}."
    except Exception as e:
        return f"Failed to create item. Reason: {str(e)}"


async def _execute_edit_item(args: dict, token: str, logger) -> str:
    try:
        item_id = args.pop("id")
        await update_item(item_id, args, token, logger)
        return f"Successfully updated details for Item ID {item_id}."
    except Exception as e:
        return f"Update failed: {str(e)}"


async def _execute_toggle_status(args: dict, token: str, logger) -> str:
    try:
        await toggle_item_status_svc(args["id"], args["active"], token, logger)
        state = "Active" if args["active"] else "Inactive"
        return f"Item {args['id']} is now {state}."
    except Exception as e:
        return f"Status change failed: {str(e)}"


async def _execute_get_bulk_template(args: dict, token: str, logger) -> str:
    try:
        url = get_template_url()
        logger.debug(f"Template URL: {url}", layer="tool", event="template_url", data={"url": url})
        return f"You can download the template here: {url}"
    except Exception as e:
        return f"Error getting template: {str(e)}"


ITEM_TOOLS = [
    {
        "name": "get_all_items",
        "description": (
            "Browse the full inventory catalog. Use when the user asks to 'list', 'show', "
            "'browse', or 'filter' items. Supports filtering by Type (Goods/Services), "
            "Category, Brand, and Status."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number (starts at 0)", "default": 0},
                "size": {"type": "integer", "description": "Number of items per page", "default": 10},
                "itemType": {"type": "string", "enum": ["PRODUCT", "SERVICE"], "description": "Filter by Item Type"},
                "brand": {"type": "string", "description": "Filter by Brand Name"},
                "category": {"type": "string", "description": "Filter by Category"},
                "active": {"type": "boolean", "description": "Filter by Active status (default true)", "default": True},
            },
            "required": [],
        },
        "execute": _execute_get_all_items,
    },
    {
        "name": "search_items",
        "description": "Search for items using a specific keyword (matches Name or Description).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search keyword (e.g. 'Samsung', 'Cable')"},
            },
            "required": ["query"],
        },
        "execute": _execute_search_items,
    },
    {
        "name": "add_item",
        "description": "Create a new inventory item. REQUIRES: Name, Category, Unit, Purchase Price, and Selling Price.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Item Name"},
                "category": {"type": "string", "description": "Category (e.g., Electronics, Raw Material)"},
                "unitOfMeasure": {"type": "string", "description": "Unit (e.g., PCS, KG, BOX)"},
                "purchasePrice": {"type": "number", "description": "Buying Price (Cost)"},
                "sellingPrice": {"type": "number", "description": "Selling Price"},
                "itemType": {"type": "string", "enum": ["PRODUCT", "SERVICE"], "default": "PRODUCT"},
                "brand": {"type": "string"},
                "manufacturer": {"type": "string"},
                "itemCode": {"type": "string", "description": "Unique Item Code. Auto-generated if omitted."},
                "sku": {"type": "string"},
                "barcode": {"type": "string"},
                "hsnSacCode": {"type": "string"},
                "description": {"type": "string"},
                "taxPercentage": {"type": "number"},
                "discountPercentage": {"type": "number"},
            },
            "required": ["name", "category", "unitOfMeasure", "purchasePrice", "sellingPrice"],
        },
        "execute": _execute_add_item,
    },
    {
        "name": "edit_item",
        "description": "Update details of an existing item. You MUST identify the item by its numeric ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "The numeric ID of the item to update"},
                "name": {"type": "string"},
                "sellingPrice": {"type": "number"},
                "purchasePrice": {"type": "number"},
                "category": {"type": "string"},
                "brand": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["id"],
        },
        "execute": _execute_edit_item,
    },
    {
        "name": "toggle_item_status",
        "description": "Enable or Disable an item (Soft Delete).",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "The numeric ID of the item"},
                "active": {"type": "boolean", "description": "True to enable, False to disable"},
            },
            "required": ["id", "active"],
        },
        "execute": _execute_toggle_status,
    },
    {
        "name": "get_bulk_template",
        "description": "Get the download link for the Item Import Excel Template.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "execute": _execute_get_bulk_template,
    },
]
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest tests/test_item_tools.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
cd C:/Users/heene/Desktop/ez-mcp && git add modules/items/item_tools.py tests/test_item_tools.py && git commit -m "feat: thread logger through item_tools execute functions"
```

---

## Task 4: Update `tool_registry.py` to accept and use logger

**Files:**
- Modify: `ai/tool_registry.py`
- Modify: `tests/test_tool_registry.py`

- [ ] **Step 1: Update `tests/test_tool_registry.py` to pass a mock logger**

Replace entire file with:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_logger():
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.error = MagicMock()
    logger.section = MagicMock()
    return logger


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


async def test_execute_tool_routes_to_correct_tool(mock_logger):
    from ai.tool_registry import execute_tool

    with patch("modules.items.item_tools.search_items", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {"data": [{"name": "Cable"}]}
        result = await execute_tool("search_items", {"query": "Cable"}, "tok", mock_logger)

    mock_svc.assert_called_once_with({"searchQuery": "Cable"}, "tok", mock_logger)
    assert "Cable" in result


async def test_execute_tool_unknown_name_returns_error(mock_logger):
    from ai.tool_registry import execute_tool
    result = await execute_tool("nonexistent_tool", {}, "tok", mock_logger)
    assert "not found" in result
    mock_logger.error.assert_called_once()


async def test_execute_tool_logs_start_and_result(mock_logger):
    from ai.tool_registry import execute_tool

    with patch("modules.items.item_tools.get_template_url") as mock_url:
        mock_url.return_value = "http://example.com/template"
        await execute_tool("get_bulk_template", {}, "tok", mock_logger)

    assert mock_logger.debug.call_count >= 2
    first_call_kwargs = mock_logger.debug.call_args_list[0][1]
    assert first_call_kwargs["layer"] == "tool"
    assert first_call_kwargs["event"] == "tool_execute_start"


async def test_run_agent_loop_returns_reply_when_no_tool_calls(mock_logger):
    from ai.tool_registry import run_agent_loop

    mock_message = MagicMock()
    mock_message.tool_calls = None
    mock_message.content = "Here are your items."

    mock_response = MagicMock()
    mock_response.message = mock_message

    mock_ollama = AsyncMock()
    mock_ollama.chat.return_value = mock_response

    with patch("ai.tool_registry.OllamaAsyncClient", return_value=mock_ollama):
        result = await run_agent_loop([{"role": "user", "content": "show items"}], "tok", mock_logger)

    assert result == "Here are your items."
    assert mock_ollama.chat.call_count == 1
    mock_logger.section.assert_called_once_with("OLLAMA ITERATION 1")


async def test_run_agent_loop_executes_tool_and_loops(mock_logger):
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
        result = await run_agent_loop([{"role": "user", "content": "give me template"}], "tok", mock_logger)

    assert mock_ollama.chat.call_count == 2
    mock_exec.assert_called_once_with("get_bulk_template", {}, "tok", mock_logger)
    assert result == "Download link: http://example.com/template"


async def test_run_agent_loop_stops_at_max_iterations(mock_logger):
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
        result = await run_agent_loop([{"role": "user", "content": "loop"}], "tok", mock_logger)

    assert mock_ollama.chat.call_count == MAX_TOOL_ITERATIONS
    assert "maximum" in result.lower()
    mock_logger.error.assert_called_once()
```

- [ ] **Step 2: Run updated tests to confirm they fail**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest tests/test_tool_registry.py -v
```

Expected: `TypeError: run_agent_loop() takes 2 positional arguments but 3 were given`

- [ ] **Step 3: Update `ai/tool_registry.py`**

Replace entire file with:

```python
import json
from ollama import AsyncClient as OllamaAsyncClient
from modules.items.item_tools import ITEM_TOOLS

ALL_TOOLS = [
    *ITEM_TOOLS,
    # Future modules: *STOCK_TOOLS, *PURCHASE_TOOLS, *SALES_TOOLS
]

MAX_TOOL_ITERATIONS = 10


def get_tool_schemas() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            },
        }
        for tool in ALL_TOOLS
    ]


async def execute_tool(name: str, args: dict, token: str, logger) -> str:
    tool = next((t for t in ALL_TOOLS if t["name"] == name), None)
    if not tool:
        logger.error(f"Tool '{name}' not found", layer="tool", event="tool_not_found", data={"name": name})
        return f"Tool '{name}' not found"
    logger.debug(f"Executing: {name}", layer="tool", event="tool_execute_start", data={"name": name, "args": dict(args)})
    result = await tool["execute"](args, token, logger)
    logger.debug(f"Result: {str(result)[:200]}", layer="tool", event="tool_execute_done", data={"name": name, "result_preview": str(result)[:200]})
    return result


async def run_agent_loop(messages: list, token: str, logger) -> str:
    client = OllamaAsyncClient()
    tool_schemas = get_tool_schemas()

    for iteration in range(MAX_TOOL_ITERATIONS):
        logger.section(f"OLLAMA ITERATION {iteration + 1}")
        logger.debug(
            f"Sending {len(messages)} messages to phi4-mini",
            layer="ollama", event="ollama_request",
            data={"iteration": iteration + 1, "messages": messages},
        )

        response = await client.chat(model="phi4-mini", messages=messages, tools=tool_schemas)

        logger.debug(
            f"Raw response — has_tool_calls={bool(response.message.tool_calls)}",
            layer="ollama", event="ollama_response",
            data={"iteration": iteration + 1, "has_tool_calls": bool(response.message.tool_calls), "content": response.message.content},
        )

        if not response.message.tool_calls:
            logger.debug("No tool calls — returning final reply", layer="ollama", event="ollama_final_reply")
            return response.message.content

        messages.append(response.message)

        for tool_call in response.message.tool_calls:
            logger.debug(
                f"Tool call requested: {tool_call.function.name}({json.dumps(dict(tool_call.function.arguments))})",
                layer="ollama", event="tool_call_detected",
                data={"name": tool_call.function.name, "args": dict(tool_call.function.arguments)},
            )
            result = await execute_tool(tool_call.function.name, tool_call.function.arguments, token, logger)
            messages.append({"role": "tool", "content": result})

    logger.error("Reached max tool iterations", layer="ollama", event="max_iterations_reached", data={"max": MAX_TOOL_ITERATIONS})
    return "I reached the maximum number of steps. Please try a simpler query."
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest tests/test_tool_registry.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
cd C:/Users/heene/Desktop/ez-mcp && git add ai/tool_registry.py tests/test_tool_registry.py && git commit -m "feat: add per-iteration Ollama + tool call logging to tool_registry"
```

---

## Task 5: Update `main.py` to create and use `RequestLogger`

**Files:**
- Modify: `main.py`
- Modify: `tests/test_generate.py`

- [ ] **Step 1: Read current `tests/test_generate.py`**

```bash
cd C:/Users/heene/Desktop/ez-mcp && cat tests/test_generate.py
```

- [ ] **Step 2: Update `tests/test_generate.py`**

Replace entire file with:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_logger():
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.close = MagicMock()
    return logger


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
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest tests/test_generate.py -v
```

Expected: `ImportError` or `TypeError` — `RequestLogger` not imported in `main.py` yet

- [ ] **Step 4: Update `main.py`**

Replace entire file with:

```python
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import httpx

from config import CHAT_BASE_URL, TIMEOUT
from ai.tool_registry import run_agent_loop
from logger import RequestLogger

app = FastAPI(title="EZ MCP AI Worker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ez-inventory.onrender.com",
        "http://localhost:4200",
        "http://localhost:8080",
        "http://localhost:8085",
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class GenerateRequest(BaseModel):
    message: str
    conversationId: Optional[int] = None


async def get_chat_history(conversation_id: Optional[int], token: str, logger: RequestLogger) -> list:
    if not conversation_id:
        logger.debug("No conversationId — skipping history fetch", layer="main", event="history_skip")
        return []
    try:
        logger.debug(f"Fetching chat history for conversation {conversation_id}", layer="main", event="history_fetch_start")
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                f"{CHAT_BASE_URL}/{conversation_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
            )
            messages = response.json().get("data", [])
            logger.debug(
                f"Chat history loaded — {len(messages)} messages",
                layer="main", event="history_fetch_done",
                data={"count": len(messages)},
            )
            return [
                {"role": "user" if msg["sender"] == "user" else "assistant", "content": msg["content"]}
                for msg in messages
            ]
    except Exception as e:
        logger.error(
            f"Failed to fetch history: {e}\n{traceback.format_exc()}",
            layer="main", event="history_fetch_error",
            data={"error": str(e)},
        )
        return []


@app.get("/health")
async def health():
    return {
        "status": "UP",
        "service": "mcp-ai-worker-python",
        "model": "phi4-mini",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/v1/ai/generate")
async def generate(request: Request, body: GenerateRequest):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = auth_header.split(" ")[1] if " " in auth_header else auth_header
    logger = RequestLogger(body.conversationId, body.message)

    try:
        history = await get_chat_history(body.conversationId, token, logger)
        messages = [*history, {"role": "user", "content": body.message}]
        logger.debug(
            "Starting agent loop",
            layer="main", event="agent_loop_start",
            data={"total_messages": len(messages)},
        )
        reply = await run_agent_loop(messages, token, logger)
        logger.info(
            f"Reply sent: {reply[:100]}",
            layer="main", event="reply_sent",
            data={"reply_preview": reply[:100]},
        )
        logger.close()
        return {"reply": reply}
    except Exception as e:
        logger.error(
            f"Unhandled error: {e}\n{traceback.format_exc()}",
            layer="main", event="unhandled_error",
            data={"error": str(e), "traceback": traceback.format_exc()},
        )
        logger.close(error=True)
        return {"reply": "I encountered an error with the local model service."}


if __name__ == "__main__":
    import uvicorn
    from config import PORT
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest tests/test_generate.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Run the full test suite**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python -m pytest -v
```

Expected: All tests across all files PASS

- [ ] **Step 7: Commit**

```bash
cd C:/Users/heene/Desktop/ez-mcp && git add main.py tests/test_generate.py && git commit -m "feat: wire RequestLogger into main.py — full request lifecycle logging"
```

---

## Task 6: Smoke Test

- [ ] **Step 1: Start the server**

```bash
cd C:/Users/heene/Desktop/ez-mcp && python main.py
```

- [ ] **Step 2: Send a test request**

In a separate terminal:

```bash
curl -X POST http://localhost:8085/v1/ai/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{"message": "show me all items", "conversationId": 1}'
```

- [ ] **Step 3: Verify console output**

Expected console output includes:
```
════════════════════════════════════════════════
 REQUEST  conversationId=1  msg="show me all items"
════════════════════════════════════════════════
  [main] No conversationId — skipping history fetch   (or history logs)
  [main] Starting agent loop

=== OLLAMA ITERATION 1 ===
  [ollama] Sending 1 messages to phi4-mini
  ...
```

- [ ] **Step 4: Verify log file created**

```bash
ls C:/Users/heene/Desktop/ez-mcp/logs/
```

Expected: A file like `1-20260417-102301.log` exists

- [ ] **Step 5: Verify JSON log file contents**

```bash
head -5 C:/Users/heene/Desktop/ez-mcp/logs/1-*.log
```

Expected: Each line is valid JSON with `ts`, `level`, `layer`, `event`, `data` fields
