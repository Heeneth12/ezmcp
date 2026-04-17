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
