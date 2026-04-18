import json
from ollama import AsyncClient as OllamaAsyncClient
from modules.items.item_tools import ITEM_TOOLS
from modules.knowledge.knowledge_tools import search_documentation_tool

ALL_TOOLS = [
    *ITEM_TOOLS,
    search_documentation_tool
    # Future modules: *STOCK_TOOLS, *PURCHASE_TOOLS, *SALES_TOOLS
]

MAX_TOOL_ITERATIONS = 10

SYSTEM_PROMPT = """You are EZ, an intelligent inventory management assistant for EZ Inventory — an enterprise Inventory & Supply Chain Management system.

You have access to tools that interact with the inventory system. 

## STRICT RULES — FOLLOW WITHOUT EXCEPTION:
1. ALWAYS call a tool immediately for any inventory-related request. NEVER ask for clarification first.
2. NEVER show JSON, code blocks, or function signatures to the user.
3. NEVER say "I will do X" or "I can do X" — just DO it by calling the tool right away.
4. Make smart assumptions using the defaults below when details are missing.
5. After a tool returns results, summarize them in a clean, friendly, human-readable format.
6. NEVER expose raw API responses or dict/list dumps to the user.

## DEFAULT ASSUMPTIONS (use when not specified):
- page = 0
- size = 10
- active = true
- itemType = not filtered (omit unless specified)

## INTENT → TOOL MAPPING:
- "browse / list / show / catalog / all items" → call get_all_items immediately
- "search [keyword]" → call search_items immediately
- "add / create item" → call add_item with provided details
- "edit / update item" → call edit_item with the item ID
- "enable / disable / toggle item" → call toggle_item_status
- "bulk template / import template" → call get_bulk_template

## RESPONSE FORMAT:
- Summarize results in a clean, readable way (e.g., a short list with key fields).
- Highlight important fields: Name, Code, Category, Price, Status.
- If no results, say so clearly and suggest next steps.
- Keep responses concise and business-friendly."""


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
        logger.error(
            f"Tool '{name}' not found",
            layer="tool", event="tool_not_found",
            data={"name": name},
        )
        return f"Tool '{name}' not found"

    logger.debug(
        f"Executing: {name}",
        layer="tool", event="tool_execute_start",
        data={"name": name, "args": dict(args)},
    )
    try:
        result = await tool["execute"](args, token, logger)
    except Exception as e:
        logger.error(
            f"Tool '{name}' raised an exception: {e}",
            layer="tool", event="tool_execute_error",
            data={"name": name, "error": str(e)},
        )
        return f"Tool '{name}' encountered an error: {str(e)}"

    logger.debug(
        f"Result: {str(result)[:200]}",
        layer="tool", event="tool_execute_done",
        data={"name": name, "result_preview": str(result)[:200]},
    )
    return result


def _normalize_response(raw):
    """
    Normalize ollama response — handles both dict and typed object responses.
    Returns (msg, tool_calls, content)
    """
    if isinstance(raw, dict):
        msg = raw.get("message", {})
        tool_calls = msg.get("tool_calls") or []
        content = msg.get("content", "")
    else:
        msg = raw.message
        tool_calls = getattr(raw.message, "tool_calls", None) or []
        content = getattr(raw.message, "content", "") or ""
    return msg, tool_calls, content


def _normalize_tool_call(tool_call):
    """
    Normalize a single tool call — handles both dict and typed object.
    Returns (name, args)
    """
    if isinstance(tool_call, dict):
        fn = tool_call.get("function", {})
        name = fn.get("name")
        args = fn.get("arguments", {})
    else:
        name = tool_call.function.name
        args = tool_call.function.arguments
    return name, args


def _to_dict_message(msg, content, tool_calls):
    """
    Always return a plain dict for appending to message history.
    """
    if isinstance(msg, dict):
        return msg
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": tool_calls,
    }


async def run_agent_loop(messages: list, token: str, logger) -> str:
    client = OllamaAsyncClient()
    tool_schemas = get_tool_schemas()

    # Prepend system prompt — keeps it separate from user history
    full_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages,
    ]

    for iteration in range(MAX_TOOL_ITERATIONS):
        logger.section(f"OLLAMA ITERATION {iteration + 1}")
        logger.debug(
            f"Sending {len(full_messages)} messages to model",
            layer="ollama", event="ollama_request",
            data={"iteration": iteration + 1, "messages": full_messages},
        )

        try:
            raw = await client.chat(
                model="qwen2.5:3b",
                messages=full_messages,
                tools=tool_schemas,
            )
        except Exception as e:
            logger.error(
                f"Ollama chat error: {e}",
                layer="ollama", event="ollama_error",
                data={"error": str(e)},
            )
            return "I'm having trouble connecting to the AI model. Please try again shortly."

        msg, tool_calls, content = _normalize_response(raw)

        logger.debug(
            f"Raw response — has_tool_calls={bool(tool_calls)}",
            layer="ollama", event="ollama_response",
            data={
                "iteration": iteration + 1,
                "has_tool_calls": bool(tool_calls),
                "content": content,
            },
        )

        # No tool calls — this is the final reply
        if not tool_calls:
            logger.debug(
                "No tool calls — returning final reply",
                layer="ollama", event="ollama_final_reply",
            )
            return content or "I couldn't generate a response. Please try again."

        # Append assistant message to history
        full_messages.append(_to_dict_message(msg, content, tool_calls))

        # Execute each tool call
        for tool_call in tool_calls:
            name, args = _normalize_tool_call(tool_call)

            logger.debug(
                f"Tool call requested: {name}({json.dumps(dict(args))})",
                layer="ollama", event="tool_call_detected",
                data={"name": name, "args": dict(args)},
            )

            result = await execute_tool(name, dict(args), token, logger)

            logger.debug(
                f"Tool result for {name}: {str(result)[:300]}",
                layer="ollama", event="tool_result",
                data={"name": name, "result_preview": str(result)[:300]},
            )

            full_messages.append({"role": "tool", "content": str(result)})

    logger.error(
        "Reached max tool iterations",
        layer="ollama", event="max_iterations_reached",
        data={"max": MAX_TOOL_ITERATIONS},
    )
    return "I reached the maximum number of steps trying to complete your request. Please try a simpler query."