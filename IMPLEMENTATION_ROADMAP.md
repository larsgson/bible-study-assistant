# Implementation Roadmap - Bible Study Assistant v2.0

## ✅ Phase 1: Foundation (COMPLETED)

### Project Structure
- [x] Moved old implementation to `/previous/bt_servant_engine/`
- [x] Created new `bs_assistant/` package structure
- [x] Updated `pyproject.toml` with new package name and dependencies
- [x] Removed `langgraph` dependency (no longer needed)
- [x] Added `tiktoken` and `sentence-transformers` for embeddings

### Core Infrastructure
- [x] **Configuration** (`bs_assistant/config.py`)
  - Settings for LLM models, RAG, conversation history
  - Cost tracking configuration
  - Verse limits and response configuration
  
- [x] **Models** (`bs_assistant/models/`)
  - `ChatRequest` and `ChatResponse` models
  - `RetrievedResource` for RAG results
  - `HealthResponse` for health checks

- [x] **Detectors** (`bs_assistant/core/detectors/`)
  - Bible reference detector with comprehensive book patterns
  - Special intent detection (TTS, Settings)
  - Pattern-based, zero-cost detection

- [x] **LLM Client** (`bs_assistant/core/llm/`)
  - OpenAI client with cost tracking
  - Token counting using tiktoken
  - Model selection (gpt-4o vs gpt-4o-mini)
  - Async support

- [x] **Prompts** (`bs_assistant/core/llm/prompts.py`)
  - System prompt for Bible translation assistant
  - RAG context formatting
  - Specialized prompts (summary, keywords, translation help)

---

## 🚧 Phase 2: RAG Implementation (NEXT)

### Vector Store Setup
- [ ] **ChromaDB Integration** (`bs_assistant/core/rag/vector_store.py`)
  - Initialize ChromaDB client
  - Collection management (create, load, update)
  - Query vector store with similarity search
  - Reuse existing embeddings where possible
  - Consider collection schema redesign for better retrieval

- [ ] **Retriever** (`bs_assistant/core/rag/retriever.py`)
  - Unified retrieval interface
  - Combine multiple retrieval strategies:
    - Bible verse lookup (direct)
    - Cross-reference lookup
    - Semantic search (vector)
    - Translation helps integration
    - BibleProject content
  - Score and rank results
  - Deduplicate resources

### Data Access Layer
- [ ] **Bible Data Service** (`bs_assistant/services/bible_service.py`)
  - Verse text retrieval
  - Chapter/book retrieval
  - Translation support
  - Reuse existing data from `/data/`

- [ ] **Cross-Linking Service** (`bs_assistant/services/cross_linking_service.py`)
  - Load existing verse resource index
  - Link verses to BibleProject content
  - Link verses to translation helps
  - Reference previous implementation in `/previous/`

- [ ] **Translation Helps Service** (`bs_assistant/services/translation_helps_service.py`)
  - Use `translation-helps-mcp-client` package
  - Retrieve notes, questions, words for verses
  - Cache results

---

## 🚧 Phase 3: Chat Service (NEXT)

### Conversation Management
- [ ] **Conversation Store** (`bs_assistant/services/conversation_service.py`)
  - In-memory store (for development)
  - TinyDB store (for persistence)
  - Session management
  - History truncation (keep last N messages)

### Main Chat Service
- [ ] **Chat Service** (`bs_assistant/services/chat_service.py`)
  - Main orchestration logic
  - Process user message:
    1. Detect Bible references
    2. Check for special intents (TTS, settings)
    3. Retrieve relevant resources via RAG
    4. Build LLM prompt with context
    5. Call LLM with cost tracking
    6. Store conversation history
    7. Return response

### Query Classification
- [ ] **Simple Query Detector** (`bs_assistant/core/detectors/query_complexity.py`)
  - Detect if query is simple (use gpt-4o-mini)
  - Patterns for simple queries:
    - "Show me John 3:16"
    - "What is Romans 8 about?"
  - Complex queries use gpt-4o

---

## 🚧 Phase 4: API Layer

### FastAPI Application
- [ ] **Main App** (`bs_assistant/main.py`)
  - Create FastAPI application
  - CORS configuration
  - Middleware setup
  - Exception handlers

- [ ] **Chat Endpoint** (`bs_assistant/api/chat.py`)
  - `POST /chat` endpoint
  - Request validation
  - Call chat service
  - Response formatting
  - Error handling

- [ ] **Health Check** (`bs_assistant/api/health.py`)
  - `GET /health` endpoint
  - Check dependencies (ChromaDB, OpenAI)
  - Return status and version

- [ ] **Admin Endpoints** (`bs_assistant/api/admin.py`)
  - Cost tracking endpoint
  - Usage statistics
  - Cache management
  - Authentication

---

## 🚧 Phase 5: Special Features

### Text-to-Speech Handler
- [ ] **TTS Service** (`bs_assistant/services/tts_service.py`)
  - Detect TTS requests
  - Extract Bible reference
  - Generate audio using OpenAI TTS
  - Return audio URL or data
  - Cache generated audio

### Settings Handler
- [ ] **Settings Service** (`bs_assistant/services/settings_service.py`)
  - Detect settings changes
  - Update user preferences
  - Store in database or memory
  - Support: language, translation, voice preferences

### Multi-Intent Handler
- [ ] **Multi-Intent Processor** (`bs_assistant/core/multi_intent.py`)
  - Detect multiple intents in single message
  - Process each intent separately
  - Combine results coherently
  - Handle dependencies between intents

---

## 🚧 Phase 6: Optimization

### Cost Optimization
- [ ] **Model Selection Logic**
  - Implement `is_simple_query()` function
  - Route simple queries to gpt-4o-mini
  - Monitor cost savings

- [ ] **Caching Layer**
  - Cache LLM responses for identical queries
  - Cache RAG retrievals
  - Cache embeddings
  - Implement TTL and eviction policies

- [ ] **Token Management**
  - Truncate long contexts intelligently
  - Summarize conversation history if too long
  - Track token usage per user/session

### Response Quality
- [ ] **Structured Output**
  - Use JSON schema for keywords extraction
  - Use structured output for summaries
  - Ensure consistent formatting

- [ ] **Prompt Engineering**
  - Test and refine prompts
  - Add examples to prompts (few-shot)
  - Optimize for clarity and conciseness

---

## 🚧 Phase 7: Testing & Validation

### Unit Tests
- [ ] Test Bible reference detection
- [ ] Test special intent detection
- [ ] Test LLM client (mocked)
- [ ] Test RAG retrieval (mocked)
- [ ] Test chat service logic

### Integration Tests
- [ ] Test full chat flow
- [ ] Test with real ChromaDB
- [ ] Test cost tracking
- [ ] Test conversation history

### Comparison Tests
- [ ] Create test suite from old system
- [ ] Compare responses quality
- [ ] Measure performance
- [ ] Validate feature retention (target: 85-90%)

---

## 🚧 Phase 8: Migration & Deployment

### Data Migration
- [ ] **Embeddings Migration**
  - Verify existing ChromaDB collections
  - Test compatibility
  - Migrate if schema changes needed

- [ ] **Conversation History Migration** (if needed)
  - Export old conversations
  - Import to new format

### Deployment
- [ ] Update `Dockerfile` for new package name
- [ ] Update `entrypoint.sh` and `start_server.sh`
- [ ] Update environment variables
- [ ] Test Docker build
- [ ] Deploy to staging
- [ ] Monitor and validate
- [ ] Deploy to production

### Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Deployment guide
- [ ] Cost optimization guide
- [ ] Migration guide from v1

---

## 📊 Success Metrics

### Feature Retention (Target: 85-90%)
- Scripture Retrieval: ⬆️ Better
- Passage Summaries: ➡️ Equal
- Question Answering: ⬆️ Better
- Translation Helps: ⬇️ Slight loss (acceptable)
- Keywords: ⬇️ Slight loss (acceptable)
- Multi-Intent: ⬆️ Much better
- Conversational: ⬆️ Better
- FIA Guidance: ⬆️ Better
- Translate Scripture: ➡️ Equal
- TTS: Needs special handler
- Settings: Needs work
- Format Consistency: Needs prompt engineering

### Performance Targets
- Average response time: < 3 seconds
- P95 response time: < 5 seconds
- Cost per query: Similar or lower than v1
- Uptime: > 99.5%

### Quality Targets
- User satisfaction: > 4/5
- Accurate references: > 95%
- Relevant retrievals: > 80%
- Natural responses: > 4/5 rating

---

## 🎯 Current Status

**Phase 1: COMPLETED** ✅
- Foundation is solid
- Core infrastructure in place
- Ready to build RAG layer

**Next Steps:**
1. Implement ChromaDB vector store integration
2. Build retriever with multiple strategies
3. Create Bible data service
4. Implement chat service
5. Build FastAPI endpoints

**Estimated Timeline:**
- Phase 2 (RAG): 2-3 days
- Phase 3 (Chat): 1-2 days
- Phase 4 (API): 1 day
- Phase 5 (Special Features): 2-3 days
- Phase 6 (Optimization): 2-3 days
- Phase 7 (Testing): 2-3 days
- Phase 8 (Deployment): 1-2 days

**Total: ~2-3 weeks for complete implementation**