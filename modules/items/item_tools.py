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
