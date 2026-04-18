import chromadb
import hashlib
import logging
import re
from pathlib import Path
from ollama import Client
from modules.knowledge.knowledge_types import KnowledgeChunk

logger = logging.getLogger(__name__)


class KnowledgeIngester:
    def __init__(self):
        self.client = Client()
        self.db = chromadb.PersistentClient(path="./vector_db")
        self.collection = self.db.get_or_create_collection("ez_docs")

    def parse_markdown_text(self, text: str, source: str, category: str) -> list[KnowledgeChunk]:
        pattern = re.compile(r'^#{2,3}\s+(.+)$', re.MULTILINE)
        matches = list(pattern.finditer(text))

        if not matches:
            logger.warning(f"No headings found in '{source}' — treating as single chunk")
            chunk_id = hashlib.md5(f"{source}::".encode()).hexdigest()
            return [KnowledgeChunk(
                id=chunk_id,
                heading=source,
                content=text.strip(),
                source=source,
                category=category,
            )]

        chunks = []
        for i, match in enumerate(matches):
            heading = match.group(1).strip()
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            chunk_id = hashlib.md5(f"{source}::{start}".encode()).hexdigest()
            chunks.append(KnowledgeChunk(
                id=chunk_id,
                heading=heading,
                content=content,
                source=source,
                category=category,
            ))
        return chunks
