# How to Run Bible Study Assistant v2.0

## Quick Start

### Run the Server (Recommended)

```bash
./start_server.sh
```

This will:
- ✅ Activate the virtual environment
- ✅ Set environment variables
- ✅ Start the server on port 8000
- ✅ Enable hot-reload for development

### Alternative Methods

#### Method 1: Using Python directly
```bash
source .venv/bin/activate
python bs_assistant/main.py
```

#### Method 2: Using uvicorn directly
```bash
source .venv/bin/activate
uvicorn bs_assistant.main:app --reload --host 0.0.0.0 --port 8000
```

#### Method 3: Production mode (no reload)
```bash
source .venv/bin/activate
uvicorn bs_assistant.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Server Access

Once running, the server is available at:

- **Base URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Interactive Swagger UI)
- **ReDoc:** http://localhost:8000/redoc (Alternative API docs)
- **Health Check:** http://localhost:8000/health

---

## Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Chat Request
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does John 3:16 mean?",
    "user_id": "test_user",
    "language": "en"
  }'
```

### Get Conversation History
```bash
curl http://localhost:8000/chat/history/test_user
```

### Clear Conversation History
```bash
curl -X POST http://localhost:8000/chat/clear?user_id=test_user
```

---

## Environment Variables

Make sure your `.env` file is configured:

```bash
# Required
OPENAI_API_KEY=your-key-here
BASE_URL=http://localhost:8000
LOG_PSEUDONYM_SECRET=your-secret-here

# Optional (has defaults)
DEFAULT_MODEL=gpt-4o
SIMPLE_QUERY_MODEL=gpt-4o-mini
TEMPERATURE=0.7
MAX_TOKENS=2000
```

---

## Port Configuration

### Change Default Port (8000)

**Option 1: Edit start_server.sh**
```bash
# Change the last line to:
uvicorn bs_assistant.main:app --reload --host 0.0.0.0 --port 8080
```

**Option 2: Pass port as argument**
```bash
uvicorn bs_assistant.main:app --reload --host 0.0.0.0 --port 8080
```

---

## Stopping the Server

Press `CTRL+C` in the terminal where the server is running.

Or if running in background:
```bash
pkill -f "uvicorn bs_assistant.main:app"
```

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
./start_server.sh --port 8080
```

### Module Not Found
```bash
# Reinstall the package
pip install -e .
```

### Environment Not Activated
```bash
# Activate virtual environment
source .venv/bin/activate

# Verify
which python  # Should show path to .venv
```

### Missing Dependencies
```bash
# Install all dependencies
pip install -e .

# Or install individually
pip install tiktoken sentence-transformers
```

---

## Comparison with v1

### Old Way (v1)
```bash
./start_server.sh
# Used: uvicorn bt_servant_engine.api_factory:create_app --factory
```

### New Way (v2)
```bash
./start_server.sh
# Uses: uvicorn bs_assistant.main:app
```

**Key Differences:**
- ✅ No `--factory` flag needed (direct app instance)
- ✅ Simpler module path
- ✅ Same port (8000)
- ✅ Same endpoints work
- ✅ Better performance

---

## Development Mode vs Production

### Development (Hot Reload)
```bash
uvicorn bs_assistant.main:app --reload --host 0.0.0.0 --port 8000
```
- ✅ Automatically reloads on code changes
- ✅ Detailed error messages
- ⚠️ Single worker

### Production (Optimized)
```bash
uvicorn bs_assistant.main:app --host 0.0.0.0 --port 8000 --workers 4
```
- ✅ Multiple workers for better performance
- ✅ Better stability
- ❌ No auto-reload

---

## Docker (Future)

Once Docker configuration is added (Phase 8):

```bash
docker-compose up
```

This will handle all setup automatically.

---

## Quick Reference

| Task | Command |
|------|---------|
| Start server | `./start_server.sh` |
| Stop server | `CTRL+C` |
| Health check | `curl http://localhost:8000/health` |
| API docs | Open `http://localhost:8000/docs` in browser |
| Chat request | `curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"Hello","user_id":"test","language":"en"}'` |
| View logs | Check console output |
| Change port | Edit `start_server.sh` or use `--port` flag |

---

## What Changed from v1?

| Aspect | v1 | v2 |
|--------|----|----|
| Start command | `./start_server.sh` | `./start_server.sh` (same!) |
| Module path | `bt_servant_engine.api_factory` | `bs_assistant.main` |
| Factory pattern | Yes (`--factory`) | No (direct app) |
| Architecture | Complex LangGraph | Simple RAG |
| Response time | 2-5 seconds | 1-3 seconds |
| Cost | $0.005-0.01 | $0.0002-0.01 |

---

## Summary

**To run Bible Study Assistant v2.0:**

1. Make sure dependencies are installed: `pip install -e .`
2. Configure `.env` with your OpenAI API key
3. Run: `./start_server.sh`
4. Test: Open http://localhost:8000/docs

**That's it!** The same simple command as before, but with a better, faster system underneath. 🚀