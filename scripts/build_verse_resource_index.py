#!/usr/bin/env python3
"""
Build Verse-to-Resource Reverse Index

Creates bi-directional cross-links between Bible verses and resources:
- BibleProject chunks → verses they discuss
- Translation helps → verses they annotate
- TA articles → verses they apply to

Output: sources/bible_data_enriched/<lang>/<translation>/<book>.json
Each verse is enriched with metadata pointing to all related resources.

This enables:
1. Intent inference without LLM (metadata tells what resources exist)
2. Direct resource lookup (no vector search needed)
3. Better response generation (all context in one place)

Usage:
    python scripts/build_verse_resource_index.py [--dry-run] [--verbose]
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.bsb import BOOK_MAP

# Book name normalization mapping
BOOK_ALIASES = {
    "genesis": "gen",
    "exodus": "exo",
    "leviticus": "lev",
    "numbers": "num",
    "deuteronomy": "deu",
    "joshua": "jos",
    "judges": "jdg",
    "ruth": "rut",
    "1 samuel": "1sa",
    "2 samuel": "2sa",
    "1 kings": "1ki",
    "2 kings": "2ki",
    "1 chronicles": "1ch",
    "2 chronicles": "2ch",
    "ezra": "ezr",
    "nehemiah": "neh",
    "esther": "est",
    "job": "job",
    "psalm": "psa",
    "psalms": "psa",
    "proverbs": "pro",
    "ecclesiastes": "ecc",
    "song of solomon": "sos",
    "song of songs": "sos",
    "isaiah": "isa",
    "jeremiah": "jer",
    "lamentations": "lam",
    "ezekiel": "ezk",
    "daniel": "dan",
    "hosea": "hos",
    "joel": "joe",
    "amos": "amo",
    "obadiah": "oba",
    "jonah": "jon",
    "micah": "mic",
    "nahum": "nah",
    "habakkuk": "hab",
    "zephaniah": "zep",
    "haggai": "hag",
    "zechariah": "zec",
    "malachi": "mal",
    "matthew": "mat",
    "mark": "mar",
    "luke": "luk",
    "john": "joh",
    "acts": "act",
    "romans": "rom",
    "1 corinthians": "1co",
    "2 corinthians": "2co",
    "galatians": "gal",
    "ephesians": "eph",
    "philippians": "php",
    "colossians": "col",
    "1 thessalonians": "1th",
    "2 thessalonians": "2th",
    "1 timothy": "1ti",
    "2 timothy": "2ti",
    "titus": "tit",
    "philemon": "phm",
    "hebrews": "heb",
    "james": "jas",
    "1 peter": "1pe",
    "2 peter": "2pe",
    "1 john": "1jo",
    "2 john": "2jo",
    "3 john": "3jo",
    "jude": "jud",
    "revelation": "rev",
}


class VerseResourceIndexer:
    """Builds reverse index from verses to resources."""

    def __init__(self, verbose: bool = False, dry_run: bool = False):
        self.verbose = verbose
        self.dry_run = dry_run
        self.stats = {
            "total_verses": 0,
            "verses_with_bibleproject": 0,
            "verses_with_translation_helps": 0,
            "verses_with_ta_articles": 0,
            "bibleproject_chunks_processed": 0,
            "total_bible_refs_in_chunks": 0,
            "languages_processed": 0,
            "translations_processed": 0,
        }

    def log(self, message: str) -> None:
        """Log message if verbose mode enabled."""
        if self.verbose:
            print(f"[INFO] {message}")

    def normalize_book_name(self, book_name: str) -> str:
        """Normalize book name to standard abbreviation."""
        normalized = book_name.lower().strip()
        return BOOK_ALIASES.get(normalized, normalized)

    def parse_reference(self, ref_text: str) -> dict[str, Any] | None:
        """Parse Bible reference into components.

        Examples:
            "Gen 3:15" → {"book": "gen", "chapter": 3, "verse": 15}
            "Genesis 3:14-16" → {"book": "gen", "chapter": 3, "verse_start": 14, "verse_end": 16}
            "Psalm 119" → {"book": "psa", "chapter": 119}
        """
        # Pattern: Book Chapter:Verse or Book Chapter:Verse-Verse
        pattern = r"(\d?\s*[A-Za-z]+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?"
        match = re.search(pattern, ref_text)

        if not match:
            return None

        book_raw = match.group(1).strip()
        book = self.normalize_book_name(book_raw)
        chapter = int(match.group(2))
        verse_start = int(match.group(3)) if match.group(3) else None
        verse_end = int(match.group(4)) if match.group(4) else verse_start

        return {
            "book": book,
            "chapter": chapter,
            "verse_start": verse_start,
            "verse_end": verse_end,
        }

    def matches_reference(self, bp_ref: dict, verse_ref: str) -> bool:
        """Check if BibleProject reference matches a specific verse reference.

        Args:
            bp_ref: BibleProject reference dict with book, chapter, verse_start, verse_end
            verse_ref: Verse reference string like "Gen 3:15"

        Returns:
            True if bp_ref includes verse_ref
        """
        parsed = self.parse_reference(verse_ref)
        if not parsed:
            return False

        # Book must match
        if bp_ref.get("book") != parsed["book"]:
            return False

        # Chapter must match
        if bp_ref.get("chapter") != parsed["chapter"]:
            return False

        # If BP reference has no verse (whole chapter), it matches
        if bp_ref.get("verse_start") is None:
            return True

        # If verse reference has no verse number, shouldn't match
        if parsed["verse_start"] is None:
            return False

        # Check if verse is in range
        verse_num = parsed["verse_start"]
        bp_start = bp_ref["verse_start"]
        bp_end = bp_ref.get("verse_end", bp_start)

        return bp_start <= verse_num <= bp_end

    def build_bibleproject_index(self) -> dict[str, list[dict]]:
        """Build verse → BibleProject chunks mapping.

        Returns:
            dict mapping "Book C:V" → [{"chunk_id": ..., "context": ..., ...}]
        """
        self.log("Building BibleProject index...")
        chunks_file = project_root / "imports/tbp/chunks/all_chunks_for_embedding.json"

        if not chunks_file.exists():
            self.log(f"WARNING: BibleProject chunks not found at {chunks_file}")
            return {}

        with chunks_file.open(encoding="utf-8") as f:
            chunks = json.load(f)

        verse_to_chunks = defaultdict(list)

        for chunk in chunks:
            chunk_id = chunk.get("id")
            metadata = chunk.get("metadata", {})
            bible_refs = metadata.get("bible_references", [])

            if not bible_refs:
                continue

            self.stats["bibleproject_chunks_processed"] += 1

            for ref in bible_refs:
                self.stats["total_bible_refs_in_chunks"] += 1

                ref_text = ref.get("text", "")
                parsed = self.parse_reference(ref_text)

                if not parsed:
                    continue

                # Generate all verse keys that this reference covers
                book = parsed["book"]
                chapter = parsed["chapter"]
                verse_start = parsed.get("verse_start")
                verse_end = parsed.get("verse_end", verse_start)

                if verse_start is None:
                    # Whole chapter reference - we'll handle this at verse lookup time
                    # Store with a special marker
                    key = f"{book} {chapter}"
                    verse_to_chunks[key].append(
                        {
                            "chunk_id": chunk_id,
                            "title": metadata.get("title", ""),
                            "context": ref.get("context", "")[:100],
                            "type": metadata.get("type", ""),
                            "category": metadata.get("category", ""),
                            "is_chapter_ref": True,
                        }
                    )
                else:
                    # Specific verse(s)
                    for verse_num in range(verse_start, verse_end + 1):
                        key = f"{book} {chapter}:{verse_num}"
                        verse_to_chunks[key].append(
                            {
                                "chunk_id": chunk_id,
                                "title": metadata.get("title", ""),
                                "context": ref.get("context", "")[:100],
                                "type": metadata.get("type", ""),
                                "category": metadata.get("category", ""),
                                "is_chapter_ref": False,
                            }
                        )

        self.log(f"  Found {len(verse_to_chunks)} verse keys with BibleProject links")
        return dict(verse_to_chunks)

    def build_translation_helps_index(self) -> dict[str, dict]:
        """Build verse → translation helps mapping.

        Returns:
            dict mapping "Book C:V" → {"has_helps": True, "note_count": N, "ta_refs": [...]}
        """
        self.log("Building Translation Helps index...")
        tn_dir = project_root / "sources/translation_helps"

        if not tn_dir.exists():
            self.log(f"WARNING: Translation helps not found at {tn_dir}")
            return {}

        verse_to_tn = {}

        for tn_file in tn_dir.glob("*.json"):
            book_abbr = tn_file.stem

            with tn_file.open(encoding="utf-8") as f:
                helps = json.load(f)

            for help_entry in helps:
                ref = help_entry.get("reference", "")
                notes = help_entry.get("notes", [])

                # Extract TA article references
                ta_refs = set()
                for note in notes:
                    support_ref = note.get("support_reference", "")
                    if support_ref.startswith("rc://"):
                        # Extract stem like "translate/figs-explicit"
                        parts = support_ref.split("/")
                        if len(parts) >= 5:
                            ta_stem = f"{parts[3]}/{parts[4]}"
                            ta_refs.add(ta_stem)

                verse_to_tn[ref] = {
                    "has_helps": True,
                    "note_count": len(notes),
                    "ta_refs": sorted(list(ta_refs)),
                    "book": book_abbr,
                }

        self.log(f"  Found {len(verse_to_tn)} verses with translation helps")
        return verse_to_tn

    def determine_applicable_intents(self, has_bp: bool, has_tn: bool, has_ta: bool) -> list[str]:
        """Determine which intents are applicable based on available resources."""
        intents = [
            "retrieve-scripture",
            "get-passage-summary",
        ]

        if has_bp:
            intents.append("get-bible-translation-assistance")

        if has_tn:
            intents.append("get-translation-helps")

        return intents

    def enrich_verse_data(
        self,
        verse: dict,
        bibleproject_index: dict,
        translation_helps_index: dict,
    ) -> dict:
        """Enrich a single verse with cross-link metadata."""
        ref = verse.get("reference", "")

        # Look up BibleProject chunks
        bp_chunks = bibleproject_index.get(ref, [])

        # Also check chapter-level references
        parsed = self.parse_reference(ref)
        if parsed and parsed.get("verse_start"):
            chapter_key = f"{parsed['book']} {parsed['chapter']}"
            chapter_chunks = bibleproject_index.get(chapter_key, [])
            bp_chunks.extend(chapter_chunks)

        # Look up translation helps
        tn_data = translation_helps_index.get(ref, {})

        # Build enriched metadata
        has_bp = len(bp_chunks) > 0
        has_tn = tn_data.get("has_helps", False)
        has_ta = len(tn_data.get("ta_refs", [])) > 0

        if has_bp:
            self.stats["verses_with_bibleproject"] += 1
        if has_tn:
            self.stats["verses_with_translation_helps"] += 1
        if has_ta:
            self.stats["verses_with_ta_articles"] += 1

        enriched = {
            **verse,
            "metadata": {
                "reference": ref,
                "bibleproject_chunks": [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "title": chunk["title"],
                        "context": chunk["context"],
                    }
                    for chunk in bp_chunks
                ],
                "bibleproject_count": len(bp_chunks),
                "has_translation_helps": has_tn,
                "translation_helps": {
                    "note_count": tn_data.get("note_count", 0),
                    "ta_articles": tn_data.get("ta_refs", []),
                }
                if has_tn
                else None,
                "ta_article_count": len(tn_data.get("ta_refs", [])),
                "applicable_intents": self.determine_applicable_intents(has_bp, has_tn, has_ta),
                "resource_summary": {
                    "has_bibleproject": has_bp,
                    "has_translation_notes": has_tn,
                    "has_ta_articles": has_ta,
                    "richness_score": (
                        (0.4 if has_bp else 0) + (0.4 if has_tn else 0) + (0.2 if has_ta else 0)
                    ),
                },
            },
        }

        self.stats["total_verses"] += 1
        return enriched

    def process_bible_data(
        self,
        bibleproject_index: dict,
        translation_helps_index: dict,
    ) -> None:
        """Process all Bible data and enrich with cross-links."""
        bible_data_dir = project_root / "sources/bible_data"

        if not bible_data_dir.exists():
            self.log(f"ERROR: Bible data not found at {bible_data_dir}")
            return

        output_dir = project_root / "sources/bible_data_enriched"

        for lang_dir in bible_data_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            lang = lang_dir.name
            self.log(f"Processing language: {lang}")
            self.stats["languages_processed"] += 1

            for translation_dir in lang_dir.iterdir():
                if not translation_dir.is_dir():
                    continue

                translation = translation_dir.name
                self.log(f"  Processing translation: {translation}")
                self.stats["translations_processed"] += 1

                # Create output directory
                out_dir = output_dir / lang / translation
                if not self.dry_run:
                    out_dir.mkdir(parents=True, exist_ok=True)

                # Process each book
                for book_file in translation_dir.glob("*.json"):
                    book_abbr = book_file.stem

                    # Skip non-book files
                    if book_abbr.startswith("_"):
                        continue

                    self.log(f"    Processing book: {book_abbr}")

                    with book_file.open(encoding="utf-8") as f:
                        verses = json.load(f)

                    # Validate data format
                    if not isinstance(verses, list):
                        self.log(f"      WARNING: Skipping {book_abbr} - not a list")
                        continue

                    # Enrich each verse
                    enriched_verses = []
                    for verse in verses:
                        # Validate verse format
                        if not isinstance(verse, dict) or "reference" not in verse:
                            continue

                        enriched = self.enrich_verse_data(
                            verse, bibleproject_index, translation_helps_index
                        )
                        enriched_verses.append(enriched)

                    # Write enriched data
                    if not self.dry_run:
                        output_file = out_dir / f"{book_abbr}.json"
                        with output_file.open("w", encoding="utf-8") as f:
                            json.dump(enriched_verses, f, indent=2, ensure_ascii=False)

                        self.log(
                            f"      Wrote {len(enriched_verses)} enriched verses to {output_file}"
                        )

    def write_index_summary(self) -> None:
        """Write summary statistics to index_summary.json."""
        if self.dry_run:
            return

        output_dir = project_root / "sources/bible_data_enriched"
        summary_file = output_dir / "index_summary.json"

        summary = {
            "statistics": self.stats,
            "percentages": {
                "verses_with_bibleproject_pct": (
                    round(
                        100 * self.stats["verses_with_bibleproject"] / self.stats["total_verses"], 2
                    )
                    if self.stats["total_verses"] > 0
                    else 0
                ),
                "verses_with_translation_helps_pct": (
                    round(
                        100
                        * self.stats["verses_with_translation_helps"]
                        / self.stats["total_verses"],
                        2,
                    )
                    if self.stats["total_verses"] > 0
                    else 0
                ),
                "verses_with_ta_articles_pct": (
                    round(
                        100 * self.stats["verses_with_ta_articles"] / self.stats["total_verses"], 2
                    )
                    if self.stats["total_verses"] > 0
                    else 0
                ),
            },
        }

        with summary_file.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        self.log(f"Wrote summary to {summary_file}")

    def print_statistics(self) -> None:
        """Print indexing statistics."""
        print("\n" + "=" * 70)
        print("Verse-to-Resource Index Statistics")
        print("=" * 70)
        print(f"Total verses processed: {self.stats['total_verses']:,}")
        print(f"Languages processed: {self.stats['languages_processed']}")
        print(f"Translations processed: {self.stats['translations_processed']}")
        print()
        print("Cross-Link Coverage:")
        print(
            f"  Verses with BibleProject links: {self.stats['verses_with_bibleproject']:,} "
            f"({100 * self.stats['verses_with_bibleproject'] / max(1, self.stats['total_verses']):.1f}%)"
        )
        print(
            f"  Verses with Translation Helps: {self.stats['verses_with_translation_helps']:,} "
            f"({100 * self.stats['verses_with_translation_helps'] / max(1, self.stats['total_verses']):.1f}%)"
        )
        print(
            f"  Verses with TA Articles: {self.stats['verses_with_ta_articles']:,} "
            f"({100 * self.stats['verses_with_ta_articles'] / max(1, self.stats['total_verses']):.1f}%)"
        )
        print()
        print("BibleProject Index:")
        print(f"  Chunks processed: {self.stats['bibleproject_chunks_processed']:,}")
        print(f"  Bible references found: {self.stats['total_bible_refs_in_chunks']:,}")
        print("=" * 70 + "\n")

    def run(self) -> None:
        """Main execution flow."""
        print("Building verse-to-resource reverse index...")
        print()

        # Step 1: Build BibleProject index
        bibleproject_index = self.build_bibleproject_index()

        # Step 2: Build Translation Helps index
        translation_helps_index = self.build_translation_helps_index()

        # Step 3: Process and enrich all Bible data
        self.process_bible_data(bibleproject_index, translation_helps_index)

        # Step 4: Write summary
        self.write_index_summary()

        # Step 5: Print statistics
        self.print_statistics()

        if self.dry_run:
            print("[DRY RUN] No files were written.")
        else:
            print(
                f"✓ Enriched Bible data written to: {project_root / 'sources/bible_data_enriched'}"
            )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build verse-to-resource reverse index for bi-directional cross-linking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing output files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    try:
        indexer = VerseResourceIndexer(verbose=args.verbose, dry_run=args.dry_run)
        indexer.run()
    except KeyboardInterrupt:
        print("\n\nIndexing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
