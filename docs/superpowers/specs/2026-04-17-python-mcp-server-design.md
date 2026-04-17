# Python FastAPI MCP Server — Design Spec
Date: 2026-04-17

## Overview

Port the existing TypeScript/Express MCP AI worker to Python using FastAPI. The server sits between the Spring backend and Ollama (phi4-mini local LLM), receives user messages, runs an agentic tool-calling loop against the inventory REST API, and returns a human-readable reply.

---

## 1. Project Structure

```
ez-mcp-python/
├── main.py                        # FastAPI app, /health, /v1/ai/generate
├── config.py                      # ENV vars, base URL, shared httpx client
├── ai/
│   └── tool_registry.py           # Registers all tools, runs agentic loop
├── modules/
│   └── items/
│       ├── item_service.py        # httpx calls to inventory REST API
│       ├── item_tools.py          # Tool definitions (name, description, schema, execute)
│       └── item_types.py          # Pydantic models (ItemModel, ItemSearchFilter)
├── requirements.txt
└── .env
```

Adding a new module (e.g., Stock, Purchases) = create a new folder under `modules/`, define tools, register in `tool_registry.py`. No changes to core.

---

## 2. API Endpoints

### GET /health
Returns service status, model name, and timestamp.

```json
{ "status": "UP", "service": "mcp-ai-worker-python", "model": "phi4-mini", "timestamp": "..." }
```

### POST /v1/ai/generate
**Request:**
```json
{ "message": "Show me all active products", "conversationId": 42 }
```
**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{ "reply": "Here are your active products: ..." }
```

---

## 3. Data Flow

```
UI
 │
 ▼
Backend (Spring) ──► POST /v1/ai/generate  (message, conversationId, Bearer token)
                          │
                          ▼
                     1. Fetch chat history from backend
                     2. Build messages: [history + user message]
                     3. Call Ollama (phi4-mini) with tool schemas
                          │
                    ┌─────▼──────┐
                    │ Tool call? │
                    └─────┬──────┘
                   yes    │    no
                    ▼     │     ▼
              Execute    │   Return final reply
              API tool   │   (UI-friendly string)
              Append     │
              result     │
              Loop back──┘ (max 10 iterations)
                    │
                    ▼
          { "reply": "Here are your items..." }
                    │
                    ▼
             Backend → UI
```

---

## 4. Tool Definition Pattern

Each tool is a plain Python dict with an async `execute` function:

```python
{
    "name": "get_all_items",
    "description": "Browse inventory catalog. Use when user asks to list, show, or filter items.",
    "parameters": {
        "type": "object",
        "properties": {
            "page":     {"type": "integer", "default": 0},
            "size":     {"type": "integer", "default": 10},
            "itemType": {"type": "string", "enum": ["PRODUCT", "SERVICE"]},
            "brand":    {"type": "string"},
            "category": {"type": "string"},
            "active":   {"type": "boolean", "default": True}
        },
        "required": []
    },
    "execute": <async function(args: dict, token: str) -> str>
}
```

`tool_registry.py` strips `execute` before sending schemas to Ollama, then routes Ollama's tool call back to the correct `execute` function.

### Items Module Tools (6 tools)
| Tool | Description |
|---|---|
| `get_all_items` | Paginated + filtered browse of inventory catalog |
| `search_items` | Keyword search by name or description |
| `add_item` | Create a new inventory item |
| `edit_item` | Update an existing item by numeric ID |
| `toggle_item_status` | Enable or disable an item (soft delete) |
| `get_bulk_template` | Returns the Excel import template download URL |

---

## 5. Agentic Loop (tool_registry.py)

```python
MAX_TOOL_ITERATIONS = 10

async def run_agent_loop(messages, tools, token):
    for _ in range(MAX_TOOL_ITERATIONS):
        response = ollama.chat(model="phi4-mini", messages=messages, tools=tool_schemas)
        if not response.message.tool_calls:
            return response.message.content  # done
        for tool_call in response.message.tool_calls:
            result = await execute_tool(tool_call.name, tool_call.args, token)
            messages.append(response.message)
            messages.append({"role": "tool", "content": result})
    return "I reached the maximum number of steps. Please try a simpler query."
```

---

## 6. Error Handling

| Scenario | Behavior |
|---|---|
| Missing auth header | 401 returned immediately, no Ollama call |
| Tool execution error | Error string returned as tool result; loop continues |
| API 401 Unauthorized | Propagated as tool error string |
| API 404 / 5xx | Meaningful error string returned to Ollama |
| httpx timeout (5s) | Caught, returned as tool error string |
| Ollama unreachable | 500 `{ "reply": "Local AI service unavailable" }` |
| Loop cap reached | Graceful message returned to user |

Key principle: errors never crash the loop — Ollama receives them as tool results and responds gracefully.

---

## 7. Dependencies (requirements.txt)

```
fastapi
uvicorn
httpx
ollama
python-dotenv
pydantic
```

---

## 8. Environment Variables (.env)

```
PORT=8085
SERVER_URL=http://localhost:8080
```

---

## 9. Future Modules

To add Stock, Purchases, Sales etc.:
1. Create `modules/<module>/` with `service.py`, `tools.py`, `types.py`
2. Import and spread tools into `all_tools` list in `tool_registry.py`
3. No changes to `main.py` or the agentic loop
