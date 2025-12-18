#!/bin/bash
# Start the bible-study-assistant web chat server

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Disable ChromaDB telemetry
export CHROMA_TELEMETRY=False

# Start the server
echo "🚀 Starting Bible Study Assistant Web Chat API..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📖 API docs at: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uvicorn bt_servant_engine.api_factory:create_app --factory --reload --host 0.0.0.0 --port 8000
