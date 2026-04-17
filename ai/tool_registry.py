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
    try:
        result = await tool["execute"](args, token, logger)
    except Exception as e:
        logger.error(f"Tool '{name}' raised an exception: {e}", layer="tool", event="tool_execute_error", data={"name": name, "error": str(e)})
        return f"Tool '{name}' encountered an error: {str(e)}"
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
