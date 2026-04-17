import httpx
from config import ITEMS_BASE_URL, TIMEOUT


async def get_all_items(page: int, size: int, filter_data: dict, token: str, logger) -> dict:
    url = f"{ITEMS_BASE_URL}/all?page={page}&size={size}"
    payload = {"active": True, **filter_data}
    logger.debug(f"POST {url}", layer="http", event="http_request", data={"method": "POST", "url": url, "payload": payload})
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
        body = response.json()
        logger.debug(f"Response {response.status_code}", layer="http", event="http_response", data={"status": response.status_code, "body": body})
        response.raise_for_status()
        return body


async def search_items(search_filter: dict, token: str, logger) -> dict:
    url = f"{ITEMS_BASE_URL}/search"
    logger.debug(f"POST {url}", layer="http", event="http_request", data={"method": "POST", "url": url, "payload": search_filter})
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json=search_filter, headers={"Authorization": f"Bearer {token}"})
        body = response.json()
        logger.debug(f"Response {response.status_code}", layer="http", event="http_response", data={"status": response.status_code, "body": body})
        response.raise_for_status()
        return body


async def create_item(item: dict, token: str, logger) -> dict:
    url = ITEMS_BASE_URL
    logger.debug(f"POST {url}", layer="http", event="http_request", data={"method": "POST", "url": url, "payload": item})
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json=item, headers={"Authorization": f"Bearer {token}"})
        body = response.json()
        logger.debug(f"Response {response.status_code}", layer="http", event="http_response", data={"status": response.status_code, "body": body})
        response.raise_for_status()
        return body


async def update_item(item_id: int, updates: dict, token: str, logger) -> dict:
    url = f"{ITEMS_BASE_URL}/{item_id}/update"
    logger.debug(f"POST {url}", layer="http", event="http_request", data={"method": "POST", "url": url, "payload": updates})
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json=updates, headers={"Authorization": f"Bearer {token}"})
        body = response.json()
        logger.debug(f"Response {response.status_code}", layer="http", event="http_response", data={"status": response.status_code, "body": body})
        response.raise_for_status()
        return body


async def toggle_item_status(item_id: int, is_active: bool, token: str, logger) -> dict:
    active_str = "true" if is_active else "false"
    url = f"{ITEMS_BASE_URL}/{item_id}/status?active={active_str}"
    logger.debug(f"POST {url}", layer="http", event="http_request", data={"method": "POST", "url": url, "payload": {}})
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json={}, headers={"Authorization": f"Bearer {token}"})
        body = response.json()
        logger.debug(f"Response {response.status_code}", layer="http", event="http_response", data={"status": response.status_code, "body": body})
        response.raise_for_status()
        return body


def get_template_url() -> str:
    return f"{ITEMS_BASE_URL}/template"
