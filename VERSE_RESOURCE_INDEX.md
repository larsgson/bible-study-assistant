# Verse-to-Resource Reverse Index

## Overview

The verse resource index creates **bi-directional cross-links** between Bible verses and related resources:

- **Bible verses** → BibleProject chunks, Translation helps, TA articles
- **BibleProject chunks** → Bible verses they discuss (already existed)

This enables:
1. **Intent inference without LLM** - metadata tells what resources exist
2. **Direct resource lookup** - no vector search needed for 80%+ of queries
3. **Better response quality** - LLM gets ALL relevant resources upfront
4. **Cost reduction** - 50-90% savings on intent classification

## Statistics

- **Total verses indexed:** 93,328 (across 3 languages: en, fr, id)
- **Verses with BibleProject links:** 22,038 (23.6%)
- **Verses with Translation Helps:** 50,546 (54.2%)  
- **Verses with TA articles:** 48,476 (51.9%)
- **BibleProject chunks processed:** 494
- **Languages:** English (BSB), French (Louis Segond 1910), Indonesian (TBI)

## Usage

### 1. Build the Index

```bash
# Run once to create enriched Bible data
python scripts/build_verse_resource_index.py

# Output: sources/bible_data_enriched/<lang>/<translation>/<book>.json
```

### 2. Load Enriched Verses

```python
from utils.enriched_bible_data import get_enriched_verse, get_bibleproject_links

# Load verse with metadata
verse = get_enriched_verse("Gen 3:15")

print(verse["text"])
# "And I will put enmity between you and the woman..."

print(verse["metadata"]["bibleproject_count"])
# 112 (BibleProject chunks that discuss this verse)

print(verse["metadata"]["has_translation_helps"])
# True

print(verse["metadata"]["applicable_intents"])
# ['retrieve-scripture', 'get-passage-summary', 
#  'get-bible-translation-assistance', 'get-translation-helps']
```

### 3. Intent Inference Without LLM

```python
from scripts.example_intent_inference_with_metadata import PatternBasedIntentInference

classifier = PatternBasedIntentInference()
result = classifier.classify_query("Explain Genesis 3:15")

print(result["intent"])
# "get-bible-translation-assistance"

print(result["confidence"])
# 0.95 (95% confidence)

print(result["needs_llm_fallback"])
# False (no LLM needed!)
```

## Example: Enriched Verse Data

```json
{
  "reference": "Gen 3:15",
  "text": "And I will put enmity between you and the woman...",
  "metadata": {
    "reference": "Gen 3:15",
    "bibleproject_chunks": [
      {
        "chunk_id": "tbp_00053",
        "title": "04 Daniel Second Edition Transcript",
        "context": "promise given to Adam and Eve in Genesis 3:15..."
      }
      // ... 111 more chunks
    ],
    "bibleproject_count": 112,
    "has_translation_helps": true,
    "translation_helps": {
      "note_count": 4,
      "ta_articles": [
        "translate/figs-metaphor",
        "translate/figs-genericnoun"
      ]
    },
    "ta_article_count": 2,
    "applicable_intents": [
      "retrieve-scripture",
      "get-passage-summary",
      "get-bible-translation-assistance",
      "get-translation-helps"
    ],
    "resource_summary": {
      "has_bibleproject": true,
      "has_translation_notes": true,
      "has_ta_articles": true,
      "richness_score": 1.0
    }
  }
}
```

## Cost Savings Analysis

### Scenario: 13 Test Queries

**Current approach (LLM for all):**
- 13 queries × $0.002 = **$0.026**

**Pattern-based inference:**
- 7 queries × $0 (pattern-based) = $0
- 6 queries × $0.002 (LLM fallback) = $0.012
- **Total: $0.012**
- **Savings: $0.014 (53.8%)**

### Real-World Production (estimated)

Assuming **80% of queries have Bible references** (based on typical usage):

**10,000 queries/month:**
- Current: 10,000 × $0.002 = $20/month
- Pattern-based: 
  - 8,000 × $0 = $0 (Bible ref queries)
  - 2,000 × $0.002 = $4 (general queries)
  - **Total: $4/month**
- **Savings: $16/month (80%)**

## Files Created

```
sources/bible_data_enriched/
├── index_summary.json           # Statistics
├── en/
│   └── bsb/
│       ├── gen.json            # 50 enriched verses
│       ├── exo.json
│       └── ...                 # 66 books
├── fr/
│   └── french_louis_segond_1910/
│       └── ...
└── id/
    └── tbi/
        └── ...
```

## Scripts

1. **`scripts/build_verse_resource_index.py`**
   - Builds the reverse index
   - Run once, or when BibleProject content updates
   - Takes ~2 minutes to process 93k verses

2. **`scripts/example_intent_inference_with_metadata.py`**
   - Demonstrates pattern-based intent inference
   - Shows cost savings calculations
   - Test suite with 13 example queries

3. **`utils/enriched_bible_data.py`**
   - Helper functions for loading enriched data
   - Cached loading for performance
   - Resource summary extraction

## Next Steps

### Phase 2A: Integration with Brain Orchestrator

```python
# In bt_servant_engine/services/brain_nodes.py

def determine_intents_pattern_based(state: dict) -> dict:
    """Classify intents using patterns + enriched metadata (no LLM)."""
    query = state["transformed_query"]
    
    # Extract Bible reference
    bible_ref = extract_bible_reference(query)
    
    if bible_ref:
        # Load enriched verse
        verse = get_enriched_verse(bible_ref)
        
        # Pattern-based inference
        intent, confidence = infer_from_pattern_and_metadata(query, verse)
        
        if confidence >= 0.70:
            # High confidence - skip LLM
            return {"intents": [intent], "intent_source": "pattern"}
    
    # Fallback to LLM for low confidence
    return determine_intents_llm(state)
```

### Maintenance

**Rebuild index when:**
- BibleProject content updates
- New translation helps added
- New Bible translations added

```bash
# Rebuild
python scripts/build_verse_resource_index.py

# Dry run (test without writing)
python scripts/build_verse_resource_index.py --dry-run --verbose
```

## Benefits Summary

✅ **Cost:** 50-80% reduction in intent classification costs  
✅ **Speed:** 500-1000ms faster (no LLM round-trip)  
✅ **Quality:** Better responses (all resources available upfront)  
✅ **Coverage:** 93k verses across 3 languages  
✅ **Richness:** 23% of verses have BibleProject links, 54% have translation helps  

## Future Enhancements

1. **Cross-references**: Add verse-to-verse links (e.g., Gen 3:15 → Rom 16:20)
2. **Thematic linking**: Group verses by theological themes
3. **Progressive enrichment**: Update metadata as new resources added
4. **Caching layer**: Redis cache for frequently accessed verses
5. **API endpoint**: `/api/verse/{reference}/resources` for direct access

