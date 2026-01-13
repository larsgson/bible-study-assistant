# Deployment Guide for fly.io

This guide explains how to deploy the Bible Study Assistant to fly.io.

## Prerequisites

1. **fly.io CLI installed**: https://fly.io/docs/hands-on/install-flyctl/
2. **fly.io account**: Sign up at https://fly.io
3. **Local ChromaDB data**: Populated `data/chroma.sqlite3` with BibleProject documents
4. **OpenAI API key**: For AI features

## Initial Setup (One-time)

### 1. Login to fly.io
```bash
flyctl auth login
```

### 2. Create the app
```bash
flyctl apps create bs-assistant
```

### 3. Create persistent volume
```bash
flyctl volumes create data_volume --region iad --size 1 --yes
```

### 4. Set environment secrets
```bash
flyctl secrets set OPENAI_API_KEY="your-openai-api-key"
flyctl secrets set LOG_PSEUDONYM_SECRET="$(openssl rand -hex 32)"
flyctl secrets set BASE_URL="https://bs-assistant.fly.dev"
```

## Deploying

### 1. Export ChromaDB data
Before each deployment, export your local ChromaDB data:

```bash
python3 scripts/export_chroma_data.py
```

This creates `exports/bibleproject_export.json.gz` (15MB compressed) which will be included in the Docker image for auto-initialization on first run.

### 2. Deploy to fly.io
```bash
flyctl deploy
```

The deployment process will:
- Build Docker image (~188 MB)
- Include Bible data (17 MB) and translation helps (34 MB)
- Include ChromaDB export for auto-initialization
- Deploy to fly.io
- Takes ~2-3 minutes

### 3. First Run Initialization
On first deployment, the app will automatically:
- Detect empty ChromaDB
- Import 1100 BibleProject documents from the export
- Takes ~6 seconds
- Creates `.chroma_initialized` marker file

Subsequent deploys will skip initialization if data already exists.

## Updating Data

### Update ChromaDB data
1. Update local ChromaDB (add/modify documents)
2. Re-export: `python3 scripts/export_chroma_data.py`
3. Stop app: `flyctl scale count 0`
4. Deploy: `flyctl deploy`
5. Start app: `flyctl scale count 1`

The new export will replace existing data on startup.

### Force re-initialization
```bash
flyctl ssh console -C "rm /data/.chroma_initialized"
flyctl machine restart <machine-id>
```

## Monitoring

### View logs
```bash
flyctl logs
```

### Check status
```bash
flyctl status
```

### SSH into machine
```bash
flyctl ssh console
```

### Check ChromaDB collections
```bash
flyctl ssh console -C "python3 -c 'from bt_servant_engine.adapters.chroma import list_chroma_collections, count_documents_in_collection; cols = list_chroma_collections(); print(f\"Collections: {cols}\"); [print(f\"  {c}: {count_documents_in_collection(c)} docs\") for c in cols]'"
```

## Data Included in Deployment

### Automatically Included in Docker Image:
- **Bible Scripture Data** (17 MB)
  - Location: `sources/bible_data/`
  - English BSB, French Louis Segond 1910, Indonesian TBI
  
- **Translation Helps** (34 MB)
  - Location: `sources/translation_helps/`
  - 48 books with translation notes

- **ChromaDB Export** (15 MB compressed)
  - Location: `exports/bibleproject_export.json.gz`
  - 1100 BibleProject documents with embeddings
  - **Generated locally before each deploy**

### Stored in Persistent Volume:
- **ChromaDB Database** (`/data/chroma.sqlite3`)
  - Imported from export on first run
  - Persists across deployments
  - ~45 MB uncompressed

## Configuration

### App Configuration (`fly.toml`)
- **Region**: iad (US East)
- **Memory**: 1 GB
- **Port**: 8080
- **Volume**: 1 GB persistent storage at `/data`
- **Environment**: `DATA_DIR=/data`

### Environment Variables
Set via `flyctl secrets set`:
- `OPENAI_API_KEY` - Required for AI features
- `LOG_PSEUDONYM_SECRET` - For anonymized logging
- `BASE_URL` - Public URL of the app

## Troubleshooting

### App won't start
Check logs for errors:
```bash
flyctl logs
```

Common issues:
- Missing secrets (OPENAI_API_KEY, BASE_URL)
- ChromaDB import failure (check for export file)
- Memory issues (increase VM size in fly.toml)

### ChromaDB import fails
1. Check export file exists locally: `ls -lh exports/`
2. Re-export: `python3 scripts/export_chroma_data.py`
3. Verify export in logs during deployment

### Out of disk space
Increase volume size:
```bash
flyctl volumes extend <volume-id> --size 2
```

### Need to reset everything
```bash
flyctl scale count 0
flyctl ssh console -C "rm -rf /data/*"
flyctl scale count 1
```

This will trigger re-initialization from the export on next startup.

## Cost Optimization

### OpenAI API Costs
- Set spending limits: https://platform.openai.com/settings/organization/limits
- Recommended: $50/month limit
- Configure email alerts

### fly.io Costs
- Current config: ~$2-5/month
- 1 machine, 1GB RAM, 1GB storage
- Scales to zero when inactive (optional)

## Features Available

Once deployed, the following features work:

- ✅ General Bible questions (RAG with BibleProject)
- ✅ Passage summaries (e.g., "Summarize Titus 1")
- ✅ Passage keywords
- ✅ Translation helps (e.g., "Translation challenges for John 1:1")
- ✅ Scripture retrieval (e.g., "Show John 3:16")
- ✅ Scripture audio (text-to-speech)
- ✅ Multi-language support (EN/FR/ID)
- ✅ Rate limiting (5 queries/hour per IP)

## Security Notes

- Secrets are encrypted in fly.io
- Rate limiting prevents abuse
- No API keys exposed in code
- Consider adding password protection for production use

## Support

For issues with:
- **Deployment**: Check fly.io docs at https://fly.io/docs/
- **Application**: Check logs with `flyctl logs`
- **Data issues**: Re-export and redeploy