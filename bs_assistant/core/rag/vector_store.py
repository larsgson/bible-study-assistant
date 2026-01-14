"""Vector store wrapper for ChromaDB with embeddings support."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from bs_assistant.config import settings


class VectorStore:
    """ChromaDB vector store for semantic search."""

    def __init__(self, persist_path: Path | None = None) -> None:
        """
        Initialize ChromaDB client.

        Args:
            persist_path: Path to persist ChromaDB data (defaults to config)
        """
        self.persist_path = persist_path or settings.VECTOR_STORE_PATH
        self.persist_path.mkdir(parents=True, exist_ok=True)

        # Configure ChromaDB settings
        chroma_settings = Settings(
            chroma_segment_cache_policy="LRU",
            chroma_memory_limit_bytes=1000000000,  # ~1GB
        )

        # Initialize persistent client
        self._client = chromadb.PersistentClient(
            path=str(self.persist_path),
            settings=chroma_settings,
        )

        # Set up embedding function (OpenAI ada-002)
        self._embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            model_name="text-embedding-ada-002",
            api_key=settings.OPENAI_API_KEY,
        )

    def get_or_create_collection(self, name: str) -> Any:
        """
        Get existing collection or create if it doesn't exist.

        Args:
            name: Collection name

        Returns:
            ChromaDB collection
        """
        existing = [col.name for col in self._client.list_collections()]
        if name in existing:
            return self._client.get_collection(
                name=name,
                embedding_function=self._embedding_function,
            )
        return self._client.create_collection(
            name=name,
            embedding_function=self._embedding_function,
        )

    def get_collection(self, name: str) -> Any | None:
        """
        Get existing collection.

        Args:
            name: Collection name

        Returns:
            ChromaDB collection or None if not found
        """
        existing = [col.name for col in self._client.list_collections()]
        if name in existing:
            return self._client.get_collection(
                name=name,
                embedding_function=self._embedding_function,
            )
        return None

    def list_collections(self) -> list[str]:
        """
        List all collection names.

        Returns:
            List of collection names
        """
        return [col.name for col in self._client.list_collections()]

    def create_collection(self, name: str) -> Any:
        """
        Create a new collection.

        Args:
            name: Collection name

        Returns:
            ChromaDB collection

        Raises:
            ValueError: If collection already exists
        """
        existing = self.list_collections()
        if name in existing:
            raise ValueError(f"Collection '{name}' already exists")
        return self._client.create_collection(
            name=name,
            embedding_function=self._embedding_function,
        )

    def delete_collection(self, name: str) -> None:
        """
        Delete a collection.

        Args:
            name: Collection name

        Raises:
            ValueError: If collection doesn't exist
        """
        existing = self.list_collections()
        if name not in existing:
            raise ValueError(f"Collection '{name}' not found")
        self._client.delete_collection(name=name)

    def query(
        self,
        collection_name: str,
        query_texts: list[str],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Query a collection for similar documents.

        Args:
            collection_name: Name of collection to query
            query_texts: List of query texts
            n_results: Number of results to return per query
            where: Metadata filters
            where_document: Document content filters

        Returns:
            Query results with ids, documents, metadatas, distances

        Raises:
            ValueError: If collection doesn't exist
        """
        collection = self.get_collection(collection_name)
        if collection is None:
            raise ValueError(f"Collection '{collection_name}' not found")

        kwargs: dict[str, Any] = {
            "query_texts": query_texts,
            "n_results": n_results,
        }
        if where is not None:
            kwargs["where"] = where
        if where_document is not None:
            kwargs["where_document"] = where_document

        return collection.query(**kwargs)

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        """
        Add documents to a collection.

        Args:
            collection_name: Name of collection
            documents: List of document texts
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs (auto-generated if not provided)

        Raises:
            ValueError: If collection doesn't exist
        """
        collection = self.get_collection(collection_name)
        if collection is None:
            raise ValueError(f"Collection '{collection_name}' not found")

        # Auto-generate IDs if not provided
        if ids is None:
            start_id = self._get_next_id(collection)
            ids = [str(start_id + i) for i in range(len(documents))]

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    def get_document(
        self,
        collection_name: str,
        document_id: str,
    ) -> tuple[str, dict[str, Any]] | None:
        """
        Get a specific document by ID.

        Args:
            collection_name: Name of collection
            document_id: Document ID

        Returns:
            Tuple of (document_text, metadata) or None if not found
        """
        collection = self.get_collection(collection_name)
        if collection is None:
            return None

        result = collection.get(
            ids=[document_id],
            include=["documents", "metadatas"],
        )

        if not result["ids"]:
            return None

        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [{}])

        if not documents:
            return None

        return documents[0], metadatas[0] if metadatas else {}

    def delete_document(
        self,
        collection_name: str,
        document_id: str,
    ) -> None:
        """
        Delete a document from a collection.

        Args:
            collection_name: Name of collection
            document_id: Document ID

        Raises:
            ValueError: If collection or document doesn't exist
        """
        collection = self.get_collection(collection_name)
        if collection is None:
            raise ValueError(f"Collection '{collection_name}' not found")

        # Check if document exists
        result = collection.get(ids=[document_id])
        if not result["ids"]:
            raise ValueError(f"Document '{document_id}' not found")

        collection.delete(ids=[document_id])

    def count_documents(self, collection_name: str) -> int:
        """
        Count documents in a collection.

        Args:
            collection_name: Name of collection

        Returns:
            Number of documents

        Raises:
            ValueError: If collection doesn't exist
        """
        collection = self.get_collection(collection_name)
        if collection is None:
            raise ValueError(f"Collection '{collection_name}' not found")

        return collection.count()

    def _get_next_id(self, collection: Any) -> int:
        """
        Get next numeric ID for a collection.

        Args:
            collection: ChromaDB collection

        Returns:
            Next available integer ID
        """
        try:
            results = collection.get(limit=10000)
            if not results["ids"]:
                return 1

            # Get max numeric ID
            int_ids = [int(doc_id) for doc_id in results["ids"] if doc_id.isdigit()]
            return max(int_ids, default=0) + 1
        except Exception:
            return 1


# Global instance
vector_store = VectorStore()


__all__ = ["VectorStore", "vector_store"]
