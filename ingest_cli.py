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
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
