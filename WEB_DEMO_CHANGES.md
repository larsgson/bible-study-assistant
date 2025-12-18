# Web Demo Changes Summary

This document summarizes the changes made to transform [bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine) into a web-based Bible study assistant demo.

---

## 🔗 Relationship to Original

This is a **derived version** of [unfoldingWord/bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine) adapted for web-based Bible study.

**Original Purpose:** WhatsApp chatbot for Bible translators  
**This Derived Version's Purpose:** Web-based Bible study assistant with browser interface

---

## 🎯 Key Changes

### Added

1. **Web Chat Interface** (`static/`)
   - `static/index.html` - Complete web UI (HTML/CSS/JS in one file)
   - `static/README.md` - Interface documentation
   - `static/QUICKSTART.txt` - Quick start guide

2. **Web API Endpoint**
   - `bt_servant_engine/apps/api/routes/chat.py` - Web chat endpoint
   - `bt_servant_engine/adapters/web_messaging.py` - Web messaging adapter

3. **Deployment Documentation**
   - `HOSTING_OPTIONS.md` - Fly.io and Render deployment guides
   - `WEB_DEMO_CHANGES.md` - This file

4. **Static File Serving**
   - Modified `bt_servant_engine/apps/api/app.py` to serve static files
   - Root redirect to chat interface

### Removed

1. **WhatsApp Integration**
   - Removed Meta/WhatsApp webhook routes
   - Removed WhatsApp message processing
   - Removed voice processing (Deepgram/Twilio)

2. **Dependencies**
   - Removed `twilio==9.5.2`
   - Removed `deepgram-sdk==4.0.0`

3. **Documentation** (Available in Original Repo)
   - Removed `AGENTS.md` → See [original repo](https://github.com/unfoldingWord/bt-servant-engine)
   - Removed `CLAUDE.md` → See [original repo](https://github.com/unfoldingWord/bt-servant-engine)
   - Removed `GEMINI.md` → See [original repo](https://github.com/unfoldingWord/bt-servant-engine)
   - Removed `KNOWN_ISSUES.txt` → See [original repo](https://github.com/unfoldingWord/bt-servant-engine)
   - Removed transformation-specific docs (PHASE summaries, etc.)

### Modified

1. **Configuration**
   - Simplified environment variables (no WhatsApp tokens needed)
   - Updated `bt_servant_engine/core/config.py` for web-only mode

2. **Logging**
   - Fixed deprecated `pythonjsonlogger` import
   - Updated to use `pythonjsonlogger.json.JsonFormatter`

3. **Health Routes**
   - Removed root endpoint from health router
   - Allows chat interface redirect

---

## 📊 Statistics

- **Lines removed:** ~1,600 (WhatsApp integration + documentation)
- **Lines added:** ~650 (web interface + deployment docs)
- **Net change:** ~950 lines removed
- **Dependencies removed:** 2 (twilio, deepgram-sdk)
- **New files:** 4 (web interface + docs)

---

## 🚀 What's Preserved

All core functionality from bt-servant-engine:

✅ **RAG Engine** - Same retrieval-augmented generation  
✅ **Intent Routing** - Same 17 intents and orchestration  
✅ **LangGraph Pipeline** - Same brain orchestration  
✅ **Bible Data** - Same BSB passages and resources  
✅ **ChromaDB Integration** - Same vector storage  
✅ **OpenAI Integration** - Same LLM processing  
✅ **Caching** - Same performance optimizations  
✅ **Architecture** - Same onion/hexagonal layers  

---

## 🎯 Future Roadmap

This derived version aims to diverge from the original by:

1. **Tailoring for Bible Study** (not translation)
   - Study-focused intents
   - Cross-reference features
   - Study plan support

2. **Web-Specific Features**
   - Bookmarks and favorites
   - Study notes and annotations
   - Conversation history
   - Export functionality

3. **UI Enhancements**
   - Markdown rendering
   - Verse highlighting
   - Dark mode
   - Mobile optimization

4. **Integration**
   - Streaming responses (SSE/WebSocket)
   - Bible app integration
   - Study tool plugins

---

## 🔄 Syncing with Upstream

### Strategy

- **Core engine:** Pull updates from upstream when beneficial
- **Web features:** Develop independently in this derived version
- **Bug fixes:** Contribute back to upstream when applicable

### What to Sync

✅ Core engine improvements  
✅ Bug fixes  
✅ Performance optimizations  
✅ Bible data updates  

### What NOT to Sync

❌ WhatsApp features  
❌ Translation-specific intents  
❌ Platform-specific code  

---

## 📝 Documentation Map

### This Repository (Web Demo Specific)

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start |
| `HOSTING_OPTIONS.md` | Deployment guides (Fly.io, Render) |
| `WEB_DEMO_CHANGES.md` | This file - change summary |
| `static/README.md` | Web interface documentation |
| `static/QUICKSTART.txt` | Visual quick start guide |

### Original Repository (Full Documentation)

See [bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine) for:

- **Architecture** - Detailed layer descriptions
- **Intent System** - All 17 intents documented
- **LangGraph Flow** - Orchestration diagrams
- **Testing** - Comprehensive test suite
- **Quality Gates** - Linting, type checking, coverage
- **API Reference** - All endpoints and admin routes
- **Contributing** - Development guidelines

---

## 🤝 Contributing

### To This Derived Version (Web Features)

Contributions welcome for:
- Web UI improvements
- Web-specific features (bookmarks, history, etc.)
- Deployment configurations
- Bible study-focused enhancements

### To Original (Core Engine)

For core engine improvements, contribute to:  
**[unfoldingWord/bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine)**

---

## ⚠️ Important Notes

### API Costs

Both this derived version and the original use OpenAI API, which costs money:
- ~$0.01-0.03 per query
- ~$10-50/month for small demos
- **Rate limiting required** for public deployments

See `HOSTING_OPTIONS.md` for cost management strategies.

### Configuration Differences

**This derived version requires:**
```bash
OPENAI_API_KEY=sk-...
LOG_PSEUDONYM_SECRET=<random>
```

**Original also requires:**
```bash
META_WHATSAPP_TOKEN=...
META_PHONE_NUMBER_ID=...
META_APP_SECRET=...
# ... etc
```

### Testing

This derived version maintains the same test structure as original:
```bash
pytest -q -m "not openai"  # Quick tests
```

See [original repo](https://github.com/unfoldingWord/bt-servant-engine#testing) for full test documentation.

---

## 📞 Support

- **Web demo issues:** Open issue in this repository
- **Core engine issues:** Open issue in [bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine)
- **Deployment help:** See `HOSTING_OPTIONS.md`

---

## 🙏 Acknowledgments

This web demo builds on the excellent work of:
- [unfoldingWord](https://www.unfoldingword.org/) team
- [bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine) contributors

The web interface makes the powerful BT Servant Engine accessible through a browser, maintaining the core intelligence while simplifying deployment and usage for Bible study purposes.

---

**Version:** 1.0  
**Last Updated:** December 2025  
**Original Repo:** https://github.com/unfoldingWord/bt-servant-engine