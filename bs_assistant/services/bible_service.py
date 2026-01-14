"""Bible data service for verse and passage retrieval."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from bs_assistant.config import settings
from bs_assistant.core.detectors import BibleReference

# Bible data root
BIBLE_DATA_ROOT = Path("sources") / "bible_data"
ENRICHED_DATA_ROOT = Path("sources") / "bible_data_enriched"


class BibleDataNotFoundError(Exception):
    """Raised when Bible data is not available."""

    pass


class BibleService:
    """Service for retrieving Bible verses and passages."""

    def __init__(self) -> None:
        """Initialize Bible service."""
        self._bible_data_root = BIBLE_DATA_ROOT
        self._enriched_data_root = ENRICHED_DATA_ROOT

    def _alias_language(self, lang_code: str | None) -> str:
        """
        Normalize language code with common aliases.

        Args:
            lang_code: Language code to normalize

        Returns:
            Normalized language code
        """
        if not lang_code:
            return "en"

        code = str(lang_code).strip().lower()

        # Common aliases
        aliases = {
            "pt-br": "pt",
            "pt_pt": "pt",
            "pt-pt": "pt",
            "ptbr": "pt",
            "en-us": "en",
            "en-gb": "en",
        }

        return aliases.get(code, code)

    def _resolve_bible_data_path(
        self,
        language: str = "en",
        translation: str = "bsb",
    ) -> tuple[Path, str, str]:
        """
        Resolve path to Bible data.

        Args:
            language: Language code
            translation: Translation identifier

        Returns:
            Tuple of (data_path, resolved_language, resolved_translation)

        Raises:
            BibleDataNotFoundError: If no suitable data found
        """
        lang = self._alias_language(language)

        # Try requested language and translation
        path = self._bible_data_root / lang / translation
        if path.exists() and any(path.glob("*.json")):
            return path, lang, translation

        # Try requested language with any translation
        lang_dir = self._bible_data_root / lang
        if lang_dir.exists():
            for trans_dir in lang_dir.iterdir():
                if trans_dir.is_dir() and any(trans_dir.glob("*.json")):
                    return trans_dir, lang, trans_dir.name

        # Fallback to English BSB
        fallback_path = self._bible_data_root / "en" / "bsb"
        if fallback_path.exists() and any(fallback_path.glob("*.json")):
            return fallback_path, "en", "bsb"

        raise BibleDataNotFoundError(
            f"Bible data not found for {lang}/{translation}. Expected at {self._bible_data_root}"
        )

    @lru_cache(maxsize=128)
    def _load_book(
        self,
        book_stem: str,
        language: str = "en",
        translation: str = "bsb",
    ) -> list[dict[str, Any]]:
        """
        Load book data from JSON (cached).

        Args:
            book_stem: Book identifier (e.g., "gen", "mat", "jhn")
            language: Language code
            translation: Translation identifier

        Returns:
            List of verse objects

        Raises:
            FileNotFoundError: If book file not found
        """
        data_path, _, _ = self._resolve_bible_data_path(language, translation)
        book_path = data_path / f"{book_stem}.json"

        if not book_path.exists():
            raise FileNotFoundError(f"Book file not found: {book_path}")

        with book_path.open(encoding="utf-8") as f:
            return json.load(f)

    def _book_name_to_stem(self, book_name: str) -> str:
        """
        Convert book name to file stem.

        Args:
            book_name: Full or abbreviated book name

        Returns:
            Book file stem (lowercase, 3 letters)
        """
        # Mapping of book names to stems
        book_map = {
            "Genesis": "gen",
            "Exodus": "exo",
            "Leviticus": "lev",
            "Numbers": "num",
            "Deuteronomy": "deu",
            "Joshua": "jos",
            "Judges": "jdg",
            "Ruth": "rut",
            "1 Samuel": "1sa",
            "2 Samuel": "2sa",
            "1 Kings": "1ki",
            "2 Kings": "2ki",
            "1 Chronicles": "1ch",
            "2 Chronicles": "2ch",
            "Ezra": "ezr",
            "Nehemiah": "neh",
            "Esther": "est",
            "Job": "job",
            "Psalms": "psa",
            "Proverbs": "pro",
            "Ecclesiastes": "ecc",
            "Song of Solomon": "sng",
            "Isaiah": "isa",
            "Jeremiah": "jer",
            "Lamentations": "lam",
            "Ezekiel": "ezk",
            "Daniel": "dan",
            "Hosea": "hos",
            "Joel": "joe",
            "Amos": "amo",
            "Obadiah": "oba",
            "Jonah": "jon",
            "Micah": "mic",
            "Nahum": "nam",
            "Habakkuk": "hab",
            "Zephaniah": "zep",
            "Haggai": "hag",
            "Zechariah": "zec",
            "Malachi": "mal",
            "Matthew": "mat",
            "Mark": "mrk",
            "Luke": "luk",
            "John": "joh",
            "Acts": "act",
            "Romans": "rom",
            "1 Corinthians": "1co",
            "2 Corinthians": "2co",
            "Galatians": "gal",
            "Ephesians": "eph",
            "Philippians": "php",
            "Colossians": "col",
            "1 Thessalonians": "1th",
            "2 Thessalonians": "2th",
            "1 Timothy": "1ti",
            "2 Timothy": "2ti",
            "Titus": "tit",
            "Philemon": "phm",
            "Hebrews": "heb",
            "James": "jas",
            "1 Peter": "1pe",
            "2 Peter": "2pe",
            "1 John": "1jo",
            "2 John": "2jo",
            "3 John": "3jo",
            "Jude": "jud",
            "Revelation": "rev",
        }

        return book_map.get(book_name, book_name.lower()[:3])

    def get_verse(
        self,
        reference: BibleReference,
        language: str = "en",
        translation: str = "bsb",
    ) -> dict[str, Any] | None:
        """
        Get a single verse.

        Args:
            reference: Bible reference object
            language: Language code
            translation: Translation identifier

        Returns:
            Verse dict with text and metadata, or None if not found
        """
        if reference.chapter is None or reference.verse_start is None:
            return None

        try:
            book_stem = self._book_name_to_stem(reference.book)
            verses = self._load_book(book_stem, language, translation)

            # Find matching verse
            for verse in verses:
                verse_ref = verse.get("reference", "")
                # Match chapter:verse pattern
                if f"{reference.chapter}:{reference.verse_start}" in verse_ref:
                    return {
                        "reference": str(reference),
                        "text": verse.get("text", ""),
                        "book": reference.book,
                        "chapter": reference.chapter,
                        "verse": reference.verse_start,
                        "translation": translation,
                        "language": language,
                    }

            return None
        except (FileNotFoundError, BibleDataNotFoundError):
            return None

    def get_verses(
        self,
        reference: BibleReference,
        language: str = "en",
        translation: str = "bsb",
    ) -> list[dict[str, Any]]:
        """
        Get multiple verses from a reference (handles ranges).

        Args:
            reference: Bible reference object
            language: Language code
            translation: Translation identifier

        Returns:
            List of verse dicts
        """
        if reference.chapter is None or reference.verse_start is None:
            return []

        try:
            book_stem = self._book_name_to_stem(reference.book)
            verses = self._load_book(book_stem, language, translation)

            # Determine verse range
            verse_start = reference.verse_start
            verse_end = reference.verse_end or verse_start

            # Find all verses in range
            result = []
            for verse in verses:
                verse_ref = verse.get("reference", "")
                # Check if verse is in chapter and range
                if f"{reference.chapter}:" in verse_ref:
                    try:
                        verse_num = int(verse_ref.split(":")[-1])
                        if verse_start <= verse_num <= verse_end:
                            result.append(
                                {
                                    "reference": verse_ref,
                                    "text": verse.get("text", ""),
                                    "book": reference.book,
                                    "chapter": reference.chapter,
                                    "verse": verse_num,
                                    "translation": translation,
                                    "language": language,
                                }
                            )
                    except (ValueError, IndexError):
                        continue

            return result
        except (FileNotFoundError, BibleDataNotFoundError):
            return []

    def get_chapter(
        self,
        reference: BibleReference,
        language: str = "en",
        translation: str = "bsb",
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get all verses in a chapter.

        Args:
            reference: Bible reference object (must have chapter)
            language: Language code
            translation: Translation identifier
            limit: Optional limit on number of verses

        Returns:
            List of verse dicts
        """
        if reference.chapter is None:
            return []

        try:
            book_stem = self._book_name_to_stem(reference.book)
            verses = self._load_book(book_stem, language, translation)

            # Find all verses in chapter
            result = []
            for verse in verses:
                verse_ref = verse.get("reference", "")
                if f"{reference.chapter}:" in verse_ref:
                    try:
                        verse_num = int(verse_ref.split(":")[-1])
                        result.append(
                            {
                                "reference": verse_ref,
                                "text": verse.get("text", ""),
                                "book": reference.book,
                                "chapter": reference.chapter,
                                "verse": verse_num,
                                "translation": translation,
                                "language": language,
                            }
                        )

                        # Check limit
                        if limit and len(result) >= limit:
                            break
                    except (ValueError, IndexError):
                        continue

            return result
        except (FileNotFoundError, BibleDataNotFoundError):
            return []

    def get_passage_text(
        self,
        reference: BibleReference,
        language: str = "en",
        translation: str = "bsb",
    ) -> str:
        """
        Get formatted passage text.

        Args:
            reference: Bible reference object
            language: Language code
            translation: Translation identifier

        Returns:
            Formatted passage text
        """
        if reference.verse_start is not None:
            # Get specific verse(s)
            verses = self.get_verses(reference, language, translation)
        elif reference.chapter is not None:
            # Get whole chapter (with limit)
            limit = settings.RETRIEVE_SCRIPTURE_VERSE_LIMIT
            verses = self.get_chapter(reference, language, translation, limit=limit)
        else:
            return ""

        if not verses:
            return ""

        # Format as passage
        lines = [f"{verse['reference']}: {verse['text']}" for verse in verses]
        return "\n".join(lines)

    def list_available_translations(self, language: str = "en") -> list[str]:
        """
        List available translations for a language.

        Args:
            language: Language code

        Returns:
            List of translation identifiers
        """
        lang = self._alias_language(language)
        lang_dir = self._bible_data_root / lang

        if not lang_dir.exists():
            return []

        translations = []
        for trans_dir in lang_dir.iterdir():
            if trans_dir.is_dir() and any(trans_dir.glob("*.json")):
                translations.append(trans_dir.name)

        return sorted(translations)

    def list_available_languages(self) -> list[str]:
        """
        List available languages.

        Returns:
            List of language codes
        """
        if not self._bible_data_root.exists():
            return []

        languages = []
        for lang_dir in self._bible_data_root.iterdir():
            if lang_dir.is_dir():
                languages.append(lang_dir.name)

        return sorted(languages)


# Global instance
bible_service = BibleService()


__all__ = ["BibleService", "BibleDataNotFoundError", "bible_service"]
