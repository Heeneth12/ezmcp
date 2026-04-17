# Detailed Logging Design

**Date:** 2026-04-17  
**Status:** Approved

## Goal

Add full-debug, layer-by-layer logging to the ez-mcp FastAPI application. Every request gets its own log file. Console shows human-readable banners; file stores structured JSON.

## Architecture

A `RequestLogger` class in `logger.py` (project root) is instantiated once per incoming request. It owns two handlers on a Python `logging.Logger`:

- `StreamHandler` — console output, plain text with `=== BANNER ===` visual separators
- `FileHandler` — writes to `logs/<conversationId>-<timestamp>.log`, one JSON object per line

The `RequestLogger` instance is passed as a parameter through the call stack:
```
main.py → run_agent_loop(logger) → execute_tool(logger) → item_service functions(logger)
```

## Log Layers

| Layer | Events logged |
|---|---|
| `main.py` | Request received (conversationId, message snippet), history fetch start/result, agent loop start, final reply, any exception with full traceback |
| `tool_registry.py` | Ollama iteration number, messages sent, raw response, tool calls detected (name + args), tool results, final answer |
| `item_service.py` | HTTP method + URL + payload, response status code + body, HTTP errors |
| `item_tools.py` | Pass-through to service — no additional logging needed |

## Console Format

```
════════════════════════════════════════
 REQUEST  conversationId=42  msg="show me all items"
════════════════════════════════════════
  [main]   Fetching chat history for conversation 42
  [main]   Chat history loaded — 3 messages
  [main]   Starting agent loop

=== OLLAMA ITERATION 1 ===
  [ollama] Sending 4 messages to phi4-mini
  [ollama] Tool call requested: get_all_items({"page": 0, "size": 10})
  [tool]   Executing: get_all_items
  [http]   POST http://localhost:8080/v1/items/all?page=0&size=10
  [http]   Response 200 — body: {...}
  [tool]   Result: {...}

=== OLLAMA ITERATION 2 ===
  [ollama] No tool calls — returning final reply
  [main]   Reply sent

════════════════════════════════════════
 REQUEST COMPLETE  duration=1.23s
════════════════════════════════════════
```

## JSON File Format

One JSON object per line:
```json
{"ts": "2026-04-17T10:23:01Z", "level": "DEBUG", "layer": "http", "event": "response", "data": {"status": 200, "url": "...", "body": {}}}
```

Fields: `ts` (ISO UTC), `level` (DEBUG/INFO/ERROR), `layer` (main/ollama/tool/http), `event` (short label), `data` (arbitrary dict).

## Error Handling

All bare `except Exception` blocks are replaced with `except Exception as e` that logs:
- Exception type and message
- Full traceback (`traceback.format_exc()`)
- To both console and file

## File Changes

| File | Change |
|---|---|
| `logger.py` | **New** — `RequestLogger` class |
| `main.py` | Instantiate `RequestLogger`, pass to `run_agent_loop`, log request/reply/errors |
| `ai/tool_registry.py` | Accept `logger` param, log Ollama iterations + tool calls |
| `modules/items/item_service.py` | Accept `logger` param, log HTTP calls + responses |
| `modules/items/item_tools.py` | Accept and pass `logger` to service functions |

## Out of Scope

- Log shipping to external services (Datadog, CloudWatch)
- Log-level configuration via env var (always DEBUG for now)
- Changes to `config.py`, `item_types.py`, or test files
