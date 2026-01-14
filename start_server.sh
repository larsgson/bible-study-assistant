#!/bin/bash
# Start the Bible Study Assistant v2.0 server

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Disable ChromaDB telemetry
export CHROMA_TELEMETRY=False

# Start the server
echo "🚀 Starting Bible Study Assistant v2.0..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📖 API docs at: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo ""
echo "🎯 New v2.0 Features:"
echo "   - RAG-based conversational assistant"
echo "   - Multi-strategy retrieval"
echo "   - Cost-optimized LLM calls"
echo "   - Simpler, faster architecture"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uvicorn bs_assistant.main:app --reload --host 0.0.0.0 --port 8000
