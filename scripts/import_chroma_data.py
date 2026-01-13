#!/usr/bin/env python3
"""Import ChromaDB data from JSON export file."""

import gzip
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bt_servant_engine.adapters.chroma import (
    create_chroma_collection,
    get_or_create_chroma_collection,
    list_chroma_collections,
)


def import_collection(import_file: Path) -> None:
    """Import a ChromaDB collection from JSON file.

    Args:
        import_file: Path to JSON or JSON.gz file
    """
    print(f"Importing from: {import_file}")

    # Open file (handle gzip if needed)
    if import_file.suffix == ".gz":
        print("Detected gzip file, decompressing...")
        with gzip.open(import_file, "rt") as f:
            data = json.load(f)
    else:
        with open(import_file, "r") as f:
            data = json.load(f)

    collection_name = data["collection_name"]
    batches = data["batches"]

    print(f"Collection: {collection_name}")
    print(f"Batches: {len(batches)}")

    # Check if collection already exists
    existing = list_chroma_collections()
    if collection_name in existing:
        print(f"WARNING: Collection '{collection_name}' already exists!")
        response = input("Overwrite? This will delete existing data! (yes/NO): ")
        if response.lower() != "yes":
            print("Aborted.")
            return
        # Delete and recreate
        from bt_servant_engine.adapters.chroma import delete_chroma_collection

        print(f"Deleting existing collection '{collection_name}'...")
        delete_chroma_collection(collection_name)

    # Create collection
    print(f"Creating collection '{collection_name}'...")
    collection = get_or_create_chroma_collection(collection_name)

    # Import batches
    total_docs = 0
    for i, batch in enumerate(batches, 1):
        ids = batch["ids"]
        documents = batch["documents"]
        metadatas = batch["metadatas"]
        embeddings = batch["embeddings"]

        if not ids:
            continue

        print(f"Importing batch {i}/{len(batches)}: {len(ids)} documents...", end="", flush=True)

        try:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
            total_docs += len(ids)
            print(" OK")
        except Exception as e:
            print(f" FAILED: {e}")
            print("Continuing with next batch...")

    print(f"\nImport complete!")
    print(f"Total documents imported: {total_docs}")
    print(f"Final collection count: {collection.count()}")


def main():
    """Import all collections from exports directory."""
    exports_dir = Path("exports")

    if not exports_dir.exists():
        print(f"ERROR: exports directory not found at {exports_dir}")
        print("Run export_chroma_data.py first to create exports.")
        sys.exit(1)

    # Find all export files
    export_files = list(exports_dir.glob("*_export.json*"))

    if not export_files:
        print(f"No export files found in {exports_dir}")
        sys.exit(1)

    print("=" * 60)
    print("ChromaDB Import")
    print("=" * 60)
    print()
    print(f"Found {len(export_files)} export file(s):")
    for f in export_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name} ({size_mb:.2f} MB)")
    print()

    # Import each file
    for export_file in export_files:
        print("-" * 60)
        import_collection(export_file)
        print()

    print("=" * 60)
    print("All imports complete!")
    print()
    print("Current collections:")
    for col in list_chroma_collections():
        from bt_servant_engine.adapters.chroma import count_documents_in_collection

        count = count_documents_in_collection(col)
        print(f"  - {col}: {count} documents")


if __name__ == "__main__":
    main()
