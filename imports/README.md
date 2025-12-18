# Imports Directory

This directory contains external content imported for the Bible Study Assistant RAG system.

## Contents

### `/tbp` - The Bible Project Resources

**Status**: ✅ Collection Complete (161 PDFs)

Comprehensive collection of BibleProject video transcripts and study notes covering:
- Biblical themes and concepts
- How to read the Bible
- Sermon on the Mount series
- God and spiritual beings
- Character of God studies
- Luke-Acts series
- And more...

**Size**: ~26 MB  
**Files**: 161 PDFs organized by category (duplicates removed)  
**Documentation**: See `tbp/COLLECTION_SUMMARY.md`

### Next Steps

1. **Text Extraction** - Run `scripts/extract_tbp_text.py`
2. **Embedding Generation** - Create embeddings via OpenAI
3. **ChromaDB Ingestion** - Store in vector database
4. **RAG Integration** - Add to query pipeline

See `TBP_INTEGRATION_PLAN.md` for detailed roadmap.

---

## Future Import Sources

Potential additional sources for the RAG system:

- **Bible Translations** - Multiple versions for comparison
- **Commentaries** - Classic and modern
- **Lexicons** - Hebrew/Greek word studies
- **Study Bibles** - Notes and cross-references
- **Theological Resources** - Systematic theology texts

---

**Last Updated**: December 18, 2024
