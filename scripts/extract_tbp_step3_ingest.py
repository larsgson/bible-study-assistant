#!/usr/bin/env python3
"""
BibleProject Resources - Step 3: ChromaDB Ingestion

This script ingests the chunked BibleProject resources into ChromaDB for semantic search.
It reads the chunks created in Step 2 and adds them to ChromaDB with proper metadata.

Usage:
    python scripts/extract_tbp_step3_ingest.py [--collection-name NAME] [--batch-size SIZE] [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bt_servant_engine.adapters.chroma import (
    get_or_create_chroma_collection,
    list_chroma_collections,
)
from bt_servant_engine.core.logging import get_logger

logger = get_logger(__name__)


class TBPIngester:
    """Ingests BibleProject chunks into ChromaDB."""

    def __init__(
        self,
        chunks_file: Path,
        collection_name: str = "bibleproject",
        batch_size: int = 100,
        dry_run: bool = False,
    ):
        self.chunks_file = chunks_file
        self.collection_name = collection_name
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.stats = {
            "total_chunks": 0,
            "ingested": 0,
            "skipped": 0,
            "errors": 0,
            "by_strategy": {},
        }

    def load_chunks(self) -> list[dict[str, Any]]:
        """Load chunks from the JSON file."""
        logger.info(f"Loading chunks from {self.chunks_file}")
        with open(self.chunks_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # The file is a direct list of chunks
        if isinstance(data, list):
            chunks = data
        else:
            # Handle dict format with "chunks" key if it exists
            chunks = data.get("chunks", [])

        self.stats["total_chunks"] = len(chunks)
        logger.info(f"Loaded {len(chunks)} chunks")
        return chunks

    def prepare_metadata(self, chunk: dict[str, Any]) -> dict[str, Any]:
        """Prepare metadata for ChromaDB ingestion.

        Flattens nested metadata and adds ingestion-specific fields.
        """
        metadata = {}

        # Add top-level fields
        if "strategy" in chunk:
            metadata["strategy"] = chunk["strategy"]
        if "strategy_id" in chunk:
            metadata["strategy_id"] = chunk["strategy_id"]

        # Flatten nested metadata
        if "metadata" in chunk and isinstance(chunk["metadata"], dict):
            nested = chunk["metadata"]

            # Core document fields
            for key in [
                "source",
                "category",
                "title",
                "type",
                "series",
                "filename",
                "folder_path",
            ]:
                if key in nested:
                    metadata[key] = nested[key]

            # Numeric fields
            for key in ["word_count", "page_count", "page_number"]:
                if key in nested:
                    metadata[key] = nested[key]

            # Timestamp fields
            for key in [
                "start_time",
                "end_time",
                "start_seconds",
                "end_seconds",
                "duration_seconds",
                "video_timestamp",
            ]:
                if key in nested:
                    metadata[key] = nested[key]

            # Bible reference fields
            if "has_bible_refs" in nested:
                metadata["has_bible_refs"] = nested["has_bible_refs"]
            if "bible_references" in nested and isinstance(nested["bible_references"], list):
                # Store as JSON string for ChromaDB compatibility
                if nested["bible_references"]:
                    metadata["bible_references"] = json.dumps(nested["bible_references"])
                    metadata["bible_ref_count"] = len(nested["bible_references"])
                else:
                    metadata["bible_ref_count"] = 0

            # URL fields
            if "original_url" in nested:
                metadata["original_url"] = nested["original_url"]

        return metadata

    def ingest_batch(self, collection: Any, batch: list[dict[str, Any]]) -> int:
        """Ingest a batch of chunks into ChromaDB.

        Returns the number of successfully ingested chunks.
        """
        if not batch:
            return 0

        try:
            ids = []
            documents = []
            metadatas = []

            for chunk in batch:
                chunk_id = chunk.get("id")
                text = chunk.get("text", "")

                if not chunk_id or not text:
                    logger.warning(
                        f"Skipping chunk with missing id or text: {chunk.get('id', 'UNKNOWN')}"
                    )
                    self.stats["skipped"] += 1
                    continue

                ids.append(str(chunk_id))
                documents.append(text)
                metadatas.append(self.prepare_metadata(chunk))

            if not ids:
                return 0

            if self.dry_run:
                logger.info(f"[DRY RUN] Would ingest batch of {len(ids)} chunks")
                return len(ids)

            # Upsert the batch
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

            return len(ids)

        except Exception as e:
            logger.error(f"Error ingesting batch: {e}")
            self.stats["errors"] += len(batch)
            return 0

    def ingest_all(self) -> dict[str, Any]:
        """Ingest all chunks into ChromaDB."""
        logger.info("Starting ingestion process")

        # Load chunks
        chunks = self.load_chunks()
        if not chunks:
            logger.warning("No chunks to ingest")
            return self.stats

        # Get or create collection
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create/use collection: {self.collection_name}")
            collection = None
        else:
            logger.info(f"Getting or creating collection: {self.collection_name}")
            collection = get_or_create_chroma_collection(self.collection_name)
            logger.info(f"Collection ready: {self.collection_name}")

        # Process chunks by strategy for better stats
        chunks_by_strategy: dict[str, list[dict[str, Any]]] = {}
        for chunk in chunks:
            strategy = chunk.get("strategy", "unknown")
            if strategy not in chunks_by_strategy:
                chunks_by_strategy[strategy] = []
            chunks_by_strategy[strategy].append(chunk)

        # Ingest in batches
        for strategy, strategy_chunks in chunks_by_strategy.items():
            logger.info(f"Processing {len(strategy_chunks)} chunks for strategy: {strategy}")
            self.stats["by_strategy"][strategy] = 0

            batch = []
            for chunk in strategy_chunks:
                batch.append(chunk)

                if len(batch) >= self.batch_size:
                    count = self.ingest_batch(collection, batch)
                    self.stats["ingested"] += count
                    self.stats["by_strategy"][strategy] += count
                    batch = []

            # Process remaining chunks in the final batch
            if batch:
                count = self.ingest_batch(collection, batch)
                self.stats["ingested"] += count
                self.stats["by_strategy"][strategy] += count

        logger.info("Ingestion complete")
        return self.stats

    def print_stats(self) -> None:
        """Print ingestion statistics."""
        print("\n" + "=" * 70)
        print("BibleProject ChromaDB Ingestion Statistics")
        print("=" * 70)
        print(f"Collection Name: {self.collection_name}")
        print(f"Dry Run: {self.dry_run}")
        print(f"\nTotal Chunks Loaded: {self.stats['total_chunks']}")
        print(f"Successfully Ingested: {self.stats['ingested']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")

        if self.stats["by_strategy"]:
            print(f"\nChunks by Strategy:")
            for strategy, count in sorted(self.stats["by_strategy"].items()):
                print(f"  {strategy}: {count}")

        print("=" * 70 + "\n")


def list_collections_info() -> None:
    """List existing ChromaDB collections."""
    print("\nExisting ChromaDB Collections:")
    print("-" * 50)
    collections = list_chroma_collections()
    if collections:
        for col_name in sorted(collections):
            print(f"  - {col_name}")
    else:
        print("  (none)")
    print("-" * 50 + "\n")


def main() -> None:
    """Main entry point for the ingestion script."""
    parser = argparse.ArgumentParser(
        description="Ingest BibleProject chunks into ChromaDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--chunks-file",
        type=Path,
        default=Path("imports/tbp/chunks/all_chunks_for_embedding.json"),
        help="Path to the chunks JSON file (default: imports/tbp/chunks/all_chunks_for_embedding.json)",
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="bibleproject",
        help="Name of the ChromaDB collection (default: bibleproject)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of chunks to ingest per batch (default: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate ingestion without actually adding to ChromaDB",
    )
    parser.add_argument(
        "--list-collections",
        action="store_true",
        help="List existing ChromaDB collections and exit",
    )

    args = parser.parse_args()

    # Handle list-collections mode
    if args.list_collections:
        list_collections_info()
        return

    # Validate chunks file exists
    chunks_file = args.chunks_file
    if not chunks_file.is_absolute():
        chunks_file = project_root / chunks_file

    if not chunks_file.exists():
        logger.error(f"Chunks file not found: {chunks_file}")
        print(f"\nError: Chunks file not found: {chunks_file}")
        print("\nPlease run Step 2 (chunking) first:")
        print("  python scripts/extract_tbp_step2_chunking.py")
        sys.exit(1)

    # Show existing collections
    list_collections_info()

    # Create ingester and run
    ingester = TBPIngester(
        chunks_file=chunks_file,
        collection_name=args.collection_name,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )

    try:
        ingester.ingest_all()
        ingester.print_stats()

        if args.dry_run:
            print("\nThis was a dry run. No data was actually ingested.")
            print(f"To ingest for real, run without --dry-run flag.\n")
        else:
            print(
                f"\nIngestion complete! Collection '{args.collection_name}' is ready for queries.\n"
            )

    except KeyboardInterrupt:
        print("\n\nIngestion interrupted by user")
        ingester.print_stats()
        sys.exit(1)
    except Exception as e:
        logger.exception("Ingestion failed")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
