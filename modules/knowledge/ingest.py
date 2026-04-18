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
        heading_count: dict = {}
        for i, match in enumerate(matches):
            heading = match.group(1).strip()
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            heading_count[heading] = heading_count.get(heading, 0) + 1
            suffix = f"::{heading_count[heading] - 1}" if heading_count[heading] > 1 else ""
            if suffix:
                logger.warning(f"Duplicate heading '{heading}' in '{source}' — disambiguating with suffix {suffix}")
            chunk_id = hashlib.md5(f"{source}::{heading}{suffix}".encode()).hexdigest()
            chunks.append(KnowledgeChunk(
                id=chunk_id,
                heading=heading,
                content=content,
                source=source,
                category=category,
            ))
        return chunks

    def ingest_file(self, filepath: Path, category: str) -> int:
        text = filepath.read_text(encoding="utf-8")
        chunks = self.parse_markdown_text(text, source=filepath.name, category=category)
        for chunk in chunks:
            try:
                response = self.client.embeddings(model="nomic-embed-text", prompt=chunk.content)
                vector = response.embedding
            except Exception as e:
                raise RuntimeError("Ollama not running — start it before ingesting") from e
            try:
                self.collection.upsert(
                    ids=[chunk.id],
                    embeddings=[vector],
                    documents=[chunk.content],
                    metadatas=[{"source": chunk.source, "category": chunk.category, "heading": chunk.heading}],
                )
            except Exception as e:
                raise RuntimeError(f"ChromaDB write failed for chunk '{chunk.heading}' in '{chunk.source}'") from e
        return len(chunks)

    def ingest_all(self, docs_dir: Path, clear: bool = False) -> tuple[int, int]:
        if not docs_dir.exists():
            raise FileNotFoundError(f"Knowledge directory not found: {docs_dir}")
        if clear:
            existing_ids = self.collection.get()["ids"]
            if existing_ids:
                self.collection.delete(ids=existing_ids)
        total_files = 0
        total_chunks = 0
        for category, directory in [("business", docs_dir / "business"), ("api", docs_dir / "api")]:
            if not directory.exists():
                continue
            for md_file in sorted(directory.glob("*.md")):
                logger.info(f"Ingesting {md_file.name} ({category})")
                total_chunks += self.ingest_file(md_file, category)
                total_files += 1
        return total_files, total_chunks
