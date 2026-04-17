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
