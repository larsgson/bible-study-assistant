# Bible Study Assistant - Web Demo

> A web-based Bible study assistant adapted from [unfoldingWord/bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine)

This is a **derived version** that removes WhatsApp functionality and adds a modern web chat interface for Bible study questions. The core intelligence (RAG engine, intent routing, passage analysis) comes from the original BT Servant Engine, with adaptations for web-based interaction.

---

## 🔗 Relationship to BT Servant Engine

This repository is derived from **[unfoldingWord/bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine)**, an AI-powered WhatsApp assistant for Bible translators.

**What's Different Here:**
- ✅ **Web chat interface** instead of WhatsApp
- ✅ **Browser-based UI** (static/index.html)
- ✅ **Simplified deployment** for public demos
- ❌ **No WhatsApp integration** (removed Meta API dependencies)
- ❌ **No voice processing** (removed Deepgram/Twilio)

**What's the Same:**
- ✅ Same RAG engine and intent routing
- ✅ Same Bible data and translation helps
- ✅ Same LangGraph orchestration
- ✅ Same core architecture (onion/hexagonal)

**For full documentation, tests, and examples**, see the **[original repository](https://github.com/unfoldingWord/bt-servant-engine)**.

---

## 🎯 Future Vision

This derived version aims to evolve into a **specialized Web Bible Study Assistant** by:

1. **Tailoring the interface** for web-based Bible study (not translation)
2. **Optimizing intents** for study questions vs. translation work
3. **Adding web-specific features** (bookmarks, history, annotations)
4. **Improving UX** for long-form study and exploration
5. **Keeping the core engine** in sync with upstream improvements

The goal is to maintain compatibility with BT Servant Engine's core while building web-specific enhancements.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- OpenAI API key
- 20MB disk space (Bible data)

### Local Development

```bash
# 1. Clone and setup
git clone <this-repo>
cd bible-study-assistant
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Start the server
./start_server.sh
# Or manually: uvicorn bt_servant_engine.api_factory:create_app --factory --reload

# 5. Open browser
open http://localhost:8000
```

The web interface will load with sample questions to get you started.

---

## 🌐 Web Interface

### Features

- **Modern chat UI** with typing indicators
- **Sample questions** for quick start
- **Session persistence** (localStorage)
- **Real-time responses** from RAG engine
- **No login required** (rate limiting recommended for public demos)

### Try These Questions

- "Summarize Titus 1"
- "Show John 3:16–18"
- "Translation challenges for John 1:1?"
- "Important words in Romans 1"

### Customization

The web interface is self-contained in `static/index.html`. Modify CSS, JavaScript, or sample questions directly in that file.

---

## 🎁 What This Repo Adds

### Unique to This Derived Version

| File/Folder | Purpose |
|-------------|---------|
| `static/` | Web chat interface (HTML/CSS/JS) |
| `HOSTING_OPTIONS.md` | Deployment guide (Fly.io, Render) |
| `bt_servant_engine/adapters/web_messaging.py` | Web messaging adapter |
| `bt_servant_engine/apps/api/routes/chat.py` | Web chat API endpoint |

### Changed from Original

| Change | Reason |
|--------|--------|
| Removed WhatsApp routes | Web-only demo |
| Removed Twilio/Deepgram | No voice processing needed |
| Added static file serving | Serve web interface |
| Simplified configuration | Fewer required env vars |

---

## 📚 Documentation

### Web Demo Specific

- **[HOSTING_OPTIONS.md](HOSTING_OPTIONS.md)** - Deploy to Fly.io or Render
- **[static/README.md](static/README.md)** - Web interface documentation
- **[static/QUICKSTART.txt](static/QUICKSTART.txt)** - Visual quick start guide

### Original BT Servant Engine

For comprehensive documentation, see **[bt-servant-engine repository](https://github.com/unfoldingWord/bt-servant-engine)**:

- **Architecture** - Onion/hexagonal layers, dependency injection
- **Intent System** - 17 supported intents and routing logic
- **LangGraph Flow** - Decision pipeline and orchestration
- **Testing** - Full test suite with OpenAI mocks
- **Quality Gates** - Linting, type checking, coverage requirements
- **API Reference** - All endpoints and admin routes

---

## 🏗️ Architecture

This derived version maintains the same clean architecture as the original:

```
apps/api/          → FastAPI routes (web chat endpoint)
services/          → Intent routing, RAG, orchestration
adapters/          → ChromaDB, OpenAI, messaging (web adapter)
core/              → Domain models, configuration
```

**Key Principle:** Dependencies point inward. Apps depend on services, services depend on core, adapters implement core ports.

See [bt-servant-engine architecture docs](https://github.com/unfoldingWord/bt-servant-engine#architecture) for details.

---

## 🔧 Configuration

### Required Environment Variables

```bash
OPENAI_API_KEY=sk-...           # Required: OpenAI API access
LOG_PSEUDONYM_SECRET=<random>   # Required: For PII scrubbing
DATA_DIR=./data                  # Optional: Data storage location
```

### Optional Settings

```bash
BT_SERVANT_LOG_LEVEL=info       # Logging level
CACHE_ENABLED=true               # Enable response caching
```

**Note:** WhatsApp-related variables (META_WHATSAPP_TOKEN, etc.) are not needed for web demo.

See `env.example` for full configuration options.

---

## 🚢 Deployment

### Recommended: Fly.io

Already configured with `fly.toml` and `Dockerfile`:

```bash
# Install Fly CLI
brew install flyctl

# Deploy (4 commands)
flyctl auth login
flyctl deploy
flyctl secrets set OPENAI_API_KEY=sk-...
flyctl secrets set LOG_PSEUDONYM_SECRET=$(openssl rand -hex 32)

# Done! https://your-app.fly.dev
```

### Alternative: Render

Simple web-based deployment:

1. Connect GitHub repo to Render
2. Add environment variables
3. Deploy automatically

See **[HOSTING_OPTIONS.md](HOSTING_OPTIONS.md)** for detailed deployment guides.

---

## ⚠️ Important: API Costs & Rate Limiting

**OpenAI API costs can be significant!** Every user query costs ~$0.01-0.03.

### Cost Protection

1. **Set OpenAI spending limits** in dashboard: $10/day recommended
2. **Implement rate limiting** before public deployment:
   ```bash
   pip install slowapi
   ```
   See [HOSTING_OPTIONS.md](HOSTING_OPTIONS.md) for implementation guide
3. **Monitor usage** closely in first week
4. **Expected costs:** $10-50/month for small demos

**Without rate limiting**, a public demo could cost hundreds of dollars per day.

---

## 🧪 Testing

### Quick Test (No OpenAI API calls)

```bash
pytest -q -m "not openai"
```

### Full Test Suite

See [bt-servant-engine testing docs](https://github.com/unfoldingWord/bt-servant-engine#testing) for comprehensive test documentation.

---

## 🤝 Contributing

This derived version focuses on **web-specific features** for Bible study.

**For core engine improvements** (RAG, intent routing, orchestration), contribute to the upstream repository: **[unfoldingWord/bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine)**

**For this derived version**, contributions welcome for:
- Web UI improvements
- Web-specific features (bookmarks, history, etc.)
- Deployment configurations
- Bible study-focused intents
- Documentation improvements

---

## 📊 Supported Features

Inherited from BT Servant Engine:

- ✅ **Passage Summaries** - AI-generated summaries of Bible passages
- ✅ **Scripture Retrieval** - Fetch and display Bible verses
- ✅ **Translation Helps** - Translation challenges and notes
- ✅ **Keywords** - Key terms and theological concepts
- ✅ **RAG-based Q&A** - Answer questions using Bible resources
- ✅ **Multi-language** - Respond in user's preferred language
- ✅ **FIA Resources** - Faithful and Inclusive Access guidance

See [intent documentation](https://github.com/unfoldingWord/bt-servant-engine) in original repo for details.

---

## 🔄 Staying in Sync with Upstream

This derived version periodically pulls updates from the original BT Servant Engine to benefit from:
- Bug fixes
- Performance improvements
- New features in core engine
- Updated Bible data

**Merge strategy:** Cherry-pick core improvements while maintaining web-specific adaptations.

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

This is a derived version of [bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine), which is also MIT licensed.

---

## 🆘 Support

- **Web demo issues:** Open issue in this repository
- **Core engine issues:** Open issue in [bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine)
- **Deployment help:** See [HOSTING_OPTIONS.md](HOSTING_OPTIONS.md)

---

## 🙏 Acknowledgments

This project builds on the excellent work of the [unfoldingWord](https://www.unfoldingword.org/) team and the [bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine) contributors.

The web adaptation maintains the core intelligence while making it accessible through a browser-based interface.

---

**Ready to try it?** Run `./start_server.sh` and open http://localhost:8000 🚀