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
    assert chunks_a[0].id != chunks_a[1].id


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


def test_parse_markdown_ignores_h1_headings():
    ingester = KnowledgeIngester.__new__(KnowledgeIngester)
    md = "# Doc Title\n\n## Section\ncontent\n"
    chunks = ingester.parse_markdown_text(md, source="doc.md", category="business")
    assert len(chunks) == 1
    assert chunks[0].heading == "Section"


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
    (tmp_path / "business" / "items.md").write_text(
        "## Item Types\nPRODUCT or SERVICE.\n"
    )

    mock_client = MagicMock()
    mock_client.embeddings.return_value = MagicMock(embedding=[0.1] * 768)
    mock_collection = MagicMock()
    mock_collection.get.return_value = {"ids": ["abc", "def"]}

    ingester = _make_ingester_with_mocks(mock_client, mock_collection)
    files, chunks = ingester.ingest_all(tmp_path, clear=True)

    mock_collection.delete.assert_called_once_with(ids=["abc", "def"])
    assert files == 1
    assert chunks == 1
    assert mock_collection.upsert.call_count == 1


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
