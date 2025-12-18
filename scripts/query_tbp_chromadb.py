#!/usr/bin/env python3
"""
BibleProject Resources - Query and Test ChromaDB

This script queries the BibleProject ChromaDB collection to test retrieval quality
and explore the ingested content.

Usage:
    python scripts/query_tbp_chromadb.py [--collection NAME] [--query "search text"] [--n-results N]
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
    get_chroma_collection,
    list_chroma_collections,
)
from bt_servant_engine.core.logging import get_logger

logger = get_logger(__name__)


class TBPQuerier:
    """Query and explore BibleProject ChromaDB collection."""

    def __init__(self, collection_name: str = "bibleproject"):
        self.collection_name = collection_name
        self.collection = None

    def connect(self) -> bool:
        """Connect to the ChromaDB collection."""
        logger.info(f"Connecting to collection: {self.collection_name}")
        self.collection = get_chroma_collection(self.collection_name)

        if self.collection is None:
            logger.error(f"Collection '{self.collection_name}' not found")
            return False

        logger.info(f"Connected to collection: {self.collection_name}")
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        if not self.collection:
            return {}

        count = self.collection.count()

        # Sample a few documents to get metadata keys
        sample = self.collection.get(limit=100)

        strategies = set()
        categories = set()
        types = set()

        if sample and sample.get("metadatas"):
            for metadata in sample["metadatas"]:
                if isinstance(metadata, dict):
                    if "strategy" in metadata:
                        strategies.add(metadata["strategy"])
                    if "category" in metadata:
                        categories.add(metadata["category"])
                    if "type" in metadata:
                        types.add(metadata["type"])

        return {
            "total_documents": count,
            "strategies": sorted(list(strategies)),
            "categories": sorted(list(categories)),
            "types": sorted(list(types)),
        }

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query the collection with semantic search."""
        if not self.collection:
            logger.error("Not connected to collection")
            return {}

        logger.info(f"Querying: '{query_text}' (n_results={n_results})")

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
            )
            return results
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {}

    def query_by_strategy(
        self,
        query_text: str,
        strategy: str,
        n_results: int = 5,
    ) -> dict[str, Any]:
        """Query with a specific chunking strategy filter."""
        where = {"strategy": strategy}
        return self.query(query_text, n_results, where)

    def query_by_category(
        self,
        query_text: str,
        category: str,
        n_results: int = 5,
    ) -> dict[str, Any]:
        """Query with a specific category filter."""
        where = {"category": category}
        return self.query(query_text, n_results, where)

    def get_document_by_id(self, doc_id: str) -> dict[str, Any]:
        """Retrieve a specific document by ID."""
        if not self.collection:
            logger.error("Not connected to collection")
            return {}

        try:
            results = self.collection.get(ids=[doc_id])
            return results
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return {}

    def browse_sample(self, limit: int = 10, strategy: str | None = None) -> dict[str, Any]:
        """Browse a sample of documents from the collection."""
        if not self.collection:
            logger.error("Not connected to collection")
            return {}

        try:
            if strategy:
                results = self.collection.get(
                    limit=limit,
                    where={"strategy": strategy},
                )
            else:
                results = self.collection.get(limit=limit)
            return results
        except Exception as e:
            logger.error(f"Failed to browse sample: {e}")
            return {}


def print_stats(stats: dict[str, Any]) -> None:
    """Print collection statistics."""
    print("\n" + "=" * 70)
    print("BibleProject ChromaDB Collection Statistics")
    print("=" * 70)
    print(f"Total Documents: {stats.get('total_documents', 0)}")

    strategies = stats.get("strategies", [])
    if strategies:
        print(f"\nChunking Strategies ({len(strategies)}):")
        for strategy in strategies:
            print(f"  - {strategy}")

    categories = stats.get("categories", [])
    if categories:
        print(f"\nCategories ({len(categories)}):")
        for category in categories:
            print(f"  - {category}")

    types = stats.get("types", [])
    if types:
        print(f"\nDocument Types ({len(types)}):")
        for doc_type in types:
            print(f"  - {doc_type}")

    print("=" * 70 + "\n")


def print_query_results(results: dict[str, Any], query_text: str) -> None:
    """Print query results in a readable format."""
    print("\n" + "=" * 70)
    print(f"Query Results: '{query_text}'")
    print("=" * 70)

    if not results or not results.get("ids"):
        print("No results found.")
        print("=" * 70 + "\n")
        return

    ids = results["ids"][0] if results.get("ids") else []
    documents = results["documents"][0] if results.get("documents") else []
    metadatas = results["metadatas"][0] if results.get("metadatas") else []
    distances = results["distances"][0] if results.get("distances") else []

    for i, doc_id in enumerate(ids):
        print(f"\nResult #{i + 1}")
        print("-" * 70)
        print(f"ID: {doc_id}")

        if i < len(distances):
            print(f"Distance: {distances[i]:.4f}")

        if i < len(metadatas):
            metadata = metadatas[i]
            if isinstance(metadata, dict):
                print(f"Strategy: {metadata.get('strategy', 'N/A')}")
                print(f"Category: {metadata.get('category', 'N/A')}")
                print(f"Title: {metadata.get('title', 'N/A')}")
                print(f"Type: {metadata.get('type', 'N/A')}")

                if metadata.get("start_time"):
                    print(f"Timestamp: {metadata.get('start_time')} - {metadata.get('end_time')}")

                if metadata.get("bible_ref_count", 0) > 0:
                    print(f"Bible References: {metadata.get('bible_ref_count')}")

        if i < len(documents):
            doc_text = documents[i]
            preview_len = 300
            if len(doc_text) > preview_len:
                print(f"\nText Preview:\n{doc_text[:preview_len]}...")
            else:
                print(f"\nText:\n{doc_text}")

    print("\n" + "=" * 70 + "\n")


def print_browse_results(results: dict[str, Any], limit: int) -> None:
    """Print browse results."""
    print("\n" + "=" * 70)
    print(f"Browse Sample (limit={limit})")
    print("=" * 70)

    if not results or not results.get("ids"):
        print("No documents found.")
        print("=" * 70 + "\n")
        return

    ids = results.get("ids", [])
    metadatas = results.get("metadatas", [])

    print(f"\nFound {len(ids)} documents:\n")

    for i, doc_id in enumerate(ids):
        metadata = metadatas[i] if i < len(metadatas) else {}
        if isinstance(metadata, dict):
            title = metadata.get("title", "N/A")
            strategy = metadata.get("strategy", "N/A")
            category = metadata.get("category", "N/A")
            print(f"  {i + 1}. {doc_id} - {title} [{strategy}] ({category})")
        else:
            print(f"  {i + 1}. {doc_id}")

    print("\n" + "=" * 70 + "\n")


def run_example_queries(querier: TBPQuerier) -> None:
    """Run a set of example queries to demonstrate functionality."""
    print("\n" + "=" * 70)
    print("Running Example Queries")
    print("=" * 70 + "\n")

    examples = [
        ("What is wisdom?", None),
        ("Exodus from Egypt", None),
        ("Creation and image of God", None),
        ("Holy Spirit", "timestamp"),
        ("covenant", "bible_reference"),
    ]

    for query_text, strategy in examples:
        if strategy:
            print(f"\nQuery: '{query_text}' (strategy={strategy})")
            results = querier.query_by_strategy(query_text, strategy, n_results=3)
        else:
            print(f"\nQuery: '{query_text}'")
            results = querier.query(query_text, n_results=3)

        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            distances = results["distances"][0] if results.get("distances") else []
            metadatas = results["metadatas"][0] if results.get("metadatas") else []

            print(f"  Found {len(ids)} results:")
            for i, doc_id in enumerate(ids[:3]):
                dist = distances[i] if i < len(distances) else "N/A"
                meta = metadatas[i] if i < len(metadatas) else {}
                title = meta.get("title", "N/A") if isinstance(meta, dict) else "N/A"
                print(f"    {i + 1}. {title} (distance: {dist})")
        else:
            print("  No results found")

    print("\n" + "=" * 70 + "\n")


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
    """Main entry point for the query script."""
    parser = argparse.ArgumentParser(
        description="Query and explore BibleProject ChromaDB collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="bibleproject",
        help="Name of the ChromaDB collection (default: bibleproject)",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query text for semantic search",
    )
    parser.add_argument(
        "--n-results",
        type=int,
        default=5,
        help="Number of results to return (default: 5)",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["timestamp", "bible_reference", "semantic"],
        help="Filter by chunking strategy",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Filter by category",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show collection statistics",
    )
    parser.add_argument(
        "--browse",
        type=int,
        metavar="LIMIT",
        help="Browse a sample of documents (specify limit)",
    )
    parser.add_argument(
        "--doc-id",
        type=str,
        help="Retrieve a specific document by ID",
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Run example queries to demonstrate functionality",
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

    # Create querier and connect
    querier = TBPQuerier(collection_name=args.collection)

    if not querier.connect():
        print(f"\nError: Collection '{args.collection}' not found")
        print("\nPlease run the ingestion script first:")
        print("  python scripts/extract_tbp_step3_ingest.py")
        print("\nOr use --list-collections to see available collections.")
        sys.exit(1)

    # Handle stats mode
    if args.stats:
        stats = querier.get_stats()
        print_stats(stats)

    # Handle browse mode
    if args.browse:
        results = querier.browse_sample(limit=args.browse, strategy=args.strategy)
        print_browse_results(results, args.browse)

    # Handle doc-id mode
    if args.doc_id:
        results = querier.get_document_by_id(args.doc_id)
        if results and results.get("ids"):
            print(f"\nDocument: {args.doc_id}")
            print("-" * 70)
            print(json.dumps(results, indent=2))
        else:
            print(f"\nDocument '{args.doc_id}' not found")

    # Handle query mode
    if args.query:
        if args.strategy:
            results = querier.query_by_strategy(args.query, args.strategy, args.n_results)
        elif args.category:
            results = querier.query_by_category(args.query, args.category, args.n_results)
        else:
            results = querier.query(args.query, args.n_results)

        print_query_results(results, args.query)

    # Handle examples mode
    if args.examples:
        run_example_queries(querier)

    # If no specific mode was requested, show stats by default
    if not any([args.stats, args.browse, args.doc_id, args.query, args.examples]):
        stats = querier.get_stats()
        print_stats(stats)
        print("\nTip: Use --query 'your search text' to search the collection")
        print("     Use --examples to see example queries")
        print("     Use --help to see all options\n")


if __name__ == "__main__":
    main()
