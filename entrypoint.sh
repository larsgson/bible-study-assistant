#!/bin/sh
echo "▶️ BT_SERVANT_LOG_LEVEL=${BT_SERVANT_LOG_LEVEL}"

# Check if ChromaDB needs to be initialized
if [ -f "/app/exports/bibleproject_export.json.gz" ]; then
  # Check if database is empty (new installation)
  if [ ! -s "/data/chroma.sqlite3" ] || [ ! -f "/data/.chroma_initialized" ]; then
    echo "📦 ChromaDB is empty, importing initial data..."
    cd /app && python3 scripts/import_chroma_data.py
    if [ $? -eq 0 ]; then
      touch /data/.chroma_initialized
      echo "✅ ChromaDB import complete"
    else
      echo "⚠️  ChromaDB import failed, but continuing startup"
    fi
  else
    echo "✅ ChromaDB already initialized"
  fi
fi

exec uvicorn bt_servant_engine.api_factory:create_app --factory \
  --host 0.0.0.0 \
  --port 8080 \
  --log-level=${BT_SERVANT_LOG_LEVEL:-info} \
  --access-log
