# Deployment Scripts

This directory contains scripts for exporting, importing, and deploying ChromaDB data to fly.io.

## Scripts Overview

### `export_chroma_data.py`
Exports ChromaDB collections to JSON format for deployment.

**Usage:**
```bash
python3 scripts/export_chroma_data.py
```

**What it does:**
- Reads all collections from local ChromaDB (`data/chroma.sqlite3`)
- Exports documents, metadata, and embeddings to JSON
- Compresses output to `exports/<collection>_export.json.gz`
- Currently exports: `bibleproject` collection (1100 documents, 15MB compressed)

**When to run:**
- Before every deployment to fly.io
- After updating local ChromaDB data
- When setting up a new deployment

### `import_chroma_data.py`
Imports ChromaDB collections from JSON export files.

**Usage:**
```bash
python3 scripts/import_chroma_data.py
```

**What it does:**
- Reads export files from `exports/` directory
- Imports documents with embeddings into ChromaDB
- Creates collections if they don't exist
- Prompts before overwriting existing collections

**When to run:**
- Automatically runs on fly.io first deployment (via `entrypoint.sh`)
- Manually when restoring local ChromaDB from exports
- When initializing a fresh ChromaDB instance

### `upload_chroma_to_flyio.py`
**Status:** Experimental / Not recommended

Attempts to upload ChromaDB database file directly to fly.io via SSH.

**Issues:**
- Very slow (base64 encoding over SSH)
- Often gets killed mid-transfer
- Not reliable for large files

**Recommendation:**
Use the export/import strategy instead (scripts above).

## Deployment Workflow

### Standard Deployment Process

1. **Export local data:**
   ```bash
   python3 scripts/export_chroma_data.py
   ```
   
2. **Deploy to fly.io:**
   ```bash
   flyctl deploy
   ```
   
3. **First run initialization:**
   - Automatically detects empty ChromaDB
   - Imports from `exports/bibleproject_export.json.gz`
   - Takes ~6 seconds
   - Creates `.chroma_initialized` marker

### Updating Data on fly.io

1. Update local ChromaDB data
2. Export: `python3 scripts/export_chroma_data.py`
3. Stop app: `flyctl scale count 0`
4. Deploy: `flyctl deploy`
5. Start app: `flyctl scale count 1`

The new export will trigger re-initialization.

### Force Re-initialization

```bash
flyctl ssh console -C "rm /data/.chroma_initialized"
flyctl machine restart <machine-id>
```

## Technical Details

### Export Format

```json
{
  "collection_name": "bibleproject",
  "batches": [
    {
      "ids": ["doc1", "doc2", ...],
      "documents": ["text1", "text2", ...],
      "metadatas": [{}, {}, ...],
      "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...]
    }
  ]
}
```

### Why Export/Import Instead of Direct Copy?

1. **Portability:** JSON works across different ChromaDB versions
2. **Compression:** 45MB database → 15MB export
3. **Validation:** Can verify data before importing
4. **Reliability:** More reliable than SSH file transfer
5. **Automation:** Easy to include in Docker build

### File Sizes

- Local ChromaDB: 45 MB (uncompressed SQLite)
- Compressed for transfer: 16 MB (gzip)
- JSON export: 59 MB (uncompressed)
- JSON export compressed: 15 MB (gzip)
- Deployed on fly.io: 45 MB (re-created from export)

## Troubleshooting

### Export fails
- **Check:** ChromaDB database exists at `data/chroma.sqlite3`
- **Check:** Collections are populated
- **Fix:** Run ingestion scripts to populate ChromaDB first

### Import fails on fly.io
- **Check logs:** `flyctl logs | grep ChromaDB`
- **Common issue:** Missing export file in Docker image
- **Fix:** Ensure `exports/` is not in `.dockerignore`
- **Verify:** Check `exports/` exists locally before deploy

### Import succeeds but no data
- **Check:** Collection count after import
- **Run:** `flyctl ssh console -C "python3 -c 'from bt_servant_engine.adapters.chroma import list_chroma_collections, count_documents_in_collection; cols = list_chroma_collections(); [print(f\"{c}: {count_documents_in_collection(c)}\") for c in cols]'"`
- **Expected:** `bibleproject: 1100`

### Need to re-export
```bash
# Delete old export
rm -rf exports/

# Re-export
python3 scripts/export_chroma_data.py

# Verify
ls -lh exports/
```

## Git Strategy

The `exports/` directory is in `.gitignore` because:
- Contains generated 15MB binary files
- Would bloat Git history
- Deployment is done from local, not from GitHub
- Can be regenerated on-demand from ChromaDB

**Important:** Always run `export_chroma_data.py` before deploying to fly.io!

## See Also

- [DEPLOYMENT.md](../DEPLOYMENT.md) - Complete fly.io deployment guide
- [fly.toml](../fly.toml) - fly.io configuration
- [entrypoint.sh](../entrypoint.sh) - Auto-initialization logic