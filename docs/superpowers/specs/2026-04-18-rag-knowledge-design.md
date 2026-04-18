# RAG Knowledge Base — Design Spec

**Date:** 2026-04-18  
**Project:** EZ Inventory MCP Server  
**Status:** Approved

---

## Goal

Enable the EZ AI assistant to answer questions about business rules, workflows, and API behaviour by retrieving relevant context from a structured knowledge base before generating a response (Retrieval-Augmented Generation).

---

## Document Structure

Knowledge files live in two category folders:

```
docs/knowledge/
  business/       ← business rules, item types, workflows, policies
  api/            ← API endpoint descriptions, params, response shapes
```

Each file is a standard Markdown file. Every heading (`##`, `###`) marks the start of one retrievable chunk. Authors write docs normally — the ingester handles splitting automatically.

**Example (`docs/knowledge/business/items.md`):**
```md
## What is an Item?
An item represents a product or service tracked in EZ Inventory...

## Item Types
Items can be PRODUCT or SERVICE. Products are physical goods...
```

---

## Components

### 1. `modules/knowledge/knowledge_types.py`
Defines `KnowledgeChunk` dataclass:
- `id` — deterministic hash of `source + heading`
- `heading` — the markdown heading text
- `content` — full text of the chunk (heading + body)
- `source` — filename (e.g., `items.md`)
- `category` — `business` or `api`

### 2. `modules/knowledge/ingest.py` — `KnowledgeIngester`
Core ingestion class with three methods:
- `parse_markdown(filepath, category)` → `list[KnowledgeChunk]`  
  Splits file on headings. If no headings found, treats whole file as one chunk (warns).
- `ingest_file(filepath, category)` → embeds each chunk via Ollama `nomic-embed-text`, upserts into ChromaDB with metadata.
- `ingest_all(docs_dir, clear=False)` → walks `docs/knowledge/business/` and `docs/knowledge/api/` recursively, calls `ingest_file` for each `.md`. If `clear=True`, wipes collection first.

### 3. `ingest_cli.py` — CLI entrypoint
```
python ingest_cli.py           # upsert mode
python ingest_cli.py --clear   # wipe + full re-ingest
```
Prints per-file progress and final summary (files processed, chunks ingested).

### 4. `main.py` update — Admin endpoint
```
POST /v1/admin/ingest
Body: { "clear": false }
```
Calls `KnowledgeIngester.ingest_all()`. Returns `{ "files": N, "chunks": N }`. No auth guard for now (internal use only).

### 5. `modules/knowledge/knowledge_service.py` — query side (minor update)
`query_docs(user_query)` already exists. No structural change needed — it embeds the query and returns top-3 matching chunks from ChromaDB. Metadata is stored but not filtered at query time (all categories searched together).

### 6. `requirements.txt` update
Add `chromadb` (currently missing from requirements despite being used).

---

## Data Flow

```
Author writes .md → docs/knowledge/business/ or api/
        ↓
python ingest_cli.py  OR  POST /v1/admin/ingest
        ↓
KnowledgeIngester.ingest_all()
  for each .md file:
    parse_markdown() → chunks (split by headings)
    for each chunk:
      Ollama nomic-embed-text → float[] vector
      ChromaDB upsert(id, vector, document, metadata)
        ↓
ChromaDB collection "ez_docs" (persisted at ./vector_db)
        ↑
User message → Ollama decides → calls search_documentation tool
  → knowledge_service.query_docs(query)
  → embed query → ChromaDB similarity search → top 3 chunks
  → chunks injected as context into agent loop
  → Ollama generates answer using retrieved context
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| `docs/knowledge/` dir missing | Raise `FileNotFoundError` with clear message |
| `.md` file has no headings | Treat whole file as one chunk, log warning |
| Ollama unavailable during ingest | Raise with message: "Ollama not running — start it before ingesting" |
| ChromaDB write error | Propagate exception with filename context |
| Query with empty knowledge base | Returns "No specific documentation found" (existing behaviour) |

---

## Testing

| Test | Type | What it verifies |
|---|---|---|
| `test_parse_markdown` | Unit | Given sample `.md`, correct chunks + headings extracted |
| `test_ingest_all_calls_upsert` | Unit | Mock Ollama + ChromaDB, assert upsert called N times |
| `test_no_headings_fallback` | Unit | File with no headings → single chunk, warning logged |
| `test_query_docs_returns_chunks` | Integration | Ingest small real `.md`, query it, assert relevant chunk returned |

---

## Out of Scope

- Authentication on `/v1/admin/ingest` (internal tool)
- PDF or DOCX ingestion
- Re-ingestion on file-change detection (manual trigger only)
- Per-category filtering at query time
