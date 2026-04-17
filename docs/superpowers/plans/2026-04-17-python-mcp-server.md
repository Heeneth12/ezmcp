# Python FastAPI MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python FastAPI server that receives inventory-related user messages, runs an agentic Ollama tool-calling loop against the inventory REST API, and returns a human-readable reply.

**Architecture:** FastAPI app exposes `/health` and `/v1/ai/generate`. On each request, chat history is fetched from the Spring backend, then an agentic loop calls Ollama (phi4-mini) with tool schemas. Ollama triggers tool executions (REST API calls), results are fed back, loop repeats until Ollama returns a plain reply (max 10 iterations).

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, httpx (async HTTP), ollama (Python SDK), Pydantic v2, python-dotenv, pytest, pytest-asyncio

---

## File Map

| File | Responsibility |
|---|---|
| `main.py` | FastAPI app, CORS, `/health`, `/v1/ai/generate`, chat history fetch |
| `config.py` | ENV vars, base URLs, timeout constant |
| `ai/__init__.py` | Empty package marker |
| `ai/tool_registry.py` | Combines all tools, builds Ollama schemas, runs agentic loop |
| `modules/__init__.py` | Empty package marker |
| `modules/items/__init__.py` | Empty package marker |
| `modules/items/item_types.py` | Pydantic models: `ItemModel`, `ItemSearchFilter` |
| `modules/items/item_service.py` | Async httpx calls to inventory REST API |
| `modules/items/item_tools.py` | 6 tool dicts with `name`, `description`, `parameters`, `execute` |
| `requirements.txt` | All dependencies pinned |
| `.env` | `PORT`, `SERVER_URL` |
| `tests/__init__.py` | Empty package marker |
| `tests/test_health.py` | /health endpoint test |
| `tests/test_generate.py` | /v1/ai/generate endpoint tests |
| `tests/test_item_service.py` | item_service.py unit tests (mock httpx) |
| `tests/test_item_tools.py` | item_tools.py unit tests (mock service functions) |
| `tests/test_tool_registry.py` | tool_registry.py unit tests (mock ollama) |

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `ai/__init__.py`
- Create: `modules/__init__.py`
- Create: `modules/items/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn==0.30.6
httpx==0.27.2
ollama==0.3.3
pydantic==2.9.2
python-dotenv==1.0.1
pytest==8.3.3
pytest-asyncio==0.24.0
```

- [ ] **Step 2: Create .env**

```
PORT=8085
SERVER_URL=http://localhost:8080
```

- [ ] **Step 3: Create package marker files**

Create these four files, each empty:
- `ai/__init__.py`
- `modules/__init__.py`
- `modules/items/__init__.py`
- `tests/__init__.py`

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env ai/__init__.py modules/__init__.py modules/items/__init__.py tests/__init__.py
git commit -m "chore: scaffold Python FastAPI MCP server project"
```

---

## Task 2: Config Module

**Files:**
- Create: `config.py`

- [ ] **Step 1: Create config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8080")
PORT = int(os.getenv("PORT", 8085))
TIMEOUT = 5.0

ITEMS_BASE_URL = f"{SERVER_URL}/v1/items"
CHAT_BASE_URL = f"{SERVER_URL}/v1/mcp/chat"
```

- [ ] **Step 2: Verify config loads**

```bash
python -c "from config import SERVER_URL, ITEMS_BASE_URL, CHAT_BASE_URL, TIMEOUT; print(SERVER_URL, ITEMS_BASE_URL, CHAT_BASE_URL, TIMEOUT)"
```

Expected output:
```
http://localhost:8080 http://localhost:8080/v1/items http://localhost:8080/v1/mcp/chat 5.0
```

- [ ] **Step 3: Commit**

```bash
git add config.py
git commit -m "feat: add config module for env vars and base URLs"
```

---

## Task 3: Pydantic Models

**Files:**
- Create: `modules/items/item_types.py`

- [ ] **Step 1: Create item_types.py**

```python
from pydantic import BaseModel
from typing import Literal, Optional


class ItemModel(BaseModel):
    id: Optional[int] = None
    name: str
    itemCode: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    itemType: Literal["SERVICE", "PRODUCT"] = "PRODUCT"
    imageUrl: Optional[str] = None
    category: str
    unitOfMeasure: str
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    purchasePrice: float
    sellingPrice: float
    mrp: Optional[float] = None
    taxPercentage: Optional[float] = None
    discountPercentage: Optional[float] = None
    hsnSacCode: Optional[str] = None
    description: Optional[str] = None
    isActive: bool = True


class ItemSearchFilter(BaseModel):
    searchQuery: Optional[str] = None
    active: Optional[bool] = None
    itemType: Optional[Literal["SERVICE", "PRODUCT"]] = None
    brand: Optional[str] = None
    category: Optional[str] = None
```

- [ ] **Step 2: Verify models parse correctly**

```bash
python -c "
from modules.items.item_types import ItemModel, ItemSearchFilter
item = ItemModel(name='Test', itemCode='ITM-001', category='Electronics', unitOfMeasure='PCS', purchasePrice=10.0, sellingPrice=15.0)
print(item.model_dump())
f = ItemSearchFilter(active=True, itemType='PRODUCT')
print(f.model_dump())
"
```

Expected: Both dicts print without errors.

- [ ] **Step 3: Commit**

```bash
git add modules/items/item_types.py
git commit -m "feat: add Pydantic models for Item and ItemSearchFilter"
```

---

## Task 4: Item Service

**Files:**
- Create: `modules/items/item_service.py`
- Create: `tests/test_item_service.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_item_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_get_all_items_posts_to_correct_url():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [], "total": 0}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("modules.items.item_service.httpx.AsyncClient", return_value=mock_client):
        from modules.items.item_service import get_all_items
        result = await get_all_items(0, 10, {"active": True}, "tok123")

    call_url = mock_client.post.call_args[0][0]
    assert "page=0&size=10" in call_url
    assert mock_client.post.call_args[1]["headers"]["Authorization"] == "Bearer tok123"
    assert result == {"data": [], "total": 0}


@pytest.mark.asyncio
async def test_search_items_posts_filter():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"name": "Cable"}]}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("modules.items.item_service.httpx.AsyncClient", return_value=mock_client):
        from modules.items.item_service import search_items
        result = await search_items({"searchQuery": "Cable"}, "tok123")

    assert mock_client.post.call_args[1]["json"] == {"searchQuery": "Cable"}
    assert result == {"data": [{"name": "Cable"}]}


@pytest.mark.asyncio
async def test_create_item_posts_payload():
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
        result = await create_item(payload, "tok123")

    assert mock_client.post.call_args[1]["json"] == payload
    assert result == {"id": 1, "name": "Widget"}


@pytest.mark.asyncio
async def test_toggle_item_status_encodes_bool_lowercase():
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("modules.items.item_service.httpx.AsyncClient", return_value=mock_client):
        from modules.items.item_service import toggle_item_status
        await toggle_item_status(42, False, "tok123")

    call_url = mock_client.post.call_args[0][0]
    assert "active=false" in call_url


def test_get_template_url_returns_correct_url():
    from modules.items.item_service import get_template_url
    url = get_template_url()
    assert url.endswith("/v1/items/template")
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_item_service.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` — item_service.py does not exist yet.

- [ ] **Step 3: Create item_service.py**

```python
import httpx
from config import ITEMS_BASE_URL, TIMEOUT


async def get_all_items(page: int, size: int, filter_data: dict, token: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{ITEMS_BASE_URL}/all?page={page}&size={size}",
            json={"active": True, **filter_data},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


async def search_items(search_filter: dict, token: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{ITEMS_BASE_URL}/search",
            json=search_filter,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


async def create_item(item: dict, token: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            ITEMS_BASE_URL,
            json=item,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


async def update_item(item_id: int, updates: dict, token: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{ITEMS_BASE_URL}/{item_id}/update",
            json=updates,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


async def toggle_item_status(item_id: int, is_active: bool, token: str) -> dict:
    active_str = "true" if is_active else "false"
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{ITEMS_BASE_URL}/{item_id}/status?active={active_str}",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


def get_template_url() -> str:
    return f"{ITEMS_BASE_URL}/template"
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_item_service.py -v
```

Expected: 5 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add modules/items/item_service.py tests/test_item_service.py
git commit -m "feat: add item service with async httpx calls to inventory API"
```

---

## Task 5: Item Tools

**Files:**
- Create: `modules/items/item_tools.py`
- Create: `tests/test_item_tools.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_item_tools.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch


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


@pytest.mark.asyncio
async def test_get_all_items_execute_calls_service():
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "get_all_items")

    with patch("modules.items.item_tools.get_all_items", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {"data": []}
        result = await tool["execute"]({"page": 0, "size": 10, "active": True}, "tok")

    mock_svc.assert_called_once_with(0, 10, {"active": True}, "tok")
    assert "data" in result


@pytest.mark.asyncio
async def test_get_all_items_execute_handles_error():
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "get_all_items")

    with patch("modules.items.item_tools.get_all_items", new_callable=AsyncMock) as mock_svc:
        mock_svc.side_effect = Exception("Connection refused")
        result = await tool["execute"]({}, "tok")

    assert "Error" in result


@pytest.mark.asyncio
async def test_search_items_execute_calls_service():
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "search_items")

    with patch("modules.items.item_tools.search_items", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {"data": [{"name": "Cable"}]}
        result = await tool["execute"]({"query": "Cable"}, "tok")

    mock_svc.assert_called_once_with({"searchQuery": "Cable"}, "tok")
    assert "Cable" in result


@pytest.mark.asyncio
async def test_add_item_generates_code_when_missing():
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "add_item")

    with patch("modules.items.item_tools.create_item", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {"id": 1}
        result = await tool["execute"](
            {"name": "Widget", "category": "General", "unitOfMeasure": "PCS",
             "purchasePrice": 5.0, "sellingPrice": 10.0},
            "tok"
        )

    call_payload = mock_svc.call_args[0][0]
    assert call_payload["itemCode"].startswith("ITM-")
    assert "Success" in result


@pytest.mark.asyncio
async def test_edit_item_execute_calls_service():
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "edit_item")

    with patch("modules.items.item_tools.update_item", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {}
        result = await tool["execute"]({"id": 7, "name": "Updated"}, "tok")

    mock_svc.assert_called_once_with(7, {"name": "Updated"}, "tok")
    assert "7" in result


@pytest.mark.asyncio
async def test_toggle_item_status_execute_calls_service():
    from modules.items.item_tools import ITEM_TOOLS
    tool = next(t for t in ITEM_TOOLS if t["name"] == "toggle_item_status")

    with patch("modules.items.item_tools.toggle_item_status_svc", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {}
        result = await tool["execute"]({"id": 3, "active": False}, "tok")

    mock_svc.assert_called_once_with(3, False, "tok")
    assert "Inactive" in result


def test_get_bulk_template_execute_returns_url():
    from modules.items.item_tools import ITEM_TOOLS
    import asyncio
    tool = next(t for t in ITEM_TOOLS if t["name"] == "get_bulk_template")

    with patch("modules.items.item_tools.get_template_url") as mock_url:
        mock_url.return_value = "http://localhost:8080/v1/items/template"
        result = asyncio.get_event_loop().run_until_complete(tool["execute"]({}, "tok"))

    assert "http://localhost:8080/v1/items/template" in result
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_item_tools.py -v
```

Expected: `ModuleNotFoundError` — item_tools.py does not exist yet.

- [ ] **Step 3: Create item_tools.py**

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


async def _execute_get_all_items(args: dict, token: str) -> str:
    try:
        filter_data = {
            k: v for k, v in {
                "itemType": args.get("itemType"),
                "brand": args.get("brand"),
                "category": args.get("category"),
                "active": args.get("active", True),
            }.items() if v is not None
        }
        data = await get_all_items(args.get("page", 0), args.get("size", 10), filter_data, token)
        return str(data)
    except Exception as e:
        return f"Error fetching items: {str(e)}"


async def _execute_search_items(args: dict, token: str) -> str:
    try:
        data = await search_items({"searchQuery": args["query"]}, token)
        return str(data)
    except Exception as e:
        return f"Search failed: {str(e)}"


async def _execute_add_item(args: dict, token: str) -> str:
    try:
        item_code = args.get("itemCode") or f"ITM-{random.randint(1000, 9999)}"
        payload = {**args, "itemCode": item_code, "isActive": True}
        await create_item(payload, token)
        return f"Success! Created Item '{args['name']}' with Code: {item_code}."
    except Exception as e:
        return f"Failed to create item. Reason: {str(e)}"


async def _execute_edit_item(args: dict, token: str) -> str:
    try:
        item_id = args.pop("id")
        await update_item(item_id, args, token)
        return f"Successfully updated details for Item ID {item_id}."
    except Exception as e:
        return f"Update failed: {str(e)}"


async def _execute_toggle_status(args: dict, token: str) -> str:
    try:
        await toggle_item_status_svc(args["id"], args["active"], token)
        state = "Active" if args["active"] else "Inactive"
        return f"Item {args['id']} is now {state}."
    except Exception as e:
        return f"Status change failed: {str(e)}"


async def _execute_get_bulk_template(args: dict, token: str) -> str:
    try:
        url = get_template_url()
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

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_item_tools.py -v
```

Expected: 9 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add modules/items/item_tools.py tests/test_item_tools.py
git commit -m "feat: add item tools with agentic execute functions"
```

---

## Task 6: Tool Registry + Agentic Loop

**Files:**
- Create: `ai/tool_registry.py`
- Create: `tests/test_tool_registry.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_tool_registry.py`:

```python
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


@pytest.mark.asyncio
async def test_execute_tool_routes_to_correct_tool():
    from ai.tool_registry import execute_tool

    with patch("modules.items.item_tools._execute_search_items", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = "results"
        result = await execute_tool("search_items", {"query": "Cable"}, "tok")

    mock_exec.assert_called_once_with({"query": "Cable"}, "tok")
    assert result == "results"


@pytest.mark.asyncio
async def test_execute_tool_unknown_name_returns_error():
    from ai.tool_registry import execute_tool
    result = await execute_tool("nonexistent_tool", {}, "tok")
    assert "not found" in result


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_tool_registry.py -v
```

Expected: `ModuleNotFoundError` — tool_registry.py does not exist yet.

- [ ] **Step 3: Create ai/tool_registry.py**

```python
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


async def execute_tool(name: str, args: dict, token: str) -> str:
    tool = next((t for t in ALL_TOOLS if t["name"] == name), None)
    if not tool:
        return f"Tool '{name}' not found"
    return await tool["execute"](args, token)


async def run_agent_loop(messages: list, token: str) -> str:
    client = OllamaAsyncClient()
    tool_schemas = get_tool_schemas()

    for _ in range(MAX_TOOL_ITERATIONS):
        response = await client.chat(
            model="phi4-mini",
            messages=messages,
            tools=tool_schemas,
        )

        if not response.message.tool_calls:
            return response.message.content

        messages.append(response.message)

        for tool_call in response.message.tool_calls:
            result = await execute_tool(
                tool_call.function.name,
                tool_call.function.arguments,
                token,
            )
            messages.append({"role": "tool", "content": result})

    return "I reached the maximum number of steps. Please try a simpler query."
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_tool_registry.py -v
```

Expected: 7 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add ai/tool_registry.py tests/test_tool_registry.py
git commit -m "feat: add tool registry and agentic Ollama loop"
```

---

## Task 7: FastAPI App

**Files:**
- Create: `main.py`
- Create: `tests/test_health.py`
- Create: `tests/test_generate.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_health.py`:

```python
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
```

Create `tests/test_generate.py`:

```python
import pytest
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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_health.py tests/test_generate.py -v
```

Expected: `ModuleNotFoundError` — main.py does not exist yet.

- [ ] **Step 3: Create main.py**

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import httpx

from config import CHAT_BASE_URL, TIMEOUT
from ai.tool_registry import run_agent_loop

app = FastAPI(title="EZ MCP AI Worker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ez-inventory.onrender.com",
        "http://localhost:4200",
        "http://localhost:8080",
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class GenerateRequest(BaseModel):
    message: str
    conversationId: Optional[int] = None


async def get_chat_history(conversation_id: Optional[int], token: str) -> list:
    if not conversation_id:
        return []
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                f"{CHAT_BASE_URL}/{conversation_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
            )
            messages = response.json().get("data", [])
            return [
                {
                    "role": "user" if msg["sender"] == "user" else "assistant",
                    "content": msg["content"],
                }
                for msg in messages
            ]
    except Exception:
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

    try:
        history = await get_chat_history(body.conversationId, token)
        messages = [*history, {"role": "user", "content": body.message}]
        reply = await run_agent_loop(messages, token)
        return {"reply": reply}
    except Exception:
        return {"reply": "I encountered an error with the local model service."}


if __name__ == "__main__":
    import uvicorn
    from config import PORT
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
```

- [ ] **Step 4: Run all tests — verify they pass**

```bash
pytest -v
```

Expected: All tests PASSED (no failures).

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_health.py tests/test_generate.py
git commit -m "feat: add FastAPI app with /health and /v1/ai/generate endpoints"
```

---

## Task 8: Smoke Test

**Files:** None — verification only.

- [ ] **Step 1: Start the server**

```bash
python main.py
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8085
```

- [ ] **Step 2: Hit /health**

In a new terminal:
```bash
curl http://localhost:8085/health
```

Expected:
```json
{"status":"UP","service":"mcp-ai-worker-python","model":"phi4-mini","timestamp":"..."}
```

- [ ] **Step 3: Hit /v1/ai/generate**

```bash
curl -X POST http://localhost:8085/v1/ai/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{"message": "show me all products"}'
```

Expected: `{"reply": "..."}` — Ollama responds (may take a few seconds).

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete Python FastAPI MCP server with Items module"
```

---

## Adding Future Modules (Reference)

When Stock module is ready:
1. Create `modules/stock/stock_service.py`, `stock_tools.py`, `stock_types.py`
2. In `ai/tool_registry.py`, add:
```python
from modules.stock.stock_tools import STOCK_TOOLS
ALL_TOOLS = [*ITEM_TOOLS, *STOCK_TOOLS]
```
3. No other files need to change.
