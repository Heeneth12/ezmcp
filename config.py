import os
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8080")
PORT = int(os.getenv("PORT", 8085))
TIMEOUT = 5.0

ITEMS_BASE_URL = f"{SERVER_URL}/v1/items"
CHAT_BASE_URL = f"{SERVER_URL}/v1/mcp/chat"
