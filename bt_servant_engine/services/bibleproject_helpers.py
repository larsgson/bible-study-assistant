"""BibleProject resource helpers for metadata enhancement and result formatting.

This module provides utilities for working with BibleProject resources retrieved
from ChromaDB, including video link generation, timestamp formatting, and
result enhancement.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from bt_servant_engine.core.logging import get_logger

logger = get_logger(__name__)


def enhance_bibleproject_metadata(doc: dict[str, Any]) -> dict[str, Any]:
    """Enhance BibleProject document metadata with computed fields.

    Args:
        doc: Document dict from ChromaDB query with metadata

    Returns:
        Enhanced document dict with additional computed fields
    """
    if doc.get("collection_name") != "bibleproject":
        return doc

    metadata = doc.get("metadata", {})
    if not isinstance(metadata, dict):
        return doc

    # Add video link if timestamp is present
    if "start_time" in metadata and "video_timestamp" in metadata:
        video_url = generate_video_link(metadata)
        if video_url:
            metadata["video_url"] = video_url

    # Add formatted timestamp
    if "start_time" in metadata and "end_time" in metadata:
        metadata["timestamp_display"] = f"{metadata['start_time']} - {metadata['end_time']}"

    # Add strategy display name
    strategy = metadata.get("strategy", "")
    strategy_names = {
        "timestamp": "Video Timestamp",
        "bible_reference": "Scripture Reference",
        "semantic": "Thematic Content",
    }
    if strategy in strategy_names:
        metadata["strategy_display"] = strategy_names[strategy]

    doc["metadata"] = metadata
    return doc


def generate_video_link(metadata: dict[str, Any]) -> str | None:
    """Generate a BibleProject video URL with timestamp.

    Args:
        metadata: Document metadata containing title and timestamp info

    Returns:
        Video URL with timestamp anchor, or None if cannot be generated
    """
    if not isinstance(metadata, dict):
        return None

    # Check if we have the required fields
    title = metadata.get("title", "")
    start_seconds = metadata.get("start_seconds")

    if not title or start_seconds is None:
        return None

    # Clean and format the title for URL
    # BibleProject video URLs typically use lowercase with hyphens
    url_slug = title.lower()
    url_slug = url_slug.replace(" ", "-")
    url_slug = url_slug.replace("_", "-")
    # Remove special characters
    url_slug = "".join(c for c in url_slug if c.isalnum() or c == "-")
    # Remove multiple consecutive hyphens
    while "--" in url_slug:
        url_slug = url_slug.replace("--", "-")
    url_slug = url_slug.strip("-")

    # Build the video URL
    # Format: https://bibleproject.com/explore/video/{slug}#t={seconds}
    base_url = "https://bibleproject.com/explore/video"
    video_url = f"{base_url}/{url_slug}#t={int(start_seconds)}"

    return video_url


def format_bibleproject_attribution(doc: dict[str, Any]) -> str:
    """Format a citation/attribution string for a BibleProject document.

    Args:
        doc: Document dict from ChromaDB query

    Returns:
        Formatted attribution string
    """
    metadata = doc.get("metadata", {})
    if not isinstance(metadata, dict):
        return "BibleProject"

    parts = ["BibleProject"]

    # Add title
    title = metadata.get("title")
    if title:
        parts.append(f'"{title}"')

    # Add series if different from title
    series = metadata.get("series")
    if series and series != metadata.get("category"):
        parts.append(f"({series})")

    # Add timestamp if present
    if "timestamp_display" in metadata:
        parts.append(f"[{metadata['timestamp_display']}]")

    return " ".join(parts)


def format_bibleproject_result(doc: dict[str, Any]) -> str:
    """Format a BibleProject document for display in RAG responses.

    Args:
        doc: Document dict from ChromaDB query

    Returns:
        Formatted string for inclusion in responses
    """
    # Enhance metadata first
    enhanced = enhance_bibleproject_metadata(doc)
    metadata = enhanced.get("metadata", {})

    # Start with the document text
    text = enhanced.get("document_text", "")

    # Build footer with attribution and links
    footer_parts = []

    # Add attribution
    attribution = format_bibleproject_attribution(enhanced)
    footer_parts.append(f"Source: {attribution}")

    # Add video link if available
    video_url = metadata.get("video_url")
    if video_url:
        timestamp = metadata.get("start_time", "")
        footer_parts.append(f"Watch: {video_url} (from {timestamp})")

    # Add strategy info if present
    strategy_display = metadata.get("strategy_display")
    if strategy_display:
        footer_parts.append(f"Type: {strategy_display}")

    # Combine text with footer
    if footer_parts:
        footer = "\n".join(footer_parts)
        return f"{text}\n\n{footer}"

    return text


def should_include_bibleproject_collection(query: str) -> bool:
    """Determine if BibleProject collection should be included in search.

    This can be enhanced with more sophisticated logic based on query content.

    Args:
        query: The user's query

    Returns:
        True if BibleProject collection should be queried
    """
    # For now, always include BibleProject in searches
    # This can be refined later to detect specific keywords or topics
    return True


def deduplicate_bibleproject_results(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate BibleProject results from different strategies.

    When the same content appears in multiple strategies (timestamp, bible_reference,
    semantic), prefer the most specific strategy for the context.

    Args:
        docs: List of documents from ChromaDB query

    Returns:
        Deduplicated list of documents
    """
    bp_docs = [d for d in docs if d.get("collection_name") == "bibleproject"]
    other_docs = [d for d in docs if d.get("collection_name") != "bibleproject"]

    if not bp_docs:
        return docs

    # Group by source document (filename + title)
    seen_sources = {}
    strategy_priority = {
        "bible_reference": 3,  # Highest priority for scripture-focused queries
        "timestamp": 2,  # Good for temporal/sequential context
        "semantic": 1,  # Fallback for general queries
    }

    for doc in bp_docs:
        metadata = doc.get("metadata", {})
        if not isinstance(metadata, dict):
            continue

        # Create unique key for source document
        filename = metadata.get("filename", "")
        title = metadata.get("title", "")
        source_key = f"{filename}:{title}"

        if not source_key or source_key == ":":
            # Can't dedupe without source info, keep as is
            continue

        strategy = metadata.get("strategy", "semantic")
        current_priority = strategy_priority.get(strategy, 0)

        if source_key not in seen_sources:
            seen_sources[source_key] = (doc, current_priority)
        else:
            existing_doc, existing_priority = seen_sources[source_key]
            if current_priority > existing_priority:
                # Replace with higher priority strategy
                seen_sources[source_key] = (doc, current_priority)

    # Combine deduplicated BP docs with other docs
    deduped_bp = [doc for doc, _ in seen_sources.values()]

    logger.info(
        "deduplicated %d BibleProject docs to %d (removed %d duplicates)",
        len(bp_docs),
        len(deduped_bp),
        len(bp_docs) - len(deduped_bp),
    )

    return other_docs + deduped_bp


def get_bibleproject_stats(docs: list[dict[str, Any]]) -> dict[str, Any]:
    """Get statistics about BibleProject documents in results.

    Args:
        docs: List of documents from ChromaDB query

    Returns:
        Dict with statistics
    """
    bp_docs = [d for d in docs if d.get("collection_name") == "bibleproject"]

    if not bp_docs:
        return {
            "count": 0,
            "has_bibleproject": False,
        }

    strategies = set()
    categories = set()
    has_timestamps = 0
    has_bible_refs = 0

    for doc in bp_docs:
        metadata = doc.get("metadata", {})
        if not isinstance(metadata, dict):
            continue

        strategy = metadata.get("strategy")
        if strategy:
            strategies.add(strategy)

        category = metadata.get("category")
        if category:
            categories.add(category)

        if metadata.get("start_time"):
            has_timestamps += 1

        if metadata.get("has_bible_refs") or metadata.get("bible_ref_count", 0) > 0:
            has_bible_refs += 1

    return {
        "count": len(bp_docs),
        "has_bibleproject": True,
        "strategies": list(strategies),
        "categories": list(categories),
        "with_timestamps": has_timestamps,
        "with_bible_refs": has_bible_refs,
    }
