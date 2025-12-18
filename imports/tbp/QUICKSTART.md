# BibleProject Integration - Quick Start

**Status**: ✅ Production Ready  
**Date**: December 18, 2024

---

## Overview

BibleProject resources (1,100 documents) are fully integrated into the RAG system. Every query automatically searches BibleProject content including videos, study notes, and thematic resources.

---

## Quick Reference

### Is It Working?

```bash
# Check if collection exists
python scripts/query_tbp_chromadb.py --stats

# Test a query
python scripts/query_tbp_chromadb.py --query "What is wisdom?"
```

**Expected**: Collection shows 1,100 documents with results for queries.

---

### Pipeline Scripts

Located in `scripts/`:

1. **scrape_tbp_pdfs.py** - Download PDFs from BibleProject
2. **extract_tbp_step1_metadata.py** - Extract text, references, timestamps
3. **extract_tbp_step2_chunking.py** - Create multi-strategy chunks
4. **extract_tbp_step3_ingest.py** - Ingest into ChromaDB
5. **query_tbp_chromadb.py** - Query and explore collection

---

### Data Pipeline

```
Step 0: Download PDFs (192 files)
   ↓
Step 1: Extract metadata (text, Bible refs, timestamps)
   ↓
Step 2: Create chunks (1,100 chunks, 3 strategies)
   ↓
Step 3: Ingest to ChromaDB (with embeddings)
   ↓
Ready for queries!
```

**One-time cost**: ~$0.11 for embeddings

---

### Updating Content

To refresh BibleProject data:

```bash
python scripts/scrape_tbp_pdfs.py
python scripts/extract_tbp_step1_metadata.py
python scripts/extract_tbp_step2_chunking.py
python scripts/extract_tbp_step3_ingest.py
```

**Note**: Re-ingestion overwrites existing data.

---

### Integration Details

**Backend**:
- `bt_servant_engine/services/bibleproject_helpers.py` - Helper utilities
- `bt_servant_engine/services/graph_pipeline.py` - RAG pipeline (enhanced)
- `bt_servant_engine/services/preprocessing.py` - Collection stack (includes BP)

**Frontend**:
- `static/index.html` - Sample questions include BibleProject examples

**How it works**:
1. Every query searches `bibleproject` collection first (highest priority)
2. Results enhanced with video URLs and timestamps
3. Duplicates removed across strategies
4. Included in RAG response generation

---

### Data Location

```
imports/tbp/
├── files/              # 192 source PDFs (generated, excluded from git)
├── extracted/          # Metadata JSON files (generated, excluded from git)
├── chunks/             # 1,100 chunks for embedding (generated, excluded from git)
├── metadata/           # Download manifest (generated, excluded from git)
├── config/             # Configuration files (committed to git)
├── README.md           # Complete documentation (committed to git)
└── QUICKSTART.md       # This file (committed to git)
```

**ChromaDB**: Collection `bibleproject` in `data/chroma.sqlite3`

**Note**: Generated content folders (files/, extracted/, chunks/, metadata/) are excluded from git via `.gitignore`. Run the pipeline scripts to regenerate them.

---

### Sample Queries

Try these to test BibleProject content:

- "What is wisdom according to the Bible?"
- "Explain the concept of covenant in Scripture"
- "Tell me about the Exodus story"
- "What does holiness mean in the Bible?"
- "Explain the image of God concept"

---

### Troubleshooting

**No BibleProject results?**
```bash
# Check collection exists
python scripts/query_tbp_chromadb.py --stats

# Verify in preprocessing.py line 743:
grep -A3 "stack_rank_collections" bt_servant_engine/services/preprocessing.py
# Should show "bibleproject" first
```

**Need to re-ingest?**
```bash
python scripts/extract_tbp_step3_ingest.py
```

---

### Documentation

- **This file**: Quick reference
- **README.md**: Complete pipeline documentation
- **temp_docs/**: Detailed implementation notes (local only, not in git)
- **temp_scripts/**: Test and verification scripts (local only)

---

### Key Features

✅ **Automatic** - Every query includes BibleProject  
✅ **Smart** - Deduplicates results from multiple strategies  
✅ **Rich** - Video links with timestamps  
✅ **Fast** - Cached and optimized  
✅ **Seamless** - No manual intervention needed

---

### Statistics

- **Documents**: 1,100 chunks
- **Sources**: 192 PDFs
- **Strategies**: Timestamp, Bible Reference, Semantic
- **Storage**: ~15-20 MB (with embeddings)
- **Query time**: 350-550ms (first) / <50ms (cached)

---

### Support

**Query tool**: `python scripts/query_tbp_chromadb.py --help`  
**Main docs**: `imports/tbp/README.md`  
**Test scripts**: `temp_scripts/` (if available locally)

---

### Git Configuration

**Excluded from repository** (in `.gitignore`):
- `imports/tbp/files/` - Source PDFs (can be re-downloaded)
- `imports/tbp/extracted/` - Extracted metadata (can be regenerated)
- `imports/tbp/chunks/` - Chunked data (can be regenerated)
- `imports/tbp/metadata/` - Download manifest (can be regenerated)
- `temp_docs/` - Development documentation
- `temp_scripts/` - Test and verification scripts

**Committed to repository**:
- `imports/tbp/config/` - Configuration files
- `imports/tbp/README.md` - Complete documentation
- `imports/tbp/QUICKSTART.md` - This quick reference
- `scripts/*tbp*.py` - Pipeline scripts

**Rationale**: Generated content can be recreated by running the pipeline scripts. This keeps the repository lightweight.

---

**Last Updated**: December 18, 2024  
**Version**: 1.0.0  
**Status**: Production Ready ✅