# Design: Verse Cross-Linking Architecture

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Source Data](#source-data)
4. [Cross-Linking Process](#cross-linking-process)
5. [Output Data Structure](#output-data-structure)
6. [Usage Patterns](#usage-patterns)
7. [Building Blocks](#building-blocks)
8. [Performance Characteristics](#performance-characteristics)
9. [Maintenance and Updates](#maintenance-and-updates)

---

## Overview

The Verse Cross-Linking system creates **bi-directional references** between Bible verses and related resources, enabling:

- **Pattern-based intent inference** without LLM calls
- **Direct resource retrieval** without vector search
- **Comprehensive context** for response generation
- **Cost reduction** of 50-90% on intent classification

### Key Concept

Instead of searching for resources every time a user queries about a verse, we **pre-compute** all relationships and store them as enriched metadata on each verse.

```
Traditional Flow:
User asks about "Gen 3:15"
  → LLM classifies intent ($0.002)
  → Vector search for "Gen 3:15" resources (500ms)
  → Retrieve top-N results
  → Generate response

Cross-Linked Flow:
User asks about "Gen 3:15"
  → Extract reference (regex, 10ms)
  → Load enriched verse with metadata (50ms)
  → See: 112 BibleProject links, 4 translation notes, 2 TA articles
  → Infer intent from pattern + metadata (no LLM!)
  → Fetch linked resources directly (no vector search!)
  → Generate response
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOURCE DATA                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ BibleProject     │  │ Bible Text       │  │ Translation  │ │
│  │ Chunks           │  │ (BSB, TBI, etc.) │  │ Helps        │ │
│  │                  │  │                  │  │              │ │
│  │ • 494 chunks     │  │ • 93k verses     │  │ • 50k notes  │ │
│  │ • Metadata       │  │ • 3 languages    │  │ • Per verse  │ │
│  │ • Bible refs     │  │ • 3 translations │  │ • TA refs    │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                              ↓  Cross-Linking Process
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    REVERSE INDEX BUILDER                         │
│              (build_verse_resource_index.py)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: Parse BibleProject chunks                              │
│    • Extract bible_references from each chunk                   │
│    • Normalize references: "Genesis 3:15" → "gen 3:15"         │
│    • Build map: verse_key → [chunk_ids]                        │
│                                                                  │
│  Step 2: Parse Translation Helps                                │
│    • Index by verse reference                                   │
│    • Extract TA article references                              │
│    • Build map: verse_key → tn_data                            │
│                                                                  │
│  Step 3: Enrich Bible Verses                                    │
│    • For each verse in each translation:                        │
│      - Look up BibleProject chunks                              │
│      - Look up translation helps                                │
│      - Look up TA articles                                      │
│      - Calculate applicable intents                             │
│      - Calculate richness score                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                              ↓  Output
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ENRICHED BIBLE DATA                           │
│          (sources/bible_data_enriched/)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Each verse now includes:                                        │
│  • Original text                                                 │
│  • Original reference                                            │
│  • Cross-link metadata:                                          │
│    - BibleProject chunks (IDs, titles, contexts)                │
│    - Translation helps availability                              │
│    - TA articles list                                            │
│    - Applicable intents                                          │
│    - Richness score                                              │
│                                                                  │
│  Structure: <lang>/<translation>/<book>.json                     │
│  Example: en/bsb/gen.json                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                              ↓  Runtime Usage
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pattern-Based Intent Inference:                                │
│    User query → Extract reference → Load enriched verse         │
│      → Check metadata → Infer intent (no LLM!)                  │
│                                                                  │
│  Direct Resource Retrieval:                                     │
│    Intent + enriched verse → Fetch linked resources             │
│      → Skip vector search → Generate response                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Source Data

### 1. BibleProject Chunks

**Location:** `imports/tbp/chunks/all_chunks_for_embedding.json`

**Structure:**
```json
{
  "id": "tbp_00053",
  "text": "...promise given to Adam and Eve in Genesis 3:15...",
  "metadata": {
    "title": "04 Daniel Second Edition Transcript",
    "category": "Old Testament",
    "bible_references": [
      {
        "text": "Genesis 3:15",
        "book": "Genesis",
        "chapter": 3,
        "verse_start": 15,
        "context": "promise given to Adam and Eve in Genesis 3:15"
      }
    ]
  }
}
```

**Key Fields Used:**
- `id`: Unique chunk identifier (for linking)
- `metadata.title`: For display in enriched verse
- `metadata.bible_references[]`: Array of Bible references discussed in this chunk
- `metadata.bible_references[].text`: Reference string to parse
- `metadata.bible_references[].book`: Book name
- `metadata.bible_references[].chapter`: Chapter number
- `metadata.bible_references[].verse_start`: Starting verse
- `metadata.bible_references[].verse_end`: Ending verse (for ranges)
- `metadata.bible_references[].context`: Surrounding text

**Statistics:**
- 494 chunks processed
- 5,676 Bible references found
- Average: 11.5 references per chunk

---

### 2. Bible Text (Verses)

**Location:** `sources/bible_data/<lang>/<translation>/<book>.json`

**Languages & Translations:**
- `en/bsb/` - English (Berean Standard Bible) - 31,102 verses
- `fr/french_louis_segond_1910/` - French (Louis Segond 1910) - 31,103 verses
- `id/tbi/` - Indonesian (Terjemahan Baru Indonesia) - 31,123 verses

**Structure:**
```json
[
  {
    "reference": "Gen 1:1",
    "text": "In the beginning God created the heavens and the earth."
  },
  {
    "reference": "Gen 1:2",
    "text": "Now the earth was formless and void..."
  }
]
```

**Key Fields:**
- `reference`: Canonical reference (e.g., "Gen 3:15")
- `text`: Verse text in target language

**Statistics:**
- 93,328 total verses across all translations
- 66 books per translation
- Average: ~1,414 verses per book

---

### 3. Translation Helps

**Location:** `sources/translation_helps/<book>.json`

**Structure:**
```json
[
  {
    "reference": "Gen 1:1",
    "bsb_verse_text": "In the beginning God created...",
    "ult_verse_text": "In the beginning God created...",
    "notes": [
      {
        "support_reference": "rc://*/ta/man/translate/figs-abstractnouns",
        "orig_language_quote": "בְּרֵאשִׁית",
        "note": "The first chapter of Genesis is a true..."
      }
    ]
  }
]
```

**Key Fields:**
- `reference`: Verse reference
- `notes[]`: Array of translation notes
- `notes[].support_reference`: Link to TA article (if applicable)
- `notes[].orig_language_quote`: Original Hebrew/Greek text
- `notes[].note`: Translation note content

**Statistics:**
- 50,546 verses have translation helps (54.2% coverage)
- Average: 3-5 notes per verse
- 48,476 verses link to TA articles (51.9% coverage)

---

### 4. Translation Academy (TA) Articles

**Location:** `sources/ta_data/<category>/<article>.json`

**Structure:**
```json
{
  "title": "Assumed Knowledge and Implicit Information",
  "sub-title": "How can I be sure...",
  "text": "Assumed knowledge is whatever a speaker assumes...",
  "support_reference": "rc://*/ta/man/translate/figs-explicit"
}
```

**Key Fields:**
- `title`: Article title
- `text`: Full article content (Markdown)
- `support_reference`: Canonical reference for linking

**Categories:**
- `translate/` - Translation techniques (e.g., figs-metaphor, figs-explicit)
- `checking/` - Quality checking guidelines

**Usage:** TA articles are linked indirectly through translation helps' `support_reference` fields.

---

## Cross-Linking Process

### Step 1: Build BibleProject Index

**Goal:** Map each verse to all BibleProject chunks that discuss it.

**Algorithm:**
```python
def build_bibleproject_index():
    verse_to_chunks = defaultdict(list)
    
    # Load all BibleProject chunks
    chunks = load_json("imports/tbp/chunks/all_chunks_for_embedding.json")
    
    for chunk in chunks:
        chunk_id = chunk["id"]
        bible_refs = chunk["metadata"]["bible_references"]
        
        for ref in bible_refs:
            # Parse reference: "Genesis 3:15" → "gen 3:15"
            parsed = parse_reference(ref["text"])
            
            # Handle verse ranges
            if ref.has_range:
                for verse_num in range(ref.verse_start, ref.verse_end + 1):
                    key = f"{parsed.book} {parsed.chapter}:{verse_num}"
                    verse_to_chunks[key].append({
                        "chunk_id": chunk_id,
                        "title": chunk["metadata"]["title"],
                        "context": ref["context"][:100]
                    })
            else:
                key = f"{parsed.book} {parsed.chapter}:{parsed.verse}"
                verse_to_chunks[key].append(...)
            
            # Handle chapter-level references (e.g., "Genesis 3")
            if ref.is_chapter_ref:
                chapter_key = f"{parsed.book} {parsed.chapter}"
                verse_to_chunks[chapter_key].append(...)
    
    return verse_to_chunks
```

**Reference Normalization:**
- Book name aliases: "Genesis" → "gen", "Psalms" → "psa", "1 John" → "1jo"
- Case-insensitive matching
- Handles ranges: "Gen 3:14-16" creates 3 entries (one per verse)
- Handles chapter refs: "Genesis 3" applies to all verses in chapter

**Output Example:**
```python
{
  "gen 3:15": [
    {"chunk_id": "tbp_00053", "title": "Daniel", "context": "..."},
    {"chunk_id": "tbp_00054", "title": "Daniel", "context": "..."},
    # ... 112 total chunks
  ],
  "gen 3": [  # Chapter-level reference
    {"chunk_id": "tbp_00125", "title": "Chaos Dragon", "context": "..."},
  ]
}
```

---

### Step 2: Build Translation Helps Index

**Goal:** Map each verse to its translation notes and TA articles.

**Algorithm:**
```python
def build_translation_helps_index():
    verse_to_tn = {}
    
    # Load all translation helps books
    for book_file in glob("sources/translation_helps/*.json"):
        book_abbr = book_file.stem  # "gen", "exo", etc.
        helps = load_json(book_file)
        
        for help_entry in helps:
            ref = help_entry["reference"]  # "Gen 1:1"
            notes = help_entry["notes"]
            
            # Extract TA article references
            ta_refs = set()
            for note in notes:
                support_ref = note.get("support_reference", "")
                if support_ref.startswith("rc://"):
                    # Parse: "rc://*/ta/man/translate/figs-explicit"
                    # Extract: "translate/figs-explicit"
                    ta_stem = extract_ta_stem(support_ref)
                    ta_refs.add(ta_stem)
            
            verse_to_tn[ref] = {
                "has_helps": True,
                "note_count": len(notes),
                "ta_refs": sorted(list(ta_refs)),
                "book": book_abbr
            }
    
    return verse_to_tn
```

**Output Example:**
```python
{
  "Gen 1:1": {
    "has_helps": True,
    "note_count": 4,
    "ta_refs": ["translate/figs-abstractnouns"],
    "book": "gen"
  },
  "Gen 3:15": {
    "has_helps": True,
    "note_count": 4,
    "ta_refs": ["translate/figs-metaphor", "translate/figs-genericnoun"],
    "book": "gen"
  }
}
```

---

### Step 3: Enrich Bible Verses

**Goal:** Combine all cross-link data into enriched verse objects.

**Algorithm:**
```python
def enrich_verse_data(verse, bibleproject_index, translation_helps_index):
    ref = verse["reference"]  # "Gen 3:15"
    
    # Look up BibleProject chunks
    bp_chunks = bibleproject_index.get(ref, [])
    
    # Also check chapter-level references
    parsed = parse_reference(ref)
    chapter_key = f"{parsed.book} {parsed.chapter}"
    chapter_chunks = bibleproject_index.get(chapter_key, [])
    bp_chunks.extend(chapter_chunks)
    
    # Look up translation helps
    tn_data = translation_helps_index.get(ref, {})
    
    # Calculate flags
    has_bp = len(bp_chunks) > 0
    has_tn = tn_data.get("has_helps", False)
    has_ta = len(tn_data.get("ta_refs", [])) > 0
    
    # Determine applicable intents
    intents = ["retrieve-scripture", "get-passage-summary"]
    if has_bp:
        intents.append("get-bible-translation-assistance")
    if has_tn:
        intents.append("get-translation-helps")
    
    # Calculate richness score
    richness_score = (
        (0.4 if has_bp else 0) +
        (0.4 if has_tn else 0) +
        (0.2 if has_ta else 0)
    )
    
    # Build enriched verse
    return {
        "reference": ref,
        "text": verse["text"],
        "metadata": {
            "reference": ref,
            "bibleproject_chunks": [
                {
                    "chunk_id": chunk["chunk_id"],
                    "title": chunk["title"],
                    "context": chunk["context"]
                }
                for chunk in bp_chunks
            ],
            "bibleproject_count": len(bp_chunks),
            "has_translation_helps": has_tn,
            "translation_helps": {
                "note_count": tn_data.get("note_count", 0),
                "ta_articles": tn_data.get("ta_refs", [])
            } if has_tn else None,
            "ta_article_count": len(tn_data.get("ta_refs", [])),
            "applicable_intents": intents,
            "resource_summary": {
                "has_bibleproject": has_bp,
                "has_translation_notes": has_tn,
                "has_ta_articles": has_ta,
                "richness_score": richness_score
            }
        }
    }
```

**Richness Score Formula:**
- BibleProject links: 40% weight
- Translation helps: 40% weight
- TA articles: 20% weight
- Score range: 0.0 (no resources) to 1.0 (all resources)

---

## Output Data Structure

### Enriched Verse Object

**Full Example (Gen 3:15):**
```json
{
  "reference": "Gen 3:15",
  "text": "And I will put enmity between you and the woman, and between your seed and her seed. He will crush your head, and you will strike his heel."",
  "metadata": {
    "reference": "Gen 3:15",
    "bibleproject_chunks": [
      {
        "chunk_id": "tbp_00053",
        "title": "04 Daniel Second Edition Transcript",
        "context": "promise given to Adam and Eve in Genesis 3:15"
      },
      {
        "chunk_id": "tbp_00054",
        "title": "04 Daniel Second Edition Transcript",
        "context": "promise given to Adam and Eve in Genesis 3:15"
      }
      // ... 110 more chunks
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

### Metadata Fields Reference

| Field | Type | Description |
|-------|------|-------------|
| `reference` | string | Canonical verse reference |
| `bibleproject_chunks[]` | array | List of linked BibleProject chunks |
| `bibleproject_chunks[].chunk_id` | string | Chunk ID for fetching full content |
| `bibleproject_chunks[].title` | string | Chunk title for display |
| `bibleproject_chunks[].context` | string | Snippet showing how verse is mentioned |
| `bibleproject_count` | integer | Count of linked chunks |
| `has_translation_helps` | boolean | Whether translation helps exist |
| `translation_helps.note_count` | integer | Number of translation notes |
| `translation_helps.ta_articles[]` | array | List of TA article stems |
| `ta_article_count` | integer | Count of linked TA articles |
| `applicable_intents[]` | array | List of valid intent strings |
| `resource_summary.has_bibleproject` | boolean | BibleProject links exist |
| `resource_summary.has_translation_notes` | boolean | Translation notes exist |
| `resource_summary.has_ta_articles` | boolean | TA articles exist |
| `resource_summary.richness_score` | float | 0.0-1.0 composite score |

### Directory Structure

```
sources/bible_data_enriched/
├── index_summary.json              # Global statistics
├── en/                             # English
│   └── bsb/                       # Berean Standard Bible
│       ├── gen.json               # Genesis (50 verses)
│       ├── exo.json               # Exodus (1,213 verses)
│       ├── ...                    # All 66 books
│       └── rev.json               # Revelation (404 verses)
├── fr/                            # French
│   └── french_louis_segond_1910/
│       └── ...                    # All 66 books
└── id/                            # Indonesian
    └── tbi/                       # Terjemahan Baru Indonesia
        └── ...                    # All 66 books
```

---

## Usage Patterns

### 1. Pattern-Based Intent Inference

**Goal:** Classify user intent without LLM by using query patterns + enriched metadata.

**Algorithm:**
```python
def infer_intent(query: str) -> tuple[str, float]:
    # Step 1: Extract Bible reference
    bible_ref = extract_reference(query)  # "Gen 3:15"
    
    if not bible_ref:
        # No Bible reference - needs LLM fallback
        return ("get-bible-translation-assistance", 0.40)
    
    # Step 2: Load enriched verse
    verse = get_enriched_verse(bible_ref)
    
    # Step 3: Check query patterns
    query_lower = query.lower()
    
    # Pattern: Summarization
    if re.search(r'\b(summarize|summary)\b', query_lower):
        return ("get-passage-summary", 0.95)
    
    # Pattern: Keywords
    if re.search(r'\b(keywords?|themes?)\b', query_lower):
        return ("get-passage-keywords", 0.95)
    
    # Pattern: Translation help
    if re.search(r'\b(translat(e|ion)|challenge|help)\b', query_lower):
        if verse["metadata"]["has_translation_helps"]:
            return ("get-translation-helps", 0.98)  # High confidence
        else:
            return ("get-translation-helps", 0.80)  # Medium confidence
    
    # Pattern: Explanation
    if re.search(r'\b(explain|what|mean)\b', query_lower):
        bp_count = verse["metadata"]["bibleproject_count"]
        if bp_count > 0:
            return ("get-bible-translation-assistance", 0.95)
        else:
            return ("get-bible-translation-assistance", 0.75)
    
    # Default: retrieve scripture
    return ("retrieve-scripture", 0.85)
```

**Confidence Thresholds:**
- **≥0.85**: High confidence - skip LLM
- **0.65-0.84**: Medium confidence - skip LLM
- **<0.65**: Low confidence - use LLM fallback

**Example Results:**
```python
infer_intent("Summarize Genesis 3:15")
# → ("get-passage-summary", 0.95) - HIGH CONFIDENCE

infer_intent("Explain Genesis 3:15")
# → ("get-bible-translation-assistance", 0.95) - HIGH (has 112 BP links)

infer_intent("Translation challenges in John 3:16")
# → ("get-translation-helps", 0.98) - HIGH (has TN data)

infer_intent("What is the gospel?")
# → ("get-bible-translation-assistance", 0.40) - LOW (needs LLM)
```

---

### 2. Direct Resource Retrieval

**Goal:** Fetch all related resources without vector search.

**Traditional Flow (Vector Search):**
```python
def get_resources_traditional(query: str):
    # LLM intent classification
    intent = llm_classify_intent(query)  # $0.002, 800ms
    
    # Vector search
    results = vector_search(query, collection="bibleproject", n=5)  # 500ms
    
    return results[:5]  # Only top-5
```

**Cross-Linked Flow (Direct Lookup):**
```python
def get_resources_crosslinked(query: str):
    # Pattern-based intent (no LLM)
    bible_ref = extract_reference(query)  # 10ms
    intent, confidence = infer_intent(query)  # 20ms
    
    # Load enriched verse
    verse = get_enriched_verse(bible_ref)  # 50ms (cached)
    
    # Fetch ALL linked resources directly
    if intent == "get-bible-translation-assistance":
        chunk_ids = [c["chunk_id"] for c in verse["metadata"]["bibleproject_chunks"]]
        chunks = [get_chunk_by_id(cid) for cid in chunk_ids]  # 100ms
        return chunks  # ALL chunks, not just top-5
    
    elif intent == "get-translation-helps":
        tn_data = load_translation_helps(bible_ref)  # 30ms
        return tn_data
```

**Performance Comparison:**
| Metric | Traditional | Cross-Linked | Improvement |
|--------|-------------|--------------|-------------|
| LLM calls | 1 ($0.002) | 0 ($0) | -$0.002 (100%) |
| Vector searches | 1 (500ms) | 0 (0ms) | -500ms (100%) |
| Total latency | ~1300ms | ~180ms | -1120ms (86%) |
| Resources returned | Top-5 | All (avg 15) | 3x more |

---

### 3. Response Generation with Full Context

**Goal:** Provide LLM with ALL relevant resources for better responses.

**Traditional Approach:**
```python
def generate_response_traditional(query: str):
    # Get top-5 vector search results
    results = vector_search(query, n=5)
    
    context = "\n\n".join([r["text"] for r in results])
    
    prompt = f"""Answer this question: {query}
    
    Context (top 5 results):
    {context}
    """
    
    return llm_generate(prompt)
```

**Cross-Linked Approach:**
```python
def generate_response_crosslinked(query: str):
    bible_ref = extract_reference(query)
    verse = get_enriched_verse(bible_ref)
    
    # Gather ALL resources
    bp_chunks = [
        get_chunk_by_id(c["chunk_id"]) 
        for c in verse["metadata"]["bibleproject_chunks"]
    ]
    tn_data = load_translation_helps(bible_ref)
    ta_articles = [
        load_ta_article(article)
        for article in verse["metadata"]["translation_helps"]["ta_articles"]
    ]
    
    # Rich context with all resources
    prompt = f"""Answer this question: {query}
    
    Verse: {verse["text"]}
    
    BibleProject Insights ({len(bp_chunks)} sources):
    {format_bibleproject_chunks(bp_chunks)}
    
    Translation Notes:
    {format_translation_helps(tn_data)}
    
    Translation Academy Articles:
    {format_ta_articles(ta_articles)}
    """
    
    return llm_generate(prompt)
```

**Quality Improvements:**
- More comprehensive context (all resources vs top-5)
- Structured by resource type (BP vs TN vs TA)
- Better for disambiguation (multiple perspectives)
- Richer theological depth

---

## Building Blocks

### 1. Intent Inference Module

**Purpose:** Pattern-based intent classification without LLM.

**Components:**
```python
class PatternBasedIntentInference:
    def extract_bible_reference(query: str) -> str
    def infer_intent_from_pattern(query, verse_metadata) -> (intent, confidence)
    def classify_query(query: str) -> dict
```

**Integration Points:**
- `bt_servant_engine/services/brain_nodes.py::determine_intents()`
- Add pattern-based path before LLM fallback
- Track confidence scores for monitoring

**Example:**
```python
def determine_intents_hybrid(state: dict) -> dict:
    query = state["transformed_query"]
    
    # Try pattern-based first
    bible_ref = extract_bible_reference(query)
    if bible_ref:
        verse = get_enriched_verse(bible_ref)
        intent, confidence = infer_intent_from_pattern(query, verse)
        
        if confidence >= 0.70:
            # High confidence - skip LLM
            return {
                "intents": [intent],
                "intent_source": "pattern",
                "confidence": confidence
            }
    
    # Fallback to LLM for low confidence
    return determine_intents_llm(state)
```

---

### 2. Resource Loader Module

**Purpose:** Efficient loading of enriched verses and linked resources.

**Components:**
```python
# In utils/enriched_bible_data.py
@lru_cache(maxsize=128)
def load_enriched_book(lang, translation, book_stem) -> list[dict]

def get_enriched_verse(reference: str) -> dict
def get_bibleproject_links(verse_data: dict) -> list[dict]
def get_translation_helps_info(verse_data: dict) -> dict
def get_applicable_intents(verse_data: dict) -> list[str]
```

**Caching Strategy:**
- LRU cache at book level (not verse level)
- Cache 128 books (~2-4 MB memory per book)
- Hit rate typically >90% for sequential reading

---

### 3. Direct Resource Fetcher

**Purpose:** Fetch linked resources without vector search.

**Components:**
```python
def fetch_bibleproject_chunks(chunk_ids: list[str]) -> list[dict]:
    """Fetch BibleProject chunks by ID from ChromaDB."""
    collection = get_chroma_collection("bibleproject")
    return collection.get(ids=chunk_ids)

def fetch_translation_helps(verse_ref: str) -> dict:
    """Fetch translation helps directly from JSON."""
    book = extract_book(verse_ref)
    tn_data = load_json(f"sources/translation_helps/{book}.json")
    return find_verse_in_tn(tn_data, verse_ref)

def fetch_ta_article(article_stem: str) -> dict:
    """Fetch TA article by stem."""
    path = f"sources/ta_data/{article_stem}.json"
    return load_json(path)
```

**Integration:**
```python
def get_all_resources_for_verse(verse_ref: str) -> dict:
    verse = get_enriched_verse(verse_ref)
    
    chunk_ids = [c["chunk_id"] for c in verse["metadata"]["bibleproject_chunks"]]
    
    return {
        "verse_text": verse["text"],
        "bibleproject_chunks": fetch_bibleproject_chunks(chunk_ids),
        "translation_helps": fetch_translation_helps(verse_ref),
        "ta_articles": [
            fetch_ta_article(article)
            for article in verse["metadata"]["translation_helps"]["ta_articles"]
        ]
    }
```

---

### 4. Monitoring and Analytics

**Purpose:** Track intent inference performance and accuracy.

**Metrics to Track:**
```python
{
    "total_queries": 10000,
    "pattern_based_inferences": 8000,  # 80%
    "llm_fallbacks": 2000,             # 20%
    "average_confidence": 0.87,
    "intent_accuracy": 0.93,            # Compared to ground truth
    "cost_savings": "$16.00",           # Per month
    "latency_improvement": "860ms"      # Average
}
```

**Implementation:**
```python
class IntentInferenceMonitor:
    def log_inference(self, query, intent, confidence, source):
        """Log each intent inference for analytics."""
        pass
    
    def calculate_accuracy(self, predicted, actual):
        """Compare to ground truth for validation."""
        pass
    
    def generate_report(self):
        """Generate weekly performance report."""
        pass
```

---

### 5. Advanced Query Patterns

**Multi-Intent Queries:**
```python
# Query: "Summarize Genesis 3:15 and explain its significance"
# → Two intents: get-passage-summary + get-bible-translation-assistance

def infer_multiple_intents(query: str, verse: dict) -> list[tuple[str, float]]:
    intents = []
    
    if "summarize" in query.lower():
        intents.append(("get-passage-summary", 0.95))
    
    if "explain" in query.lower() or "significance" in query.lower():
        if verse["metadata"]["bibleproject_count"] > 0:
            intents.append(("get-bible-translation-assistance", 0.90))
    
    return intents
```

**Range Queries:**
```python
# Query: "Summarize Romans 8:28-39"
# → Load multiple verses, aggregate metadata

def handle_verse_range(query: str):
    bible_ref = extract_reference(query)  # "Rom 8:28-39"
    parsed = parse_range(bible_ref)
    
    verses = get_enriched_verses_for_range(
        book=parsed.book,
        chapter=parsed.chapter,
        verse_start=parsed.verse_start,
        verse_end=parsed.verse_end
    )
    
    # Aggregate metadata
    total_bp_chunks = sum(v["metadata"]["bibleproject_count"] for v in verses)
    has_any_tn = any(v["metadata"]["has_translation_helps"] for v in verses)
    
    return {
        "verses": verses,
        "aggregate_metadata": {
            "bibleproject_count": total_bp_chunks,
            "has_translation_helps": has_any_tn
        }
    }
```

---

## Performance Characteristics

### Build Time

**One-Time Index Build:**
- **Duration:** ~2 minutes on modern laptop
- **CPU:** Single-threaded (can be parallelized)
- **Memory:** ~500 MB peak
- **Disk I/O:** Read 9 MB (source), Write 45 MB (output)

**Breakdown:**
```
Step 1: Build BibleProject index     : 15 seconds
Step 2: Build Translation Helps index: 10 seconds
Step 3: Enrich Bible verses          : 90 seconds
Step 4: Write output files           : 10 seconds
Total                                : 125 seconds
```

---

### Runtime Performance

**Pattern-Based Intent Inference:**
```
Extract Bible reference : 10-20 ms  (regex)
Load enriched verse     : 50-100 ms (JSON read + parse, cached)
Pattern matching        : 5-10 ms   (regex checks)
Total                   : 65-130 ms
```

**Traditional LLM Approach:**
```
LLM API call           : 800-1200 ms
Total                  : 800-1200 ms

Improvement: 6-18x faster
```

**Direct Resource Retrieval:**
```
Load enriched verse     : 50 ms  (cached)
Fetch BibleProject chunks: 100 ms (ChromaDB get by ID)
Load translation helps  : 30 ms  (JSON read)
Total                   : 180 ms
```

**Traditional Vector Search:**
```
Vector search          : 500 ms  (ChromaDB query)
Total                  : 500 ms

Improvement: 2.8x faster
```

---

### Memory Usage

**Enriched Data Size:**
```
Original Bible data : 9 MB (93k verses)
Enriched Bible data : 45 MB (93k verses + metadata)
Overhead            : 36 MB (4x increase)

Per verse average   : 483 bytes (enriched vs 96 bytes original)
```

**Runtime Memory (with caching):**
```
Cache: 128 books × 700 KB avg = 90 MB
Process memory: ~150 MB total
```

---

### Cost Analysis

**Traditional Approach (10,000 queries/month):**
```
Intent classification: 10,000 × $0.002 = $20.00
Vector search        : Free (self-hosted ChromaDB)
Response generation  : 10,000 × $0.015 = $150.00
Total                : $170.00/month
```

**Cross-Linked Approach:**
```
Pattern-based (80%):  8,000 × $0.000 = $0.00
LLM fallback (20%):   2,000 × $0.002 = $4.00
Response generation : 10,000 × $0.015 = $150.00
Total               : $154.00/month

Monthly savings     : $16.00 (9.4%)
Annual savings      : $192.00
```

**If 90% have Bible refs:**
```
Pattern-based (90%):  9,000 × $0.000 = $0.00
LLM fallback (10%):   1,000 × $0.002 = $2.00
Response generation : 10,000 × $0.015 = $150.00
Total               : $152.00/month

Monthly savings     : $18.00 (10.6%)
Annual savings      : $216.00
```

---

## Maintenance and Updates

### When to Rebuild Index

**Required:**
- BibleProject content updates (new chunks added)
- Translation helps updates (new notes added)
- Bible translation updates (new versions added)

**Optional:**
- Algorithm improvements (better reference parsing)
- Metadata schema changes (new fields)

### Rebuild Process

```bash
# Full rebuild
python scripts/build_verse_resource_index.py

# Dry run (test without writing)
python scripts/build_verse_resource_index.py --dry-run --verbose

# Incremental update (if supported in future)
python scripts/build_verse_resource_index.py --incremental
```

### Validation

**After rebuild, verify:**
```bash
# Check statistics
cat sources/bible_data_enriched/index_summary.json

# Test random verses
python scripts/example_intent_inference_with_metadata.py

# Compare counts
echo "Expected: 93,328 verses"
find sources/bible_data_enriched -name "*.json" -exec jq '. | length' {} + | awk '{s+=$1} END {print "Actual: " s " verses"}'
```

---

## Building Blocks for Future Features

### 1. Semantic Router (Phase 3)

**Concept:** Route queries based on embedding similarity without LLM.

**Building on cross-linking:**
```python
# Pre-compute intent embeddings
intent_embeddings = {
    "get-passage-summary": embed("summarize Bible passage keywords"),
    "get-translation-helps": embed("translation challenges notes"),
    "get-bible-translation-assistance": embed("explain Bible verse meaning")
}

# At query time
query_embedding = embed(user_query)

# Find closest intent
closest_intent = max(
    intent_embeddings.items(),
    key=lambda x: cosine_similarity(query_embedding, x[1])
)

# Use enriched metadata to validate
verse = get_enriched_verse(extract_reference(user_query))
if closest_intent in verse["metadata"]["applicable_intents"]:
    return closest_intent  # High confidence
else:
    # Fallback to pattern-based or LLM
```

**Cost:** ~$0.0001 per query (embedding only)

---

### 2. Cross-Reference Network

**Concept:** Link verses that reference each other.

**Data source:** Parse cross-reference notes in study Bibles.

**Enrichment:**
```json
{
  "reference": "Gen 3:15",
  "metadata": {
    "cross_references": [
      {
        "reference": "Rom 16:20",
        "relationship": "fulfillment",
        "note": "Promise fulfilled in Christ"
      },
      {
        "reference": "Rev 12:9",
        "relationship": "imagery",
        "note": "Dragon defeated"
      }
    ]
  }
}
```

**Use cases:**
- "Show me related verses"
- "What other passages discuss this?"
- Thematic study chains

---

### 3. Topical Index

**Concept:** Group verses by theological topics/themes.

**Enrichment:**
```json
{
  "reference": "Gen 3:15",
  "metadata": {
    "topics": [
      "protoevangelium",
      "messianic_prophecy",
      "spiritual_warfare",
      "redemption"
    ],
    "themes": [
      "covenant",
      "promise",
      "enmity"
    ]
  }
}
```

**Use cases:**
- "Find all verses about covenant"
- "Show messianic prophecies"
- Topical sermon preparation

---

### 4. Progressive Enhancement

**Concept:** Incrementally enrich verses as new resources become available.

**Algorithm:**
```python
def update_enrichment_for_new_resource(resource_type, resource_data):
    """Update enriched verses when new resource added."""
    
    if resource_type == "bibleproject_chunk":
        # Extract Bible references from new chunk
        bible_refs = extract_references(resource_data)
        
        # Update affected verses
        for ref in bible_refs:
            verse = load_enriched_verse(ref)
            verse["metadata"]["bibleproject_chunks"].append({
                "chunk_id": resource_data["id"],
                "title": resource_data["title"],
                "context": extract_context(resource_data, ref)
            })
            save_enriched_verse(ref, verse)
```

---

### 5. Multi-Language Cross-Linking

**Concept:** Link verses across translations for comparative study.

**Enrichment:**
```json
{
  "reference": "Gen 3:15",
  "language": "en",
  "translation": "bsb",
  "metadata": {
    "parallel_verses": [
      {
        "language": "fr",
        "translation": "french_louis_segond_1910",
        "reference": "Gén 3:15",
        "text": "Je mettrai inimitié entre toi et la femme..."
      },
      {
        "language": "id",
        "translation": "tbi",
        "reference": "Kej 3:15",
        "text": "Aku akan mengadakan permusuhan..."
      }
    ]
  }
}
```

**Use cases:**
- Translation comparison
- Multi-language study
- Language learning

---

### 6. Caching Layer

**Concept:** Redis cache for frequently accessed verses.

**Architecture:**
```python
def get_enriched_verse_cached(reference: str) -> dict:
    # Try Redis first
    cached = redis.get(f"verse:{reference}")
    if cached:
        return json.loads(cached)
    
    # Fall back to file system
    verse = get_enriched_verse(reference)
    
    # Cache for 24 hours
    redis.setex(f"verse:{reference}", 86400, json.dumps(verse))
    
    return verse
```

**Benefits:**
- Sub-10ms lookup for hot verses
- Reduce disk I/O
- Support high-concurrency

---

### 7. API Endpoints

**Concept:** RESTful API for verse data and resources.

**Endpoints:**
```
GET /api/verse/{reference}
  → Returns enriched verse with metadata

GET /api/verse/{reference}/bibleproject
  → Returns linked BibleProject chunks

GET /api/verse/{reference}/translation-helps
  → Returns translation notes

GET /api/verse/{reference}/resources
  → Returns all resources in one call

POST /api/infer-intent
  Body: {"query": "Explain Genesis 3:15"}
  → Returns intent + confidence
```

---

## Conclusion

The verse cross-linking architecture provides a **foundation for cost-effective, high-performance Bible study features** by:

1. **Pre-computing relationships** between verses and resources
2. **Enabling pattern-based inference** without expensive LLM calls
3. **Supporting direct retrieval** without slow vector searches
4. **Providing rich metadata** for intelligent decision-making

**Key Success Metrics:**
- ✅ **93,328 verses** enriched with cross-links
- ✅ **23.6%** have BibleProject links (22,038 verses)
- ✅ **54.2%** have translation helps (50,546 verses)
- ✅ **50-90% cost reduction** potential
- ✅ **6-18x faster** intent inference
- ✅ **2.8x faster** resource retrieval

**Next Steps:**
1. Integrate pattern-based inference into production
2. Monitor accuracy and adjust confidence thresholds
3. Build additional features on top of enriched metadata
4. Explore advanced building blocks (semantic router, cross-refs, etc.)

This architecture positions the system for **scalable, cost-effective growth** while maintaining **high-quality responses**.