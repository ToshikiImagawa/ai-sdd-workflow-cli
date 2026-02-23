"""Index command implementation."""

from pathlib import Path

from sdd_cli.cache import get_cache_dir
from sdd_cli.config import resolve_config
from sdd_cli.indexer.db import IndexDB
from sdd_cli.indexer.parser import DocumentParser
from sdd_cli.indexer.scanner import DocumentScanner


def build_index(root: Path, quiet: bool = False) -> None:
    """Build document index.

    Args:
        root: Project root directory
        quiet: Suppress output messages

    Raises:
        Exception: If indexing fails
    """
    config = resolve_config(root)
    sdd_root = root / config["root"]

    if not sdd_root.exists():
        raise ValueError(f"SDD root directory not found: {sdd_root}")

    # Initialize scanner
    scanner = DocumentScanner(sdd_root, directories=config["directories"])

    # Get all documents
    documents = scanner.scan_all()

    if not quiet:
        print(f"Found {len(documents)} documents to index...")

    # Initialize database using XDG cache directory
    cache_dir = get_cache_dir(root)
    db_path = cache_dir / "index.db"

    with IndexDB(db_path) as db:
        # Clear the existing index
        db.clear()

        # Index each document
        indexed_count = 0
        for doc_info in documents:
            try:
                # Parse document
                parsed_data = DocumentParser.parse(
                    doc_info["full_path"],
                    directory=doc_info["directory"],
                    rel_path=doc_info["file_path"],
                )

                # Index document
                db.index_document(doc_info, parsed_data)

                indexed_count += 1

                if not quiet and indexed_count % 10 == 0:
                    print(f"  Indexed {indexed_count}/{len(documents)} documents...")

            except Exception as e:
                if not quiet:
                    print(f"  Warning: Failed to index {doc_info['file_path']}: {e}")

        if not quiet:
            print(f"Indexed {indexed_count}/{len(documents)} documents")

    if not quiet:
        print(f"✓ Index built successfully at {db_path}")

    # Save metadata
    import datetime
    import json

    metadata = {
        "indexed_at": datetime.datetime.now().isoformat(),
        "document_count": indexed_count,
        "root": str(root),
    }

    metadata_path = cache_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
