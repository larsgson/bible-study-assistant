# Quick Start Guide - Bible Study Assistant v2.0

## Overview

This guide shows you how to use the new RAG-based conversational Bible Study Assistant.

---

## Installation

```bash
# Install dependencies
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

---

## Basic Usage Examples

### 1. Bible Reference Detection

```python
from bs_assistant.core.detectors import extract_bible_reference

# Extract a Bible reference from user input
text = "Can you explain John 3:16 to me?"
ref = extract_bible_reference(text)

print(ref.book)          # "John"
print(ref.chapter)       # 3
print(ref.verse_start)   # 16
print(str(ref))          # "John 3:16"
```

### 2. Special Intent Detection

```python
from bs_assistant.core.detectors import detect_tts_request, detect_settings_request

# Detect TTS request
text = "Read Romans 8 to me"
tts_req = detect_tts_request(text)
print(tts_req.detected)  # True

# Detect settings change
text = "Change language to Spanish"
settings_req = detect_settings_request(text)
print(settings_req.detected)       # True
print(settings_req.setting_type)   # "language"
print(settings_req.setting_value)  # "Spanish"
```

### 3. LLM Client with Cost Tracking

```python
from bs_assistant.core.llm import llm_client, build_chat_messages

# Build messages for a simple query
messages = build_chat_messages(
    user_message="What is the main theme of Romans 8?",
    retrieved_resources=[
        {
            "type": "verse",
            "content": "There is therefore now no condemnation...",
            "reference": "Romans 8:1"
        }
    ]
)

# Make LLM call with automatic cost tracking
response, input_tokens, output_tokens, cost_usd = llm_client.chat_completion(
    messages=messages,
    model="gpt-4o-mini"  # Use cheaper model for simple queries
)

print(f"Response: {response}")
print(f"Cost: ${cost_usd:.4f}")
print(f"Tokens: {input_tokens} in, {output_tokens} out")
```

### 4. Model Selection Based on Complexity

```python
from bs_assistant.core.llm import llm_client

# Simple query - use gpt-4o-mini (cheaper)
simple_model = llm_client.select_model(is_simple=True)
print(simple_model)  # "gpt-4o-mini"

# Complex query - use gpt-4o (better quality)
complex_model = llm_client.select_model(is_simple=False)
print(complex_model)  # "gpt-4o"
```

### 5. Token Counting

```python
from bs_assistant.core.llm import llm_client

text = "This is a sample text to count tokens."
token_count = llm_client.count_tokens(text, model="gpt-4o")
print(f"Tokens: {token_count}")

# Count tokens in message list
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
]
message_tokens = llm_client.count_message_tokens(messages)
print(f"Message tokens: {message_tokens}")
```

---

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here
BASE_URL=https://your-domain.com
LOG_PSEUDONYM_SECRET=your-secret-here

# LLM Configuration
DEFAULT_MODEL=gpt-4o
SIMPLE_QUERY_MODEL=gpt-4o-mini
TEMPERATURE=0.7
MAX_TOKENS=2000

# RAG Configuration
VECTOR_STORE_PATH=data/chroma
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_RETRIEVAL_RESULTS=10
SIMILARITY_THRESHOLD=0.7

# Conversation
CONVERSATION_STORE=memory
CONVERSATION_HISTORY_MAX_MESSAGES=10
```

### Using Settings in Code

```python
from bs_assistant.config import settings

print(settings.DEFAULT_MODEL)      # "gpt-4o"
print(settings.TEMPERATURE)        # 0.7
print(settings.MAX_TOKENS)         # 2000
print(settings.VECTOR_STORE_PATH)  # Path("data/chroma")
```

---

## Full Chat Example (Coming Soon)

Once Phase 2-4 are complete, you'll be able to do:

```python
from bs_assistant.services.chat_service import ChatService
from bs_assistant.models import ChatRequest

# Initialize chat service
chat_service = ChatService()

# Create request
request = ChatRequest(
    message="Can you explain John 3:16 and give me related verses?",
    user_id="user123",
    language="en"
)

# Get response
response = chat_service.process_message(request)

print(response.response)  # Natural language response
print(response.model_used)  # "gpt-4o-mini"
print(response.cost_usd)  # 0.0023

# Retrieved resources used
for resource in response.retrieved_resources:
    print(f"{resource.type}: {resource.reference}")
```

---

## API Endpoints (Coming Soon)

Once Phase 4 is complete:

### POST /chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does Romans 8 say about the Spirit?",
    "user_id": "user123",
    "language": "en"
  }'
```

Response:
```json
{
  "response": "Romans 8 emphasizes the role of the Holy Spirit...",
  "session_id": "session-abc123",
  "retrieved_resources": [
    {
      "type": "verse",
      "content": "There is therefore now no condemnation...",
      "reference": "Romans 8:1",
      "score": 0.95
    }
  ],
  "model_used": "gpt-4o-mini",
  "tokens_used": 245,
  "cost_usd": 0.0018
}
```

### GET /health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "2.0.0"
}
```

---

## Running the Server (Coming Soon)

```bash
# Development
uvicorn bs_assistant.main:app --reload --port 8000

# Production
uvicorn bs_assistant.main:app --host 0.0.0.0 --port 8000
```

---

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_detectors.py

# Run with coverage
pytest --cov=bs_assistant
```

---

## Cost Optimization Tips

### 1. Use Model Selection

```python
# Simple queries - use cheaper model
if is_simple_query(message):
    model = "gpt-4o-mini"  # ~15x cheaper
else:
    model = "gpt-4o"
```

### 2. Cache Results

```python
# Cache identical queries
cache_key = hash(user_message + str(resources))
if cache_key in cache:
    return cache[cache_key]
```

### 3. Truncate Context

```python
# Keep only last N messages in history
if len(history) > settings.CONVERSATION_HISTORY_MAX_MESSAGES:
    history = history[-settings.CONVERSATION_HISTORY_MAX_MESSAGES:]
```

### 4. Monitor Costs

```python
from bs_assistant.core.llm import llm_client

# Track costs per session
total_cost = 0
for message in conversation:
    _, _, _, cost = llm_client.chat_completion(...)
    total_cost += cost

print(f"Total session cost: ${total_cost:.4f}")
```

---

## Comparison with v1

### Old Way (v1)
```python
# Complex intent routing
from bt_servant_engine.core.agentic import process_intent

intent = detect_intent(message)
if intent == "RETRIEVE_SCRIPTURE":
    response = handle_scripture(message)
elif intent == "SUMMARIZE":
    response = handle_summary(message)
# ... 10+ more intent handlers
```

### New Way (v2)
```python
# Simple conversational flow
from bs_assistant.services.chat_service import chat_service

response = chat_service.process_message(request)
# Automatically detects intent, retrieves resources, and responds
```

**Benefits:**
- ✅ 80% less code
- ✅ More natural conversations
- ✅ Handles multi-intent queries
- ✅ Similar or lower cost
- ✅ Easier to maintain

---

## Next Steps

1. **Now**: Use detectors and LLM client for experimentation
2. **Phase 2**: RAG retrieval will be added
3. **Phase 3**: Full chat service
4. **Phase 4**: API endpoints
5. **Phase 5+**: Special features (TTS, settings, etc.)

See `IMPLEMENTATION_ROADMAP.md` for detailed timeline.

---

## Getting Help

- **Roadmap**: `IMPLEMENTATION_ROADMAP.md`
- **Migration**: `MIGRATION_GUIDE.md`
- **Old Code**: Reference `previous/bt_servant_engine/`
- **Config**: Check `bs_assistant/config.py`

---

## Contributing

We're currently implementing Phase 2 (RAG). Check the roadmap for current priorities.

Priority areas:
1. Vector store integration
2. Retriever implementation
3. Bible data service
4. Cross-linking service

See the roadmap for where to start!