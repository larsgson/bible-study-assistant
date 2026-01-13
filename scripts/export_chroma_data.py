#!/usr/bin/env python3
"""Export ChromaDB data to JSON format for transfer to fly.io."""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bt_servant_engine.adapters.chroma import (
    get_chroma_collection,
    iter_collection_batches,
    list_chroma_collections,
)


def export_collection(collection_name: str, output_file: Path, batch_size: int = 100) -> None:
    """Export a ChromaDB collection to JSON file.

    Args:
        collection_name: Name of the collection to export
        output_file: Path to output JSON file
        batch_size: Number of documents per batch
    """
    print(f"Exporting collection: {collection_name}")

    col = get_chroma_collection(collection_name)
    if not col:
        print(f"ERROR: Collection '{collection_name}' not found")
        return

    all_data = {"collection_name": collection_name, "batches": []}

    total_docs = 0
    for batch in iter_collection_batches(col, batch_size=batch_size, include_embeddings=True):
        # Convert embeddings (numpy arrays) to lists for JSON serialization
        embeddings = batch.get("embeddings", [])
        if embeddings is not None and len(embeddings) > 0:
            embeddings = [emb.tolist() if hasattr(emb, "tolist") else emb for emb in embeddings]

        batch_data = {
            "ids": batch.get("ids", []),
            "documents": batch.get("documents", []),
            "metadatas": batch.get("metadatas", []),
            "embeddings": embeddings,
        }
        all_data["batches"].append(batch_data)
        total_docs += len(batch_data["ids"])
        print(f"  Batch {len(all_data['batches'])}: {len(batch_data['ids'])} documents")

    print(f"\nTotal documents exported: {total_docs}")
    print(f"Writing to: {output_file}")

    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"File size: {file_size_mb:.2f} MB")


def main():
    """Export all collections."""
    collections = list_chroma_collections()

    if not collections:
        print("No collections found in ChromaDB")
        return

    print(f"Found collections: {collections}\n")

    output_dir = Path("exports")
    output_dir.mkdir(exist_ok=True)

    for collection_name in collections:
        output_file = output_dir / f"{collection_name}_export.json"
        export_collection(collection_name, output_file)
        print()


if __name__ == "__main__":
    main()
