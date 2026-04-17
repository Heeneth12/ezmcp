import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import httpx

from config import CHAT_BASE_URL, TIMEOUT
from ai.tool_registry import run_agent_loop
from logger import RequestLogger

app = FastAPI(title="EZ MCP AI Worker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ez-inventory.onrender.com",
        "http://localhost:4200",
        "http://localhost:8080",
        "http://localhost:8085",
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class GenerateRequest(BaseModel):
    message: str
    conversationId: Optional[int] = None


async def get_chat_history(conversation_id: Optional[int], token: str, logger: RequestLogger) -> list:
    if not conversation_id:
        logger.debug("No conversationId — skipping history fetch", layer="main", event="history_skip")
        return []
    try:
        logger.debug(f"Fetching chat history for conversation {conversation_id}", layer="main", event="history_fetch_start")
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                f"{CHAT_BASE_URL}/{conversation_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
            )
            messages = response.json().get("data", [])
            logger.debug(
                f"Chat history loaded — {len(messages)} messages",
                layer="main", event="history_fetch_done",
                data={"count": len(messages)},
            )
            return [
                {"role": "user" if msg["sender"] == "user" else "assistant", "content": msg["content"]}
                for msg in messages
            ]
    except Exception as e:
        logger.error(
            f"Failed to fetch history: {e}\n{traceback.format_exc()}",
            layer="main", event="history_fetch_error",
            data={"error": str(e)},
        )
        return []


@app.get("/health")
async def health():
    return {
        "status": "UP",
        "service": "mcp-ai-worker-python",
        "model": "phi4-mini",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/v1/ai/generate")
async def generate(request: Request, body: GenerateRequest):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = auth_header.split(" ")[1] if " " in auth_header else auth_header
    logger = RequestLogger(body.conversationId, body.message)

    try:
        history = await get_chat_history(body.conversationId, token, logger)
        messages = [*history, {"role": "user", "content": body.message}]
        logger.debug(
            "Starting agent loop",
            layer="main", event="agent_loop_start",
            data={"total_messages": len(messages)},
        )
        reply = await run_agent_loop(messages, token, logger)
        logger.info(
            f"Reply sent: {reply[:100]}",
            layer="main", event="reply_sent",
            data={"reply_preview": reply[:100]},
        )
        logger.close()
        return {"reply": reply}
    except Exception as e:
        logger.error(
            f"Unhandled error: {e}\n{traceback.format_exc()}",
            layer="main", event="unhandled_error",
            data={"error": str(e), "traceback": traceback.format_exc()},
        )
        logger.close(error=True)
        return {"reply": "I encountered an error with the local model service."}


if __name__ == "__main__":
    import uvicorn
    from config import PORT
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
