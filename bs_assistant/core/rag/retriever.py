"""Unified RAG retriever combining multiple retrieval strategies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bs_assistant.config import settings
from bs_assistant.core.detectors import BibleReference
from bs_assistant.core.rag.vector_store import vector_store
from bs_assistant.models import RetrievedResource

if TYPE_CHECKING:
    from bs_assistant.services.bible_service import BibleService


class Retriever:
    """Unified retriever combining multiple strategies."""

    def __init__(self) -> None:
        """Initialize retriever."""
        self.vector_store = vector_store
        self._bible_service = None

    @property
    def bible_service(self):
        """Lazy load bible service to avoid circular import."""
        if self._bible_service is None:
            from bs_assistant.services.bible_service import bible_service

            self._bible_service = bible_service
        return self._bible_service

    def retrieve(
        self,
        query: str,
        bible_ref: BibleReference | None = None,
        language: str = "en",
        translation: str = "bsb",
        max_results: int | None = None,
    ) -> list[RetrievedResource]:
        """
        Retrieve relevant resources for a query.

        Args:
            query: User query text
            bible_ref: Detected Bible reference (if any)
            language: Language code
            translation: Translation identifier
            max_results: Maximum number of results to return

        Returns:
            List of retrieved resources
        """
        max_results = max_results or settings.MAX_RETRIEVAL_RESULTS
        resources: list[RetrievedResource] = []

        # Strategy 1: Direct Bible verse retrieval (if reference detected)
        if bible_ref:
            verse_resources = self._retrieve_bible_verses(bible_ref, language, translation)
            resources.extend(verse_resources)

        # Strategy 2: Vector search for semantic matches
        vector_resources = self._retrieve_from_vector_store(query, max_results)
        resources.extend(vector_resources)

        # Strategy 3: Cross-references (if we have a verse)
        if bible_ref:
            cross_ref_resources = self._retrieve_cross_references(bible_ref, language, translation)
            resources.extend(cross_ref_resources)

        # Deduplicate and score
        resources = self._deduplicate_resources(resources)

        # Sort by score (if available) and limit
        resources.sort(key=lambda r: r.score or 0, reverse=True)
        return resources[:max_results]

    def _retrieve_bible_verses(
        self,
        reference: BibleReference,
        language: str,
        translation: str,
    ) -> list[RetrievedResource]:
        """
        Retrieve Bible verses directly.

        Args:
            reference: Bible reference
            language: Language code
            translation: Translation identifier

        Returns:
            List of verse resources
        """
        resources: list[RetrievedResource] = []

        # Get verses based on reference type
        if reference.verse_start is not None:
            # Specific verse or range
            verses = self.bible_service.get_verses(reference, language, translation)
        elif reference.chapter is not None:
            # Whole chapter (with limit)
            verses = self.bible_service.get_chapter(
                reference,
                language,
                translation,
                limit=settings.RETRIEVE_SCRIPTURE_VERSE_LIMIT,
            )
        else:
            verses = []

        if not verses:
            return resources

        # Consolidate verses into a single passage block
        first = verses[0]
        last = verses[-1]
        if len(verses) == 1:
            passage_ref = first["reference"]
        else:
            passage_ref = f"{first['reference']}–{last['reference']}"

        passage_text = "\n".join(v["text"] for v in verses)

        resources.append(
            RetrievedResource(
                type="verse",
                content=passage_text,
                reference=passage_ref,
                score=0.95,
                metadata={
                    "book": first.get("book"),
                    "chapter": first.get("chapter"),
                    "verse_start": first.get("verse"),
                    "verse_end": last.get("verse"),
                    "translation": first.get("translation"),
                    "language": first.get("language"),
                    "verse_count": len(verses),
                },
            )
        )

        return resources

    def _retrieve_from_vector_store(
        self,
        query: str,
        max_results: int,
    ) -> list[RetrievedResource]:
        """
        Retrieve from vector store using semantic search.

        Args:
            query: Query text
            max_results: Maximum results

        Returns:
            List of resources from vector store
        """
        resources: list[RetrievedResource] = []

        # Try to query available collections
        collections = self.vector_store.list_collections()

        for collection_name in collections:
            try:
                results = self.vector_store.query(
                    collection_name=collection_name,
                    query_texts=[query],
                    n_results=max_results,
                )

                # Process results
                if results.get("ids") and results["ids"][0]:
                    ids = results["ids"][0]
                    documents = results.get("documents", [[]])[0]
                    metadatas = results.get("metadatas", [[]])[0]
                    distances = results.get("distances", [[]])[0]

                    for i, doc_id in enumerate(ids):
                        # Convert distance to similarity score (lower distance = higher similarity)
                        distance = distances[i] if i < len(distances) else 1.0
                        score = 1.0 / (1.0 + distance)

                        # Filter by similarity threshold
                        if score < settings.SIMILARITY_THRESHOLD:
                            continue

                        document = documents[i] if i < len(documents) else ""
                        metadata = metadatas[i] if i < len(metadatas) else {}

                        # Determine resource type from collection or metadata
                        resource_type = metadata.get("type", collection_name)

                        resources.append(
                            RetrievedResource(
                                type=resource_type,
                                content=document,
                                reference=metadata.get("reference"),
                                score=score,
                                metadata={
                                    **metadata,
                                    "collection": collection_name,
                                    "doc_id": doc_id,
                                },
                            )
                        )
            except Exception:
                # Skip collections that error
                continue

        return resources

    def _retrieve_cross_references(
        self,
        reference: BibleReference,
        language: str,
        translation: str,
    ) -> list[RetrievedResource]:
        """
        Retrieve cross-references for a Bible reference.

        Args:
            reference: Bible reference
            language: Language code
            translation: Translation identifier

        Returns:
            List of cross-reference resources
        """
        resources: list[RetrievedResource] = []

        # Try to load enriched verse data
        try:
            from utils.enriched_bible_data import get_enriched_verse

            enriched = get_enriched_verse(str(reference), lang=language, translation=translation)

            if enriched and enriched.get("metadata"):
                metadata = enriched["metadata"]

                # BibleProject chunks
                bp_chunks = metadata.get("bibleproject_chunks", [])
                for chunk in bp_chunks[:3]:  # Limit to top 3
                    resources.append(
                        RetrievedResource(
                            type="bibleproject",
                            content=chunk.get("content", ""),
                            reference=str(reference),
                            score=0.9,
                            metadata={
                                "source": "bibleproject",
                                "chunk_id": chunk.get("id"),
                            },
                        )
                    )

                # Translation helps
                tn_data = metadata.get("translation_notes", [])
                for note in tn_data[:3]:  # Limit to top 3
                    resources.append(
                        RetrievedResource(
                            type="translation_notes",
                            content=note.get("content", ""),
                            reference=str(reference),
                            score=0.85,
                            metadata={
                                "source": "translation_notes",
                                "note_id": note.get("id"),
                            },
                        )
                    )

                # Translation words
                tw_data = metadata.get("translation_words", [])
                for word in tw_data[:3]:  # Limit to top 3
                    resources.append(
                        RetrievedResource(
                            type="translation_words",
                            content=word.get("content", ""),
                            reference=str(reference),
                            score=0.8,
                            metadata={
                                "source": "translation_words",
                                "word": word.get("word"),
                            },
                        )
                    )

        except Exception:
            # Enriched data not available or error loading
            pass

        return resources

    def _deduplicate_resources(self, resources: list[RetrievedResource]) -> list[RetrievedResource]:
        """
        Remove duplicate resources.

        Args:
            resources: List of resources

        Returns:
            Deduplicated list
        """
        seen_content: set[str] = set()
        deduplicated: list[RetrievedResource] = []

        for resource in resources:
            # Create unique key from content and reference
            key = f"{resource.content[:100]}|{resource.reference or ''}"

            if key not in seen_content:
                seen_content.add(key)
                deduplicated.append(resource)

        return deduplicated


# Global instance
retriever = Retriever()


__all__ = ["Retriever", "retriever"]
