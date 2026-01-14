"""Bible reference detection and parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern

# Common Bible book names and abbreviations
BOOK_PATTERNS = {
    # Old Testament
    "Genesis": r"(?:Genesis|Gen|Ge|Gn)",
    "Exodus": r"(?:Exodus|Exod|Ex|Exo)",
    "Leviticus": r"(?:Leviticus|Lev|Le|Lv)",
    "Numbers": r"(?:Numbers|Num|Nu|Nm|Nb)",
    "Deuteronomy": r"(?:Deuteronomy|Deut|Dt)",
    "Joshua": r"(?:Joshua|Josh|Jos|Jsh)",
    "Judges": r"(?:Judges|Judg|Jdg|Jg|Jdgs)",
    "Ruth": r"(?:Ruth|Rth|Ru)",
    "1 Samuel": r"(?:1\s*Samuel|1\s*Sam|1\s*Sm|1\s*Sa|I\s*Samuel|I\s*Sam)",
    "2 Samuel": r"(?:2\s*Samuel|2\s*Sam|2\s*Sm|2\s*Sa|II\s*Samuel|II\s*Sam)",
    "1 Kings": r"(?:1\s*Kings|1\s*Kgs|1\s*Ki|I\s*Kings|I\s*Kgs)",
    "2 Kings": r"(?:2\s*Kings|2\s*Kgs|2\s*Ki|II\s*Kings|II\s*Kgs)",
    "1 Chronicles": r"(?:1\s*Chronicles|1\s*Chron|1\s*Chr|1\s*Ch|I\s*Chronicles|I\s*Chr)",
    "2 Chronicles": r"(?:2\s*Chronicles|2\s*Chron|2\s*Chr|2\s*Ch|II\s*Chronicles|II\s*Chr)",
    "Ezra": r"(?:Ezra|Ezr|Ez)",
    "Nehemiah": r"(?:Nehemiah|Neh|Ne)",
    "Esther": r"(?:Esther|Esth|Est|Es)",
    "Job": r"(?:Job|Jb)",
    "Psalms": r"(?:Psalms|Psalm|Ps|Pslm|Psa|Psm|Pss)",
    "Proverbs": r"(?:Proverbs|Prov|Pro|Prv|Pr)",
    "Ecclesiastes": r"(?:Ecclesiastes|Eccles|Eccle|Ecc|Ec|Qoh)",
    "Song of Solomon": r"(?:Song\s+of\s+Solomon|Song\s+of\s+Songs|Songs|Song|SOS|So|Canticle|Canticles)",
    "Isaiah": r"(?:Isaiah|Isa|Is)",
    "Jeremiah": r"(?:Jeremiah|Jer|Je|Jr)",
    "Lamentations": r"(?:Lamentations|Lam|La)",
    "Ezekiel": r"(?:Ezekiel|Ezek|Eze|Ezk)",
    "Daniel": r"(?:Daniel|Dan|Da|Dn)",
    "Hosea": r"(?:Hosea|Hos|Ho)",
    "Joel": r"(?:Joel|Jl)",
    "Amos": r"(?:Amos|Am)",
    "Obadiah": r"(?:Obadiah|Obad|Ob)",
    "Jonah": r"(?:Jonah|Jnh|Jon)",
    "Micah": r"(?:Micah|Mic|Mc)",
    "Nahum": r"(?:Nahum|Nah|Na)",
    "Habakkuk": r"(?:Habakkuk|Hab|Hb)",
    "Zephaniah": r"(?:Zephaniah|Zeph|Zep|Zp)",
    "Haggai": r"(?:Haggai|Hag|Hg)",
    "Zechariah": r"(?:Zechariah|Zech|Zec|Zc)",
    "Malachi": r"(?:Malachi|Mal|Ml)",
    # New Testament
    "Matthew": r"(?:Matthew|Matt|Mt)",
    "Mark": r"(?:Mark|Mrk|Mk|Mr)",
    "Luke": r"(?:Luke|Luk|Lk)",
    "John": r"(?:John|Jhn|Jn)",
    "Acts": r"(?:Acts|Act|Ac)",
    "Romans": r"(?:Romans|Rom|Ro|Rm)",
    "1 Corinthians": r"(?:1\s*Corinthians|1\s*Cor|1\s*Co|I\s*Corinthians|I\s*Cor)",
    "2 Corinthians": r"(?:2\s*Corinthians|2\s*Cor|2\s*Co|II\s*Corinthians|II\s*Cor)",
    "Galatians": r"(?:Galatians|Gal|Ga)",
    "Ephesians": r"(?:Ephesians|Eph|Ephes)",
    "Philippians": r"(?:Philippians|Phil|Php|Pp)",
    "Colossians": r"(?:Colossians|Col|Co)",
    "1 Thessalonians": r"(?:1\s*Thessalonians|1\s*Thess|1\s*Th|I\s*Thessalonians|I\s*Thess)",
    "2 Thessalonians": r"(?:2\s*Thessalonians|2\s*Thess|2\s*Th|II\s*Thessalonians|II\s*Thess)",
    "1 Timothy": r"(?:1\s*Timothy|1\s*Tim|1\s*Ti|I\s*Timothy|I\s*Tim)",
    "2 Timothy": r"(?:2\s*Timothy|2\s*Tim|2\s*Ti|II\s*Timothy|II\s*Tim)",
    "Titus": r"(?:Titus|Tit|Ti)",
    "Philemon": r"(?:Philemon|Phlm|Phm)",
    "Hebrews": r"(?:Hebrews|Heb|He)",
    "James": r"(?:James|Jas|Jm)",
    "1 Peter": r"(?:1\s*Peter|1\s*Pet|1\s*Pe|1\s*Pt|I\s*Peter|I\s*Pet)",
    "2 Peter": r"(?:2\s*Peter|2\s*Pet|2\s*Pe|2\s*Pt|II\s*Peter|II\s*Pet)",
    "1 John": r"(?:1\s*John|1\s*Jhn|1\s*Jn|I\s*John|I\s*Jhn)",
    "2 John": r"(?:2\s*John|2\s*Jhn|2\s*Jn|II\s*John|II\s*Jhn)",
    "3 John": r"(?:3\s*John|3\s*Jhn|3\s*Jn|III\s*John|III\s*Jhn)",
    "Jude": r"(?:Jude|Jud|Jd)",
    "Revelation": r"(?:Revelation|Rev|Re|The\s+Revelation)",
}


@dataclass
class BibleReference:
    """Parsed Bible reference."""

    book: str
    chapter: int | None = None
    verse_start: int | None = None
    verse_end: int | None = None
    raw_text: str = ""

    def __str__(self) -> str:
        """Format as readable reference."""
        if self.chapter is None:
            return self.book
        if self.verse_start is None:
            return f"{self.book} {self.chapter}"
        if self.verse_end is None:
            return f"{self.book} {self.chapter}:{self.verse_start}"
        return f"{self.book} {self.chapter}:{self.verse_start}-{self.verse_end}"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "book": self.book,
            "chapter": self.chapter,
            "verse_start": self.verse_start,
            "verse_end": self.verse_end,
            "raw_text": self.raw_text,
        }


class BibleReferenceDetector:
    """Detects and parses Bible references from text."""

    def __init__(self) -> None:
        """Initialize the detector with compiled patterns."""
        self._patterns: list[tuple[str, Pattern[str]]] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for all books."""
        for book_name, book_pattern in BOOK_PATTERNS.items():
            # Pattern: Book Chapter:Verse-Verse (e.g., "John 3:16-17")
            pattern = re.compile(
                rf"\b({book_pattern})\s+(\d+):(\d+)(?:-(\d+))?\b",
                re.IGNORECASE,
            )
            self._patterns.append((book_name, pattern))

            # Pattern: Book Chapter (e.g., "Romans 8")
            pattern = re.compile(
                rf"\b({book_pattern})\s+(\d+)\b(?!:)",
                re.IGNORECASE,
            )
            self._patterns.append((book_name, pattern))

    def extract_references(self, text: str) -> list[BibleReference]:
        """
        Extract all Bible references from text.

        Args:
            text: Text to search for references

        Returns:
            List of BibleReference objects found
        """
        references: list[BibleReference] = []
        seen_spans: set[tuple[int, int]] = set()

        for book_name, pattern in self._patterns:
            for match in pattern.finditer(text):
                span = match.span()
                # Skip if we've already found a reference at this position
                if span in seen_spans:
                    continue

                seen_spans.add(span)
                groups = match.groups()

                if len(groups) >= 3 and groups[2] is not None:
                    # Full reference with verse
                    ref = BibleReference(
                        book=book_name,
                        chapter=int(groups[1]),
                        verse_start=int(groups[2]),
                        verse_end=int(groups[3]) if len(groups) > 3 and groups[3] else None,
                        raw_text=match.group(0),
                    )
                elif len(groups) >= 2 and groups[1] is not None:
                    # Chapter only
                    ref = BibleReference(
                        book=book_name,
                        chapter=int(groups[1]),
                        raw_text=match.group(0),
                    )
                else:
                    continue

                references.append(ref)

        return references

    def extract_first_reference(self, text: str) -> BibleReference | None:
        """
        Extract the first Bible reference from text.

        Args:
            text: Text to search for reference

        Returns:
            First BibleReference found, or None
        """
        references = self.extract_references(text)
        return references[0] if references else None

    def has_reference(self, text: str) -> bool:
        """
        Check if text contains any Bible reference.

        Args:
            text: Text to check

        Returns:
            True if at least one reference found
        """
        return self.extract_first_reference(text) is not None


# Global instance for easy import
detector = BibleReferenceDetector()


def extract_bible_reference(text: str) -> BibleReference | None:
    """
    Convenience function to extract first Bible reference.

    Args:
        text: Text to search

    Returns:
        First BibleReference found, or None
    """
    return detector.extract_first_reference(text)


def extract_bible_references(text: str) -> list[BibleReference]:
    """
    Convenience function to extract all Bible references.

    Args:
        text: Text to search

    Returns:
        List of all BibleReferences found
    """
    return detector.extract_references(text)


__all__ = [
    "BibleReference",
    "BibleReferenceDetector",
    "extract_bible_reference",
    "extract_bible_references",
]
