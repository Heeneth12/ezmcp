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
