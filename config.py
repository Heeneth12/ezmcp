import os
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8085")
PORT = int(os.getenv("PORT", 8080))
TIMEOUT = 5.0

ITEMS_BASE_URL = f"http://localhost:8085/v1/items"
CHAT_BASE_URL = f"http://localhost:8085/v1/mcp/chat"
