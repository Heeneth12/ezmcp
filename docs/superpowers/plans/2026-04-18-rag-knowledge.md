# RAG Knowledge Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a RAG ingestion pipeline that loads markdown docs from `docs/knowledge/` into ChromaDB so the EZ assistant can retrieve relevant context when answering questions.

**Architecture:** Markdown files in `docs/knowledge/business/` and `docs/knowledge/api/` are split by headings into `KnowledgeChunk` objects, embedded via Ollama `nomic-embed-text`, and upserted into a persistent ChromaDB collection. Retrieval uses the existing `search_documentation` tool and `query_docs()` method. Ingestion is triggered via CLI (`python ingest_cli.py`) or `POST /v1/admin/ingest`.

**Tech Stack:** Python, ChromaDB, Ollama (`nomic-embed-text`), FastAPI, pytest, unittest.mock

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `requirements.txt` | Modify | Add `chromadb` |
| `modules/knowledge/knowledge_types.py` | Modify | `KnowledgeChunk` dataclass |
| `modules/knowledge/ingest.py` | Create | `KnowledgeIngester`: parse headings, embed, upsert |
| `ingest_cli.py` | Create | CLI entrypoint with `--clear` flag |
| `docs/knowledge/business/items.md` | Create | Sample business knowledge doc |
| `docs/knowledge/api/items-api.md` | Create | Sample API knowledge doc |
| `main.py` | Modify | Add `POST /v1/admin/ingest` endpoint |
| `tests/test_ingest.py` | Create | Unit tests for `parse_markdown_text`, `ingest_all` |

---

### Task 1: Add chromadb dependency and KnowledgeChunk type

**Files:**
- Modify: `requirements.txt`
- Modify: `modules/knowledge/knowledge_types.py`

- [ ] **Step 1: Add chromadb to requirements.txt**

Open `requirements.txt` and add `chromadb` on a new line at the end:
```
fastapi==0.115.0
uvicorn==0.30.6
httpx==0.27.2
ollama==0.3.3
pydantic==2.9.2
python-dotenv==1.0.1
pytest==8.3.3
pytest-asyncio==0.24.0
chromadb
```

- [ ] **Step 2: Define KnowledgeChunk in knowledge_types.py**

Replace the full content of `modules/knowledge/knowledge_types.py`:
```python
from dataclasses import dataclass


@dataclass
class KnowledgeChunk:
    id: str
    heading: str
    content: str
    source: str
    category: str
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt modules/knowledge/knowledge_types.py
git commit -m "feat: add KnowledgeChunk type and chromadb dependency"
```

---

### Task 2: TDD — parse_markdown_text()

**Files:**
- Create: `tests/test_ingest.py`
- Create: `modules/knowledge/ingest.py`

- [ ] **Step 1: Write failing tests for parse_markdown_text**

Create `tests/test_ingest.py`:
```python
import logging
import pytest
from unittest.mock import MagicMock, patch

from modules.knowledge.ingest import KnowledgeIngester

SAMPLE_MD = """\
## What is an Item?
An item represents a product or service tracked in EZ Inventory.

## Item Types
Items can be PRODUCT or SERVICE. Products are physical goods.
"""


def test_parse_markdown_returns_two_chunks():
    ingester = KnowledgeIngester.__new__(KnowledgeIngester)
    chunks = ingester.parse_markdown_text(SAMPLE_MD, source="items.md", category="business")
    assert len(chunks) == 2


def test_parse_markdown_chunk_fields():
    ingester = KnowledgeIngester.__new__(KnowledgeIngester)
    chunks = ingester.parse_markdown_text(SAMPLE_MD, source="items.md", category="business")
    assert chunks[0].heading == "What is an Item?"
    assert "product or service" in chunks[0].content
    assert chunks[0].source == "items.md"
    assert chunks[0].category == "business"
    assert chunks[1].heading == "Item Types"


def test_parse_markdown_ids_are_deterministic():
    ingester = KnowledgeIngester.__new__(KnowledgeIngester)
    chunks_a = ingester.parse_markdown_text(SAMPLE_MD, source="items.md", category="business")
    chunks_b = ingester.parse_markdown_text(SAMPLE_MD, source="items.md", category="business")
    assert chunks_a[0].id == chunks_b[0].id


def test_parse_markdown_no_headings_returns_single_chunk(caplog):
    ingester = KnowledgeIngester.__new__(KnowledgeIngester)
    with caplog.at_level(logging.WARNING, logger="modules.knowledge.ingest"):
        chunks = ingester.parse_markdown_text(
            "This is plain text with no headings.", source="plain.md", category="business"
        )
    assert len(chunks) == 1
    assert chunks[0].heading == "plain.md"
    assert len(caplog.records) == 1
    assert "No headings" in caplog.records[0].message
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_ingest.py -v
```
Expected: `ERROR` — `ModuleNotFoundError: No module named 'modules.knowledge.ingest'`

- [ ] **Step 3: Create ingest.py with parse_markdown_text()**

Create `modules/knowledge/ingest.py`:
```python
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
        pattern = re.compile(r'^#{1,3}\s+(.+)$', re.MULTILINE)
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
            chunk_id = hashlib.md5(f"{source}::{heading}".encode()).hexdigest()
            chunks.append(KnowledgeChunk(
                id=chunk_id,
                heading=heading,
                content=content,
                source=source,
                category=category,
            ))
        return chunks
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ingest.py::test_parse_markdown_returns_two_chunks tests/test_ingest.py::test_parse_markdown_chunk_fields tests/test_ingest.py::test_parse_markdown_ids_are_deterministic tests/test_ingest.py::test_parse_markdown_no_headings_returns_single_chunk -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add modules/knowledge/ingest.py tests/test_ingest.py
git commit -m "feat: add KnowledgeIngester.parse_markdown_text with TDD"
```

---

### Task 3: TDD — ingest_file() and ingest_all()

**Files:**
- Modify: `tests/test_ingest.py`
- Modify: `modules/knowledge/ingest.py`

- [ ] **Step 1: Write failing tests for ingest_all**

Append to `tests/test_ingest.py`:
```python
def _make_ingester_with_mocks(mock_client, mock_collection):
    with patch("modules.knowledge.ingest.Client", return_value=mock_client), \
         patch("modules.knowledge.ingest.chromadb") as mock_chroma:
        mock_chroma.PersistentClient.return_value.get_or_create_collection.return_value = mock_collection
        return KnowledgeIngester()


def test_ingest_all_upserts_correct_chunk_count(tmp_path):
    (tmp_path / "business").mkdir()
    (tmp_path / "api").mkdir()
    (tmp_path / "business" / "items.md").write_text(
        "## What is an Item?\nAn item is a product.\n\n## Item Types\nPRODUCT or SERVICE.\n"
    )
    (tmp_path / "api" / "items-api.md").write_text(
        "## Get All Items\nPOST /v1/items/all returns paginated items.\n"
    )

    mock_client = MagicMock()
    mock_client.embeddings.return_value = MagicMock(embedding=[0.1] * 768)
    mock_collection = MagicMock()
    mock_collection.get.return_value = {"ids": []}

    ingester = _make_ingester_with_mocks(mock_client, mock_collection)
    files, chunks = ingester.ingest_all(tmp_path)

    assert files == 2
    assert chunks == 3
    assert mock_collection.upsert.call_count == 3


def test_ingest_all_clear_deletes_existing(tmp_path):
    (tmp_path / "business").mkdir()
    (tmp_path / "api").mkdir()

    mock_client = MagicMock()
    mock_client.embeddings.return_value = MagicMock(embedding=[0.1] * 768)
    mock_collection = MagicMock()
    mock_collection.get.return_value = {"ids": ["abc", "def"]}

    ingester = _make_ingester_with_mocks(mock_client, mock_collection)
    ingester.ingest_all(tmp_path, clear=True)

    mock_collection.delete.assert_called_once_with(ids=["abc", "def"])


def test_ingest_all_missing_docs_dir_raises(tmp_path):
    mock_client = MagicMock()
    mock_collection = MagicMock()

    ingester = _make_ingester_with_mocks(mock_client, mock_collection)
    with pytest.raises(FileNotFoundError, match="Knowledge directory not found"):
        ingester.ingest_all(tmp_path / "nonexistent")


def test_ingest_file_raises_on_ollama_unavailable(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("## Heading\nSome content.")

    mock_client = MagicMock()
    mock_client.embeddings.side_effect = Exception("connection refused")
    mock_collection = MagicMock()

    ingester = _make_ingester_with_mocks(mock_client, mock_collection)
    with pytest.raises(RuntimeError, match="Ollama not running"):
        ingester.ingest_file(md_file, "business")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_ingest.py::test_ingest_all_upserts_correct_chunk_count tests/test_ingest.py::test_ingest_all_clear_deletes_existing tests/test_ingest.py::test_ingest_all_missing_docs_dir_raises tests/test_ingest.py::test_ingest_file_raises_on_ollama_unavailable -v
```
Expected: 4 FAILED — `ingest_all` and `ingest_file` methods don't exist yet

- [ ] **Step 3: Add ingest_file and ingest_all to KnowledgeIngester**

Append these two methods inside the `KnowledgeIngester` class in `modules/knowledge/ingest.py`:
```python
    def ingest_file(self, filepath: Path, category: str) -> int:
        text = filepath.read_text(encoding="utf-8")
        chunks = self.parse_markdown_text(text, source=filepath.name, category=category)
        for chunk in chunks:
            try:
                response = self.client.embeddings(model="nomic-embed-text", prompt=chunk.content)
                vector = response.embedding
            except Exception as e:
                raise RuntimeError("Ollama not running — start it before ingesting") from e
            self.collection.upsert(
                ids=[chunk.id],
                embeddings=[vector],
                documents=[chunk.content],
                metadatas=[{"source": chunk.source, "category": chunk.category, "heading": chunk.heading}],
            )
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
```

- [ ] **Step 4: Run all ingest tests to verify they pass**

```bash
pytest tests/test_ingest.py -v
```
Expected: 8 PASSED

- [ ] **Step 5: Commit**

```bash
git add modules/knowledge/ingest.py tests/test_ingest.py
git commit -m "feat: add ingest_file and ingest_all with TDD"
```

---

### Task 4: Create ingest_cli.py

**Files:**
- Create: `ingest_cli.py`

- [ ] **Step 1: Create ingest_cli.py**

Create `ingest_cli.py` in the project root:
```python
import argparse
import sys
from pathlib import Path
from modules.knowledge.ingest import KnowledgeIngester


def main():
    parser = argparse.ArgumentParser(description="Ingest knowledge docs into ChromaDB")
    parser.add_argument("--clear", action="store_true", help="Wipe collection before ingesting")
    args = parser.parse_args()

    docs_dir = Path(__file__).parent / "docs" / "knowledge"
    if not docs_dir.exists():
        print(f"ERROR: Knowledge directory not found: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    mode = " [CLEAR MODE]" if args.clear else ""
    print(f"Starting ingestion from {docs_dir}{mode}")

    try:
        ingester = KnowledgeIngester()
        files, chunks = ingester.ingest_all(docs_dir, clear=args.clear)
        print(f"Done. Files: {files}, Chunks: {chunks}")
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify import works**

```bash
python -c "import ingest_cli; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add ingest_cli.py
git commit -m "feat: add ingest_cli.py entrypoint"
```

---

### Task 5: Create sample knowledge docs

**Files:**
- Create: `docs/knowledge/business/items.md`
- Create: `docs/knowledge/api/items-api.md`

- [ ] **Step 1: Create the folder structure**

```bash
mkdir -p docs/knowledge/business docs/knowledge/api
```

- [ ] **Step 2: Create docs/knowledge/business/items.md**

Create `docs/knowledge/business/items.md` with this content:
```markdown
## What is an Item?
An item represents a product or service tracked in EZ Inventory. Every item has a unique code, a category, a unit of measure, and both a purchase price and a selling price.

## Item Types
Items can be one of two types:
- **PRODUCT** — A physical good that is bought and sold (e.g., Electronics, Raw Materials).
- **SERVICE** — An intangible offering billed to customers (e.g., Installation, Consultation).

## Item Status
Items have an Active or Inactive status. Inactive items are soft-deleted — they are hidden from catalog views but their data is retained. Use the toggle feature to enable or disable an item.

## Required Fields When Adding an Item
- **Name** — Human-readable item name.
- **Item Code** — Unique identifier. Auto-generated as ITM-XXXX if not provided.
- **Category** — Grouping such as Electronics, Furniture, Raw Material.
- **Unit of Measure** — PCS, KG, BOX, LITRE, etc.
- **Purchase Price** — Cost price used for procurement.
- **Selling Price** — The price charged to customers.

## Optional Fields
Brand, Manufacturer, SKU, Barcode, HSN/SAC Code, Tax Percentage, Discount Percentage, Description.

## Adding a New Item
To add an item, provide Name, Category, Unit, Purchase Price, and Selling Price at minimum. An Item Code will be auto-generated if omitted. The item defaults to Active status on creation.

## Bulk Import
Use the bulk import template to add multiple items at once. Download the Excel template, fill in item data, and upload via the Bulk Import feature. The template endpoint is GET /v1/items/template.
```

- [ ] **Step 3: Create docs/knowledge/api/items-api.md**

Create `docs/knowledge/api/items-api.md` with this content:
```markdown
## Get All Items
Endpoint: POST /v1/items/all?page=0&size=10
Returns a paginated list of inventory items with optional filters.
Request body fields (all optional): active (boolean, default true), itemType (PRODUCT or SERVICE), brand (string), category (string).
Default values: page=0, size=10, active=true.

## Search Items
Endpoint: POST /v1/items/search
Keyword search across item Name and Description fields.
Request body: searchQuery (string, required).
Returns matching items regardless of active status.

## Create Item
Endpoint: POST /v1/items
Creates a new inventory item.
Required fields: name, category, unitOfMeasure, purchasePrice, sellingPrice.
Optional fields: itemType (default PRODUCT), brand, manufacturer, itemCode, sku, barcode, hsnSacCode, taxPercentage, discountPercentage, description.
If itemCode is omitted, one is auto-generated as ITM-XXXX.

## Update Item
Endpoint: POST /v1/items/{id}/update
Updates an existing item by numeric ID. Only provide the fields you want to change.

## Toggle Item Status
Endpoint: POST /v1/items/{id}/status?active=true
Enables (active=true) or disables (active=false) an item by numeric ID. This is a soft delete — data is retained.

## Get Bulk Import Template
Endpoint: GET /v1/items/template
Returns the download URL for the Excel bulk import template.
```

- [ ] **Step 4: Commit**

```bash
git add docs/knowledge/
git commit -m "docs: add sample business and API knowledge docs"
```

---

### Task 6: Add POST /v1/admin/ingest to main.py

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Add import at top of main.py**

In `main.py`, add this import alongside the existing imports at the top of the file:
```python
from modules.knowledge.ingest import KnowledgeIngester
```

- [ ] **Step 2: Add IngestRequest model**

In `main.py`, add this class directly after the `GenerateRequest` class (around line 32):
```python
class IngestRequest(BaseModel):
    clear: bool = False
```

- [ ] **Step 3: Add the /v1/admin/ingest endpoint**

In `main.py`, add this endpoint directly after the `/health` endpoint (around line 72):
```python
@app.post("/v1/admin/ingest")
async def admin_ingest(body: IngestRequest):
    import asyncio
    from pathlib import Path
    docs_dir = Path(__file__).parent / "docs" / "knowledge"
    ingester = KnowledgeIngester()
    try:
        files, chunks = await asyncio.to_thread(ingester.ingest_all, docs_dir, body.clear)
        return {"files": files, "chunks": chunks}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
```

- [ ] **Step 4: Verify server imports without error**

```bash
python -c "from main import app; print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
pytest tests/ -v
```
Expected: All previously passing tests still pass. New ingest tests pass.

- [ ] **Step 6: Commit**

```bash
git add main.py
git commit -m "feat: add POST /v1/admin/ingest endpoint"
```

---

## How to Use After Implementation

**Step 1 — Write your knowledge files:**
```
docs/knowledge/business/items.md      ← item rules, workflows
docs/knowledge/business/suppliers.md  ← supplier policies
docs/knowledge/api/items-api.md       ← API endpoint docs
```

**Step 2 — Ingest (first time or after changes):**
```bash
# Add new/changed docs to ChromaDB
python ingest_cli.py

# Full re-ingest (wipes stale data first)
python ingest_cli.py --clear
```

**Or via API:**
```bash
curl -X POST http://localhost:8080/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"clear": false}'
```

**Step 3 — The assistant now uses your docs automatically.** When a user asks "how do I add an item?", the `search_documentation` tool retrieves the relevant chunk from ChromaDB and injects it as context before Ollama answers.
