# Migration Guide - Bible Study Assistant v2.0

## Overview

This guide helps developers understand the transition from `bt_servant_engine` (v1) to `bs_assistant` (v2).

---

## Key Changes

### 1. Package Rename
- **Old**: `bt_servant_engine`
- **New**: `bs_assistant`

### 2. Architecture Shift
- **Old**: Intent-based routing with LangGraph
- **New**: RAG + Conversational LLM

### 3. Dependencies
- **Removed**: `langgraph`
- **Added**: `tiktoken`, `sentence-transformers`
- **Kept**: `openai`, `chromadb`, `tinydb`, `translation-helps-mcp-client`

---

## Directory Structure Comparison

### Old Structure (`previous/bt_servant_engine/`)
```
bt_servant_engine/
├── adapters/          # External integrations
├── apps/              # WhatsApp and web apps
├── core/              # Domain logic
│   ├── intents.py     # Intent definitions
│   ├── agentic.py     # LangGraph workflows
│   └── ports.py       # Interfaces
└── services/          # Service implementations
```

### New Structure (`bs_assistant/`)
```
bs_assistant/
├── api/                      # FastAPI endpoints (TO BUILD)
├── core/
│   ├── detectors/           # Pattern detection ✅
│   │   ├── bible_ref.py     # Bible reference extraction
│   │   └── special_intents.py # TTS, settings detection
│   ├── llm/                 # LLM client ✅
│   │   ├── client.py        # OpenAI with cost tracking
│   │   └── prompts.py       # System prompts
│   └── rag/                 # RAG components (TO BUILD)
├── models/                  # Pydantic models ✅
├── services/                # Business logic (TO BUILD)
└── config.py               # Settings ✅
```

---

## Configuration Changes

### Environment Variables

**Old:**
```bash
BT_SERVANT_LOG_LEVEL=debug
BT_SERVANT_LOG_DIR=./logs
AGENTIC_STRENGTH=normal
```

**New:**
```bash
BS_ASSISTANT_LOG_LEVEL=info
BS_ASSISTANT_LOG_DIR=./logs

# New LLM settings
DEFAULT_MODEL=gpt-4o
SIMPLE_QUERY_MODEL=gpt-4o-mini
TEMPERATURE=0.7

# New RAG settings
VECTOR_STORE_PATH=data/chroma
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_RETRIEVAL_RESULTS=10

# New conversation settings
CONVERSATION_STORE=memory
CONVERSATION_HISTORY_MAX_MESSAGES=10
```

### Settings Class

**Old:**
```python
from bt_servant_engine.core.config import settings

settings.OPENAI_API_KEY
settings.AGENTIC_STRENGTH
```

**New:**
```python
from bs_assistant.config import settings

settings.OPENAI_API_KEY
settings.DEFAULT_MODEL
settings.SIMPLE_QUERY_MODEL
settings.TEMPERATURE
```

---

## Code Migration Examples

### 1. Bible Reference Detection

**Old:**
```python
from bt_servant_engine.services.intent_router import detect_bible_reference

ref = detect_bible_reference(text)
```

**New:**
```python
from bs_assistant.core.detectors import extract_bible_reference

ref = extract_bible_reference(text)
# Returns: BibleReference(book="John", chapter=3, verse_start=16)
```

### 2. LLM Calls

**Old:**
```python
from bt_servant_engine.core.agentic import call_llm

response = call_llm(prompt, intent="SUMMARIZE")
```

**New:**
```python
from bs_assistant.core.llm import llm_client, build_chat_messages

messages = build_chat_messages(
    user_message="Summarize Romans 8",
    retrieved_resources=resources,
)

response, input_tokens, output_tokens, cost = llm_client.chat_completion(
    messages=messages,
    model="gpt-4o-mini",  # Automatic selection available
)
```

### 3. Intent Detection (Now Pattern-Based)

**Old:**
```python
intent = detect_intent(message)
if intent == "TTS_REQUEST":
    handle_tts()
```

**New:**
```python
from bs_assistant.core.detectors import detect_tts_request

tts_req = detect_tts_request(message)
if tts_req.detected:
    # Handle TTS
    handle_tts(tts_req.reference)
```

---

## What to Reuse from Old Code

### ✅ Directly Reusable

1. **Bible Data Files** (`data/`)
   - Verse text files
   - Translation data
   - Keep as-is

2. **ChromaDB Collections** (`data/chroma/`)
   - Embeddings can be reused
   - May need schema updates

3. **Translation Helps Integration**
   - Same MCP client package
   - Same API

4. **Bible Reference Patterns**
   - Reference: `previous/bt_servant_engine/core/intents.py`
   - Already ported to `bs_assistant/core/detectors/bible_ref.py`

### 🔄 Needs Adaptation

1. **Intent Handlers** → **RAG Retrieval**
   - Old: Each intent had dedicated handler
   - New: Single retriever fetches relevant resources
   - Reference old handlers for what data to retrieve

2. **LangGraph Workflows** → **Chat Service**
   - Old: Complex state machine
   - New: Simpler orchestration
   - Extract business logic, discard graph complexity

3. **WhatsApp/Web Apps** → **Unified API**
   - Old: Separate adapters
   - New: Single `/chat` endpoint
   - Apps call same endpoint

### ❌ Not Needed

1. **LangGraph State Management**
   - Too complex for this use case
   - Replaced by simple conversation history

2. **Intent Classification LLM Calls**
   - Old: Used LLM to detect intent
   - New: Pattern-based detection (free)

3. **Complex Routing Logic**
   - Old: Graph-based routing
   - New: Unified conversational flow

---

## Implementation Priority

### Phase 1: Core RAG (Next)
1. Vector store integration
2. Retriever implementation
3. Bible data service

**Reference these old files:**
- `previous/bt_servant_engine/adapters/chroma_client.py`
- `previous/bt_servant_engine/services/bible_lookup.py`
- `previous/bt_servant_engine/services/translation_helps.py`

### Phase 2: Chat Service
1. Conversation management
2. Main orchestration logic
3. Response formatting

**Reference these old files:**
- `previous/bt_servant_engine/core/agentic.py` (for flow logic)
- `previous/bt_servant_engine/services/intent_router.py`

### Phase 3: API Layer
1. FastAPI app setup
2. Chat endpoint
3. Health checks

**Reference these old files:**
- `previous/bt_servant_engine/apps/web/main.py`
- `previous/bt_servant_engine/adapters/web_handler.py`

---

## Testing Strategy

### 1. Create Test Cases from Old System
```python
# Extract test cases from old logs or create based on old behavior
test_cases = [
    ("Show me John 3:16", expected_features=["scripture_retrieval"]),
    ("Summarize Romans 8", expected_features=["summary", "context"]),
    ("What does 'propitiation' mean?", expected_features=["keyword", "definition"]),
]
```

### 2. Compare Quality
```python
# Run same query on both systems
old_response = old_system.process(query)
new_response = new_system.chat(query)

# Compare:
# - Accuracy
# - Completeness
# - Response time
# - Cost
```

### 3. Monitor Metrics
- Track feature retention (target: 85-90%)
- Track cost per query
- Track user satisfaction

---

## Rollback Plan

If issues arise:

1. **Keep old system in `previous/`**
   - Can quickly reference or revert
   - Don't delete until v2 is stable

2. **Parallel Deployment**
   - Run v2 alongside v1
   - Route percentage of traffic to v2
   - Compare metrics

3. **Feature Flags**
   - Toggle between implementations
   - Gradual migration per feature

---

## FAQs

### Q: Can I mix old and new code?
**A:** No. They're separate systems. Reference old code for logic, but don't import it.

### Q: What about my existing embeddings?
**A:** They can be reused. The new system uses ChromaDB same as old.

### Q: Will the API change?
**A:** Yes. New API is simpler:
- Old: Multiple endpoints per intent
- New: Single `/chat` endpoint

### Q: What about WhatsApp integration?
**A:** To be built. Will call the same `/chat` endpoint as web interface.

### Q: How do I contribute?
**A:** Follow the `IMPLEMENTATION_ROADMAP.md` for current priorities.

---

## Getting Help

- **Roadmap**: See `IMPLEMENTATION_ROADMAP.md` for implementation plan
- **Old Code**: Reference `previous/bt_servant_engine/` for patterns
- **Config**: Check `bs_assistant/config.py` for all settings
- **Models**: Check `bs_assistant/models/` for request/response schemas

---

## Summary

**v1 (bt_servant_engine)**: Complex intent routing with LangGraph
**v2 (bs_assistant)**: Simple RAG + Conversational LLM

**Key Benefits:**
- ✅ Simpler architecture
- ✅ More natural conversations
- ✅ Better multi-intent handling
- ✅ Similar or lower cost
- ✅ Easier to maintain and extend

**Migration Status:**
- ✅ Phase 1: Foundation complete
- 🚧 Phase 2: RAG implementation (next)
- 🚧 Phases 3-8: To be implemented