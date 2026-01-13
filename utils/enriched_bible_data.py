"""Enriched Bible data utilities with cross-links to resources.

Loads Bible verses enriched with metadata pointing to:
- BibleProject chunks that discuss the verse
- Translation helps for the verse
- TA articles relevant to the verse

This enables intent inference without LLM and direct resource lookup.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# Project root
_project_root = Path(__file__).parent.parent


class EnrichedVerseNotFoundError(Exception):
    """Raised when enriched verse data is not found."""

    pass


@lru_cache(maxsize=128)
def load_enriched_book(lang: str, translation: str, book_stem: str) -> list[dict[str, Any]]:
    """Load enriched book JSON from sources/bible_data_enriched (cached).

    Args:
        lang: Language code (e.g., "en", "fr", "id")
        translation: Translation name (e.g., "bsb", "tbi")
        book_stem: Book file stem (e.g., "gen", "mat")

    Returns:
        List of enriched verse objects with metadata

    Raises:
        EnrichedVerseNotFoundError: If enriched data doesn't exist
        FileNotFoundError: If the book file is not found
    """
    enriched_root = _project_root / "sources" / "bible_data_enriched"

    if not enriched_root.exists():
        raise EnrichedVerseNotFoundError(
            f"Enriched Bible data not found at {enriched_root}. "
            "Run scripts/build_verse_resource_index.py first."
        )

    book_path = enriched_root / lang / translation / f"{book_stem}.json"

    if not book_path.exists():
        raise FileNotFoundError(f"Enriched book not found: {book_path}")

    with book_path.open(encoding="utf-8") as f:
        return json.load(f)


def get_enriched_verse(
    reference: str,
    lang: str = "en",
    translation: str = "bsb",
) -> dict[str, Any] | None:
    """Get enriched verse data by reference.

    Args:
        reference: Bible reference (e.g., "Gen 1:1", "John 3:16")
        lang: Language code (default: "en")
        translation: Translation name (default: "bsb")

    Returns:
        Enriched verse dict with metadata, or None if not found

    Example:
        >>> verse = get_enriched_verse("Gen 3:15")
        >>> print(verse["text"])
        >>> print(verse["metadata"]["bibleproject_chunks"])
        >>> print(verse["metadata"]["applicable_intents"])
    """
    from utils.bible_data import parse_reference_simple

    # Parse reference to get book stem and chapter:verse
    parsed = parse_reference_simple(reference)
    if not parsed:
        return None

    book_stem = parsed["book"]
    target_chapter = parsed["chapter"]
    target_verse = parsed["verse"]

    try:
        verses = load_enriched_book(lang, translation, book_stem)
    except (EnrichedVerseNotFoundError, FileNotFoundError):
        return None

    # Find matching verse by chapter and verse number (not exact string match)
    for verse in verses:
        verse_ref = verse.get("reference", "")
        verse_parsed = parse_reference_simple(verse_ref)
        if (
            verse_parsed
            and verse_parsed["chapter"] == target_chapter
            and verse_parsed["verse"] == target_verse
        ):
            return verse

    return None


def get_enriched_verses_for_range(
    book_stem: str,
    chapter: int,
    verse_start: int,
    verse_end: int,
    lang: str = "en",
    translation: str = "bsb",
) -> list[dict[str, Any]]:
    """Get enriched verses for a range.

    Args:
        book_stem: Book abbreviation (e.g., "gen", "joh")
        chapter: Chapter number
        verse_start: Starting verse number
        verse_end: Ending verse number
        lang: Language code
        translation: Translation name

    Returns:
        List of enriched verse dicts
    """
    try:
        verses = load_enriched_book(lang, translation, book_stem)
    except (EnrichedVerseNotFoundError, FileNotFoundError):
        return []

    # Filter verses in range
    result = []
    for verse in verses:
        ref = verse.get("reference", "")
        # Parse reference to check if in range
        if f" {chapter}:" in ref:
            # Extract verse number
            try:
                verse_num = int(ref.split(":")[-1])
                if verse_start <= verse_num <= verse_end:
                    result.append(verse)
            except (ValueError, IndexError):
                continue

    return result


def get_resource_summary(verse_data: dict[str, Any]) -> dict[str, Any]:
    """Get summary of resources available for a verse.

    Args:
        verse_data: Enriched verse dict

    Returns:
        Summary dict with resource availability flags
    """
    metadata = verse_data.get("metadata", {})
    return metadata.get(
        "resource_summary",
        {
            "has_bibleproject": False,
            "has_translation_notes": False,
            "has_ta_articles": False,
            "richness_score": 0.0,
        },
    )


def get_applicable_intents(verse_data: dict[str, Any]) -> list[str]:
    """Get list of applicable intents for a verse.

    Args:
        verse_data: Enriched verse dict

    Returns:
        List of intent strings (e.g., ["retrieve-scripture", "get-translation-helps"])
    """
    metadata = verse_data.get("metadata", {})
    return metadata.get("applicable_intents", ["retrieve-scripture"])


def get_bibleproject_links(verse_data: dict[str, Any]) -> list[dict[str, str]]:
    """Get BibleProject chunks linked to a verse.

    Args:
        verse_data: Enriched verse dict

    Returns:
        List of dicts with chunk_id, title, and context
    """
    metadata = verse_data.get("metadata", {})
    return metadata.get("bibleproject_chunks", [])


def get_translation_helps_info(verse_data: dict[str, Any]) -> dict[str, Any] | None:
    """Get translation helps info for a verse.

    Args:
        verse_data: Enriched verse dict

    Returns:
        Dict with note_count and ta_articles, or None if no helps
    """
    metadata = verse_data.get("metadata", {})
    return metadata.get("translation_helps")


def has_rich_resources(verse_data: dict[str, Any], threshold: float = 0.5) -> bool:
    """Check if verse has rich resources (richness score above threshold).

    Args:
        verse_data: Enriched verse dict
        threshold: Minimum richness score (0.0 to 1.0)

    Returns:
        True if richness score >= threshold
    """
    summary = get_resource_summary(verse_data)
    return summary.get("richness_score", 0.0) >= threshold


def get_index_summary() -> dict[str, Any] | None:
    """Get summary statistics for the enriched index.

    Returns:
        Summary dict with statistics, or None if not available
    """
    summary_path = _project_root / "sources" / "bible_data_enriched" / "index_summary.json"

    if not summary_path.exists():
        return None

    with summary_path.open(encoding="utf-8") as f:
        return json.load(f)


def is_enriched_data_available() -> bool:
    """Check if enriched Bible data is available.

    Returns:
        True if enriched data exists
    """
    enriched_root = _project_root / "sources" / "bible_data_enriched"
    return enriched_root.exists()


__all__ = [
    "EnrichedVerseNotFoundError",
    "load_enriched_book",
    "get_enriched_verse",
    "get_enriched_verses_for_range",
    "get_resource_summary",
    "get_applicable_intents",
    "get_bibleproject_links",
    "get_translation_helps_info",
    "has_rich_resources",
    "get_index_summary",
    "is_enriched_data_available",
]
