# BibleProject Resources - Complete Extraction Pipeline

This directory contains BibleProject PDF resources and their extracted metadata, organized for integration into the Bible Study Assistant RAG system.

## 📁 Directory Structure

```
imports/tbp/
├── config/
│   └── tbp.json                    # Categorization rules and path redirections
│
├── metadata/
│   └── download-manifest.json      # Download tracking with URLs and MD5 hashes
│
├── files/                          # Source PDFs (192 files, 95 MB)
│   ├── Script-References/          # Video script references (110 files)
│   │   ├── The-Covenants_Script-References.pdf
│   │   ├── Sermon-on-the-Mount/
│   │   └── word_studies/
│   ├── Study-Notes/                # Detailed study guides (49 files)
│   ├── Deuterocanon-Apocrypha/     # Deuterocanonical resources (10 files)
│   ├── Insight-Videos/             # Hebrew/Greek word studies (9 files)
│   ├── The-Wilderness/             # Theme resources (2 files)
│   ├── Redemption/                 # Theme resources (2 files)
│   ├── The-Exodus-Way/             # Theme resources (2 files)
│   ├── The-Mountain/               # Theme resources (2 files)
│   ├── advent/                     # Advent season resources (4 files)
│   └── Root/                       # Miscellaneous (2 files)
│
├── extracted/                      # Metadata JSON (192 files, 13 MB)
│   ├── Script-References/          # Mirrors files/ structure
│   │   ├── The-Covenants_Script-References.json
│   │   ├── Sermon-on-the-Mount/
│   │   └── word_studies/
│   ├── Study-Notes/
│   ├── ... (mirrors files/ completely)
│   └── extraction_summary.json
│
└── chunks/                         # Chunked for embedding (2,380 chunks, 19 MB)
    ├── by_strategy/
    │   ├── timestamp_chunks.json        # 682 chunks (video navigation)
    │   ├── bible_reference_chunks.json  # 857 chunks (scripture search)
    │   └── semantic_chunks.json         # 841 chunks (general search)
    ├── all_chunks_for_embedding.json    # Master file (2,380 chunks)
    └── chunking_summary.json
```

## 🔄 Complete Pipeline

### Step 0: Download PDFs

```bash
python scripts/scrape_tbp_pdfs.py
```

**What it does:**
- Downloads PDFs from bibleproject.com/downloads/
- Mirrors CloudFront folder structure
- Applies path redirections from config
- Generates download-manifest.json with MD5 deduplication

**Output:**
- `files/` - 192 PDFs in mirrored structure
- `metadata/download-manifest.json` - Download tracking

### Step 1: Extract Metadata

```bash
python scripts/extract_tbp_step1_metadata.py
```

**What it does:**
- Extracts text from all PDFs with page-by-page structure
- Detects 12,555 Bible references (book, chapter, verse, context)
- Preserves video timestamps from 137 documents
- Creates mirrored JSON structure

**Output:**
- `extracted/{folder}/{file}.json` - One metadata file per PDF
- `extracted/extraction_summary.json` - Statistics

**Metadata includes:**
- Full text with page breaks
- Bible references with context and positions
- Video timestamps with start/end times
- Content statistics
- Original URLs

### Step 2: Create Intelligent Chunks

```bash
python scripts/extract_tbp_step2_chunking.py
```

**What it does:**
- Reads metadata from extracted/
- Creates 3 chunking strategies simultaneously
- Generates embedding-ready chunks with rich metadata

**Output:**
- `chunks/by_strategy/timestamp_chunks.json` - 682 chunks
- `chunks/by_strategy/bible_reference_chunks.json` - 857 chunks
- `chunks/by_strategy/semantic_chunks.json` - 841 chunks
- `chunks/all_chunks_for_embedding.json` - 2,380 total chunks

### Step 3: Ingest to ChromaDB

```bash
# Dry run first to verify
python scripts/extract_tbp_step3_ingest.py --dry-run

# Actual ingestion
python scripts/extract_tbp_step3_ingest.py
```

**What it does:**
- Reads chunks from `all_chunks_for_embedding.json`
- Creates or updates ChromaDB collection "bibleproject"
- Generates embeddings using OpenAI text-embedding-ada-002
- Ingests in batches with proper metadata flattening
- Tracks progress by strategy

**Output:**
- ChromaDB collection "bibleproject" with 1,100+ documents
- Searchable embeddings with rich metadata
- Ready for semantic search and RAG queries

**Options:**
```bash
# Use custom collection name
python scripts/extract_tbp_step3_ingest.py --collection-name custom_name

# Adjust batch size
python scripts/extract_tbp_step3_ingest.py --batch-size 50

# List existing collections
python scripts/extract_tbp_step3_ingest.py --list-collections
```

### Query and Test ChromaDB

```bash
# Show collection statistics
python scripts/query_tbp_chromadb.py --stats

# Run example queries
python scripts/query_tbp_chromadb.py --examples

# Custom query
python scripts/query_tbp_chromadb.py --query "What is wisdom?" --n-results 5

# Filter by strategy
python scripts/query_tbp_chromadb.py --query "Holy Spirit" --strategy timestamp

# Browse sample documents
python scripts/query_tbp_chromadb.py --browse 10

# Get specific document
python scripts/query_tbp_chromadb.py --doc-id tbp_00042
```

## 📊 Statistics

| Metric | Count |
|--------|-------|
| Total PDFs | 192 |
| Total Pages | 1,410 |
| Total Words | ~486,000 |
| Documents with Timestamps | 137 (71%) |
| Documents with Bible References | 166 (86%) |
| **Total Bible References Found** | **12,555** |
| **Total Chunks Created** | **2,380** |

### By Category
- Script-References: 110 docs, 224 semantic chunks, 3,592 Bible refs
- Study-Notes: 49 docs, 534 semantic chunks, 8,475 Bible refs
- Deuterocanon-Apocrypha: 10 docs, 28 semantic chunks, 9 Bible refs
- Insight-Videos: 9 docs, 9 semantic chunks, 1 Bible ref
- Theme Resources: 14 docs, 46 semantic chunks, 831 Bible refs

### Chunking Strategies

**Strategy A: Timestamp-Based (682 chunks)**
- Purpose: Video navigation and temporal search
- Aligns with video timestamps for direct linking
- Each chunk represents a video segment
- Includes all Bible references within that time segment

**Strategy B: Bible Reference-Based (857 chunks)**
- Purpose: Scripture-focused search and cross-referencing
- Chunks centered around clusters of Bible references
- Enables searching by specific passages (e.g., "Genesis 1:28")
- Variable size (200-1200 words) based on reference density

**Strategy C: Semantic Fixed-Size (841 chunks)**
- Purpose: General thematic search
- 800 words per chunk with 150-word overlap
- Consistent size for predictable embeddings
- Includes all Bible references and timestamps within chunk

## 📄 Data Schemas

### Metadata JSON (Step 1 Output)

Each file in `extracted/` contains:

```json
{
  "file_info": {
    "filename": "The-Covenants_Script-References.pdf",
    "title": "The Covenants",
    "category": "Script-References",
    "type": "Script-References",
    "series": "Script-References",
    "folder_path": "Script-References",
    "original_url": "https://d1bsmz3sdihplr.cloudfront.net/..."
  },
  "content_stats": {
    "pages": 3,
    "word_count": 1205,
    "char_count": 6648
  },
  "features": {
    "has_timestamps": true,
    "timestamp_count": 6,
    "has_bible_refs": true,
    "bible_ref_count": 71
  },
  "bible_references": [
    {
      "text": "Genesis 2:19",
      "position": 1664,
      "book": "Genesis",
      "chapter": 2,
      "verse_start": 19,
      "context": "partnership with everybody else...",
      "page": 1
    }
  ],
  "timestamps": [
    {
      "start": "00:00",
      "end": "01:40",
      "start_seconds": 0,
      "end_seconds": 100,
      "position": 1687,
      "page": 1
    }
  ],
  "pages": [
    {
      "page": 1,
      "text": "Full page text...",
      "word_count": 318,
      "bible_references": [...],
      "timestamps": [...]
    }
  ],
  "full_text": "Complete document text..."
}
```

### Chunk JSON (Step 2 Output)

Each chunk in `chunks/` contains:

```json
{
  "id": "tbp_00000",
  "strategy": "timestamp|bible_reference|semantic",
  "strategy_id": "tbp_tim_00000",
  "text": "[Title] Chunk content with 800 words...",
  "metadata": {
    "source": "bibleproject",
    "category": "Script-References",
    "title": "The Covenants",
    "type": "Script-References",
    "series": "Script-References",
    "filename": "The-Covenants_Script-References.pdf",
    "original_url": "https://...",
    "word_count": 800,
    "page_count": 3,
    
    // Strategy-specific fields
    // For timestamp chunks:
    "start_time": "00:00",
    "end_time": "01:40",
    "video_timestamp": 0,
    "duration_seconds": 100,
    
    // For bible_reference chunks:
    "primary_reference": "Genesis 1:28-29",
    "primary_book": "Genesis",
    "primary_chapter": 1,
    "primary_verse": 28,
    "all_references": ["Genesis 1:28-29", "Genesis 2:15"],
    
    // For semantic chunks:
    "chunk_index": 0,
    "overlap_words": 150,
    
    // Common fields:
    "bible_references": [...],
    "has_bible_refs": true,
    "has_timestamp": true
  }
}
```

## 🎯 Use Cases

### 1. Video Navigation
**Query:** "What does BibleProject say about covenants at 1:30 in the video?"

**Strategy:** Search `timestamp_chunks.json`
- Filter: `start_seconds <= 90 <= end_seconds`
- Result: Direct link to video timestamp with content

### 2. Scripture Cross-Reference
**Query:** "Show me all BibleProject content about Genesis 1:28"

**Strategy:** Search `bible_reference_chunks.json`
- Filter: `primary_book == "Genesis" AND primary_chapter == 1`
- Result: All content discussing that specific passage

### 3. Thematic Search
**Query:** "What is holiness according to BibleProject?"

**Strategy:** Search `semantic_chunks.json`
- Semantic similarity search
- Result: Comprehensive thematic understanding

### 4. Comprehensive Search
**Query:** "Tell me about the Exodus theme"

**Strategy:** Search ALL strategies, deduplicate by source
- Result: Maximum coverage from multiple chunking approaches

## 🔧 Configuration

### Path Redirections (`config/tbp.json`)

Redirects files during download:

```json
{
  "pattern": "^SOTM-Episode-\\d+$",
  "target": "Script-References/Sermon-on-the-Mount",
  "enabled": true
}
```

### Categorization Rules (`config/tbp.json`)

Maps folder paths to document types:

```json
{
  "folder_pattern": "^Script-References/Sermon-on-the-Mount/?$",
  "type": "Script-References",
  "series": "Sermon-on-the-Mount"
}
```

## 📈 Storage Requirements

| Component | Files | Size |
|-----------|-------|------|
| Source PDFs | 192 | 95 MB |
| Metadata (Step 1) | 192 | 13 MB |
| Chunks (Step 2) | 4 | 19 MB |
| **Total** | **388** | **127 MB** |

## 🚀 Next Steps

1. **✅ Ingestion Complete** (Step 3)
   - ChromaDB collection "bibleproject" created
   - All chunks ingested with embeddings
   - Metadata preserved and searchable
   - Estimated cost: ~$0.11 (1,100 chunks × 400 tokens avg)

2. **Create Source Adapter**
   - Implement BibleProjectSource class
   - Query by strategy (timestamp/bible_reference/semantic)
   - Filter by Bible reference
   - Filter by video timestamp
   - Intelligent result combination and deduplication

3. **RAG Integration**
   - Add to Bible Study Assistant brain orchestrator
   - Enable video timestamp linking in UI
   - Enable Bible reference cross-linking
   - Strategy-based search routing
   - Combine with existing Bible verse sources

4. **UI Enhancements**
   - Video player integration for timestamp links
   - BibleProject attribution and source links
   - Category/series browsing
   - "Watch video at this timestamp" buttons

## 📚 Resources

- **Source**: https://bibleproject.com/downloads/
- **CDN**: https://d1bsmz3sdihplr.cloudfront.net/media/
- **Scripts**: 
  - `scripts/scrape_tbp_pdfs.py` - Download PDFs
  - `scripts/extract_tbp_step1_metadata.py` - Extract metadata
  - `scripts/extract_tbp_step2_chunking.py` - Create chunks
  - `scripts/extract_tbp_step3_ingest.py` - Ingest to ChromaDB
  - `scripts/query_tbp_chromadb.py` - Query and test collection

---

**Last Updated**: December 18, 2024  
**Status**: ✅ ChromaDB ingestion complete - Ready for RAG integration  
**Pipeline Version**: Three-step extraction with multi-strategy chunking and ChromaDB storage