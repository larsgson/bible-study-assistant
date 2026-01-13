# Quick Start: Verse Resource Index

## Build Index (One Time)

```bash
python scripts/build_verse_resource_index.py
```

**Time:** ~2 minutes  
**Output:** 93,328 enriched verses in `sources/bible_data_enriched/`

## Test It

```bash
python scripts/example_intent_inference_with_metadata.py
```

**Expected result:** 53.8% cost savings on 13 test queries

## Use in Code

```python
from utils.enriched_bible_data import get_enriched_verse

verse = get_enriched_verse("Gen 3:15")
print(f"BibleProject links: {verse['metadata']['bibleproject_count']}")
print(f"Has translation helps: {verse['metadata']['has_translation_helps']}")
print(f"Applicable intents: {verse['metadata']['applicable_intents']}")
```

## Key Stats

- **93,328** verses indexed
- **23.6%** have BibleProject links  
- **54.2%** have translation helps
- **50-80%** cost reduction potential

## What This Enables

✅ Intent inference without LLM (for 80% of queries with Bible refs)  
✅ Direct resource lookup (no vector search needed)  
✅ Better responses (all context in one place)  
✅ Faster queries (500-1000ms saved per query)

## See Full Docs

Read `VERSE_RESOURCE_INDEX.md` for complete documentation.
