"""Pattern-based intent inference using enriched verse metadata.

Comprehensive Bible reference extraction supporting multiple formats:
- Standard: "John 3:16", "Gen. 3:15"
- Verbose: "Genesis chapter 3 verse 15"
- Ordinal verbose: "first john chapter 3 verse 16"
- Ordinal standard: "1st John 3:16", "second peter 1:3"
- Chapter-verse: "Romans 8 verse 28"
"""

from __future__ import annotations

import re
from typing import Optional

from bt_servant_engine.core.intents import IntentType
from bt_servant_engine.core.logging import get_logger

logger = get_logger(__name__)

# Book name normalization for reference extraction
# Maps various forms to canonical abbreviations used in enriched data
BOOK_NORMALIZATION = {
    # Genesis-Deuteronomy
    "genesis": "Gen",
    "gen": "Gen",
    "ge": "Gen",
    "exodus": "Exo",
    "exo": "Exo",
    "ex": "Exo",
    "leviticus": "Lev",
    "lev": "Lev",
    "numbers": "Num",
    "num": "Num",
    "deuteronomy": "Deu",
    "deu": "Deu",
    "deut": "Deu",
    # 1 Samuel, 2 Samuel
    "1 samuel": "1Sa",
    "1samuel": "1Sa",
    "1sa": "1Sa",
    "1sam": "1Sa",
    "first samuel": "1Sa",
    "1st samuel": "1Sa",
    "i samuel": "1Sa",
    "2 samuel": "2Sa",
    "2samuel": "2Sa",
    "2sa": "2Sa",
    "2sam": "2Sa",
    "second samuel": "2Sa",
    "2nd samuel": "2Sa",
    "ii samuel": "2Sa",
    # 1 Kings, 2 Kings
    "1 kings": "1Ki",
    "1kings": "1Ki",
    "1ki": "1Ki",
    "first kings": "1Ki",
    "1st kings": "1Ki",
    "i kings": "1Ki",
    "2 kings": "2Ki",
    "2kings": "2Ki",
    "2ki": "2Ki",
    "second kings": "2Ki",
    "2nd kings": "2Ki",
    "ii kings": "2Ki",
    # 1 Chronicles, 2 Chronicles
    "1 chronicles": "1Ch",
    "1chronicles": "1Ch",
    "1ch": "1Ch",
    "first chronicles": "1Ch",
    "1st chronicles": "1Ch",
    "i chronicles": "1Ch",
    "2 chronicles": "2Ch",
    "2chronicles": "2Ch",
    "2ch": "2Ch",
    "second chronicles": "2Ch",
    "2nd chronicles": "2Ch",
    "ii chronicles": "2Ch",
    # Psalms
    "psalm": "Psa",
    "psalms": "Psa",
    "psa": "Psa",
    "ps": "Psa",
    # Matthew-John (Gospels)
    "matthew": "Mat",
    "mat": "Mat",
    "matt": "Mat",
    "mt": "Mat",
    "mark": "Mar",
    "mar": "Mar",
    "mk": "Mar",
    "luke": "Luk",
    "luk": "Luk",
    "lk": "Luk",
    "john": "Joh",
    "joh": "Joh",
    "jn": "Joh",
    # Romans
    "romans": "Rom",
    "rom": "Rom",
    "ro": "Rom",
    # 1 Corinthians, 2 Corinthians
    "1 corinthians": "1Co",
    "1corinthians": "1Co",
    "1co": "1Co",
    "1cor": "1Co",
    "first corinthians": "1Co",
    "1st corinthians": "1Co",
    "i corinthians": "1Co",
    "2 corinthians": "2Co",
    "2corinthians": "2Co",
    "2co": "2Co",
    "2cor": "2Co",
    "second corinthians": "2Co",
    "2nd corinthians": "2Co",
    "ii corinthians": "2Co",
    # Galatians-Colossians
    "galatians": "Gal",
    "gal": "Gal",
    "ephesians": "Eph",
    "eph": "Eph",
    "philippians": "Php",
    "php": "Php",
    "phil": "Php",
    "colossians": "Col",
    "col": "Col",
    # 1 Thessalonians, 2 Thessalonians
    "1 thessalonians": "1Th",
    "1thessalonians": "1Th",
    "1th": "1Th",
    "1thess": "1Th",
    "first thessalonians": "1Th",
    "1st thessalonians": "1Th",
    "i thessalonians": "1Th",
    "2 thessalonians": "2Th",
    "2thessalonians": "2Th",
    "2th": "2Th",
    "2thess": "2Th",
    "second thessalonians": "2Th",
    "2nd thessalonians": "2Th",
    "ii thessalonians": "2Th",
    # 1 Timothy, 2 Timothy
    "1 timothy": "1Ti",
    "1timothy": "1Ti",
    "1ti": "1Ti",
    "1tim": "1Ti",
    "first timothy": "1Ti",
    "1st timothy": "1Ti",
    "i timothy": "1Ti",
    "2 timothy": "2Ti",
    "2timothy": "2Ti",
    "2ti": "2Ti",
    "2tim": "2Ti",
    "second timothy": "2Ti",
    "2nd timothy": "2Ti",
    "ii timothy": "2Ti",
    # 1 Peter, 2 Peter
    "1 peter": "1Pe",
    "1peter": "1Pe",
    "1pe": "1Pe",
    "1pet": "1Pe",
    "first peter": "1Pe",
    "1st peter": "1Pe",
    "i peter": "1Pe",
    "2 peter": "2Pe",
    "2peter": "2Pe",
    "2pe": "2Pe",
    "2pet": "2Pe",
    "second peter": "2Pe",
    "2nd peter": "2Pe",
    "ii peter": "2Pe",
    # 1 John, 2 John, 3 John (DIFFERENT from Gospel of "John"!)
    "1 john": "1Jo",
    "1john": "1Jo",
    "1jo": "1Jo",
    "1jn": "1Jo",
    "first john": "1Jo",
    "1st john": "1Jo",
    "i john": "1Jo",
    "2 john": "2Jo",
    "2john": "2Jo",
    "2jo": "2Jo",
    "2jn": "2Jo",
    "second john": "2Jo",
    "2nd john": "2Jo",
    "ii john": "2Jo",
    "3 john": "3Jo",
    "3john": "3Jo",
    "3jo": "3Jo",
    "3jn": "3Jo",
    "third john": "3Jo",
    "3rd john": "3Jo",
    "iii john": "3Jo",
    # Revelation
    "revelation": "Rev",
    "rev": "Rev",
    "revelations": "Rev",
}

# Ordinal to number mapping for numbered books
ORDINAL_MAP = {
    "1st": "1",
    "first": "1",
    "i": "1",
    "2nd": "2",
    "second": "2",
    "ii": "2",
    "3rd": "3",
    "third": "3",
    "iii": "3",
}


def _normalize_book_name(book_raw: str) -> Optional[str]:
    """Normalize book name to standard abbreviation."""
    return BOOK_NORMALIZATION.get(book_raw.lower().strip())


def _extract_abbreviated_verbose(query: str) -> Optional[str]:
    """Extract: first/1st/i john chapter X verse Y.

    Examples:
        "first john chapter 3 verse 16" -> "1Jo 3:16"
        "second peter chapter 1 verse 3" -> "2Pe 1:3"
    """
    pattern = r"\b(1st|2nd|3rd|first|second|third|i|ii|iii)\s+([A-Za-z]+)\s+chapter\s+(\d+)\s+verse\s+(\d+)\b"
    match = re.search(pattern, query, re.IGNORECASE)

    if match:
        ordinal = match.group(1).lower()
        book_raw = match.group(2).lower()
        chapter, verse = match.group(3), match.group(4)

        number = ORDINAL_MAP.get(ordinal, "1")
        full_book = f"{number} {book_raw}"
        book = _normalize_book_name(full_book)

        if book:
            normalized_ref = f"{book} {chapter}:{verse}"
            logger.debug(
                "[pattern-ref] Abbrev-verbose: '%s' -> '%s'",
                match.group(0),
                normalized_ref,
            )
            return normalized_ref
    return None


def _extract_abbreviated_standard(query: str) -> Optional[str]:
    """Extract: 1st/first/i john 3:16.

    Examples:
        "1st John 3:16" -> "1Jo 3:16"
        "second corinthians 5:17" -> "2Co 5:17"
    """
    pattern = r"\b(1st|2nd|3rd|first|second|third|i|ii|iii)\s+([A-Za-z]+)\s+(\d+):(\d+)\b"
    match = re.search(pattern, query, re.IGNORECASE)

    if match:
        ordinal = match.group(1).lower()
        book_raw = match.group(2).lower()
        chapter, verse = match.group(3), match.group(4)

        number = ORDINAL_MAP.get(ordinal, "1")
        full_book = f"{number} {book_raw}"
        book = _normalize_book_name(full_book)

        if book:
            normalized_ref = f"{book} {chapter}:{verse}"
            logger.debug(
                "[pattern-ref] Abbrev-standard: '%s' -> '%s'",
                match.group(0),
                normalized_ref,
            )
            return normalized_ref
    return None


def _extract_verbose_format(query: str) -> Optional[str]:
    """Extract: Book chapter X verse Y.

    Examples:
        "Genesis chapter 3 verse 15" -> "Gen 3:15"
        "Romans chapter 8 verse 28" -> "Rom 8:28"
    """
    pattern = r"\b(\d?\s*[A-Za-z]+)\s+chapter\s+(\d+)\s+verse\s+(\d+)\b"
    match = re.search(pattern, query, re.IGNORECASE)

    if match:
        book_raw = match.group(1).strip().lower()
        chapter, verse = match.group(2), match.group(3)
        book = _normalize_book_name(book_raw)

        if book:
            normalized_ref = f"{book} {chapter}:{verse}"
            logger.debug(
                "[pattern-ref] Verbose: '%s' -> '%s'",
                match.group(0),
                normalized_ref,
            )
            return normalized_ref
    return None


def _extract_chapter_verse_format(query: str) -> Optional[str]:
    """Extract: Book Chapter verse Y.

    Examples:
        "John 3 verse 16" -> "Joh 3:16"
        "Romans 8 verse 28" -> "Rom 8:28"
    """
    pattern = r"\b(\d?\s*[A-Za-z]+)\s+(\d+)\s+verse\s+(\d+)\b"
    match = re.search(pattern, query, re.IGNORECASE)

    if match:
        book_raw = match.group(1).strip().lower()
        chapter, verse = match.group(2), match.group(3)
        book = _normalize_book_name(book_raw)

        if book:
            normalized_ref = f"{book} {chapter}:{verse}"
            logger.debug(
                "[pattern-ref] Chapter-verse: '%s' -> '%s'",
                match.group(0),
                normalized_ref,
            )
            return normalized_ref
    return None


def _extract_standard_format(query: str) -> Optional[str]:
    """Extract: Book Chapter:Verse (standard colon notation).

    Examples:
        "John 3:16" -> "Joh 3:16"
        "Gen. 3:15" -> "Gen 3:15" (handles period)
    """
    pattern = r"\b(\d?\s*[A-Za-z]+\.?)\s+(\d+):(\d+)\b"
    match = re.search(pattern, query, re.IGNORECASE)

    if match:
        book_raw = match.group(1).strip().rstrip(".").lower()
        chapter, verse = match.group(2), match.group(3)
        book = _normalize_book_name(book_raw)

        if book:
            normalized_ref = f"{book} {chapter}:{verse}"
            logger.debug(
                "[pattern-ref] Standard: '%s' -> '%s'",
                match.group(0),
                normalized_ref,
            )
            return normalized_ref
    return None


def extract_bible_reference(query: str) -> Optional[str]:
    """Extract Bible reference from query using comprehensive pattern matching.

    Tries multiple patterns in order of specificity:
    1. Abbreviated verbose: "first john chapter 3 verse 16"
    2. Abbreviated standard: "1st John 3:16"
    3. Verbose format: "Genesis chapter 3 verse 15"
    4. Chapter-verse format: "Romans 8 verse 28"
    5. Standard format: "John 3:16"

    Returns:
        Normalized reference string (e.g., "1Jo 3:16", "Gen 3:15") or None
    """
    # Order matters! Most specific patterns first to avoid false matches
    extractors = [
        _extract_abbreviated_verbose,
        _extract_abbreviated_standard,
        _extract_verbose_format,
        _extract_chapter_verse_format,
        _extract_standard_format,
    ]

    for extractor in extractors:
        result = extractor(query)
        if result:
            logger.info("[pattern-ref] Extracted: '%s'", result)
            return result

    logger.debug("[pattern-ref] No Bible reference detected in query")
    return None


def infer_intent_from_pattern(
    query: str, verse_data: Optional[dict] = None
) -> tuple[IntentType, float]:
    """Infer intent from query patterns and enriched verse metadata.

    Returns:
        (intent, confidence) tuple
    """
    query_lower = query.lower()
    bible_ref = extract_bible_reference(query)

    if bible_ref:
        # Bible reference queries - high confidence patterns

        if re.search(r"\b(summarize|summary|sum\s+up|overview)\b", query_lower):
            logger.info("[pattern-inference] Detected: summarize + Bible ref")
            return (IntentType.GET_PASSAGE_SUMMARY, 0.95)

        if re.search(r"\b(keywords?|key\s+words?|themes?|main\s+points?)\b", query_lower):
            logger.info("[pattern-inference] Detected: keywords + Bible ref")
            return (IntentType.GET_PASSAGE_KEYWORDS, 0.95)

        # Check for translation to target language (e.g., "translate John 3:16 into Spanish")
        # Requires: "translate" verb + target language preposition
        # Use "into" or "to" to avoid false positives with "in" (e.g., "challenges in John")
        if re.search(r"\btranslate\b", query_lower):
            # Look for target language pattern: "into Spanish", "to Indonesian"
            if re.search(r"\b(into|to)\s+[A-Z][a-z]+", query):
                logger.info("[pattern-inference] Detected: translate + target language")
                return (IntentType.TRANSLATE_SCRIPTURE, 0.90)

        # Check for translation help request (challenges, guidance, difficulties)
        if re.search(
            r"\b(translat(e|ion)|render|how\s+to|challenge|difficult|help)\b", query_lower
        ):
            if verse_data and verse_data.get("metadata", {}).get("has_translation_helps"):
                logger.info("[pattern-inference] Detected: translation + has TN data")
                return (IntentType.GET_TRANSLATION_HELPS, 0.98)
            else:
                logger.info("[pattern-inference] Detected: translation (no TN data)")
                return (IntentType.GET_TRANSLATION_HELPS, 0.85)

        if re.search(r"\b(explain|what|why|mean|understand|about|significance)\b", query_lower):
            if verse_data:
                bp_count = verse_data.get("metadata", {}).get("bibleproject_count", 0)
                if bp_count > 0:
                    logger.info("[pattern-inference] Detected: explain + %d BP links", bp_count)
                    return (IntentType.GET_BIBLE_TRANSLATION_ASSISTANCE, 0.95)
                else:
                    logger.info("[pattern-inference] Detected: explain (no BP links)")
                    return (IntentType.GET_BIBLE_TRANSLATION_ASSISTANCE, 0.80)
            else:
                logger.info("[pattern-inference] Detected: explain (no metadata)")
                return (IntentType.GET_BIBLE_TRANSLATION_ASSISTANCE, 0.75)

        # Default for Bible reference
        logger.info("[pattern-inference] Default: retrieve scripture")
        return (IntentType.RETRIEVE_SCRIPTURE, 0.85)

    # No Bible reference - general queries (lower confidence)
    if re.search(r"\b(what|who|why|how|explain|tell\s+me\s+about)\b", query_lower):
        logger.info("[pattern-inference] General question without Bible ref")
        return (IntentType.GET_BIBLE_TRANSLATION_ASSISTANCE, 0.60)

    # Very unclear - default but low confidence
    logger.info("[pattern-inference] Unclear intent, defaulting to general assistance")
    return (IntentType.GET_BIBLE_TRANSLATION_ASSISTANCE, 0.40)


def determine_intents_pattern_based(query: str) -> tuple[list[IntentType], float]:
    """Determine intents using pattern-based inference.

    Returns:
        (list of intents, confidence) tuple
    """
    bible_ref = extract_bible_reference(query)
    verse_data = None

    if bible_ref:
        try:
            from utils.enriched_bible_data import get_enriched_verse

            verse_data = get_enriched_verse(bible_ref)
            logger.info("[pattern-inference] Loaded enriched data for %s", bible_ref)
        except Exception as e:
            logger.warning("[pattern-inference] Could not load enriched data: %s", e)

    intent, confidence = infer_intent_from_pattern(query, verse_data)

    return ([intent], confidence)
