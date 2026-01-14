# API Endpoints - Bible Study Assistant v2.0

## 📍 Available Endpoints

### v2.0 (New) Endpoints

All endpoints are available at: `http://localhost:8000`

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/` | Root info with version and endpoints | ✅ |
| GET | `/health` | Health check with dependency status | ✅ |
| GET | `/ready` | Kubernetes readiness probe | ✅ |
| GET | `/live` | Kubernetes liveness probe | ✅ |
| GET | `/docs` | Interactive API documentation (Swagger) | ✅ |
| GET | `/redoc` | Alternative API documentation (ReDoc) | ✅ |
| POST | `/chat` | Main conversational chat endpoint | ✅ |
| POST | `/chat/clear` | Clear conversation history | ✅ |
| GET | `/chat/sessions/{user_id}` | List user sessions | ✅ |
| GET | `/chat/history/{user_id}` | Get conversation history | ✅ |

### v1.0 (Legacy) Compatibility

For backward compatibility, the old v1 endpoint is still available:

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/api/chat` | Legacy chat endpoint (redirects to `/chat`) | ✅ Compat |

---

## 🔄 Migration Guide: v1 → v2

### What Changed

**Old (v1):**
```
POST /api/chat
```

**New (v2):**
```
POST /chat
```

### Backward Compatibility

✅ **Good News:** Both endpoints work! We've added backward compatibility.

- `/api/chat` still works (redirects to new endpoint)
- `/chat` is the new, preferred endpoint

### Recommended Migration

**Option 1: No changes needed**
- Keep using `/api/chat` - it still works!
- No urgency to migrate

**Option 2: Update to new endpoint (recommended)**
```bash
# Old
curl -X POST http://localhost:8000/api/chat

# New
curl -X POST http://localhost:8000/chat
```

---

## 📝 Request/Response Format

### POST /chat (or /api/chat)

**Request Body:**
```json
{
  "message": "What does John 3:16 mean?",
  "user_id": "user123",
  "language": "en",
  "session_id": "optional-session-id",
  "translation_id": "bsb"
}
```

**Required Fields:**
- `message` (string): The user's question or message
- `user_id` (string): Unique user identifier
- `language` (string): Language code (e.g., "en", "fr", "id")

**Optional Fields:**
- `session_id` (string): Session identifier for conversation continuity
- `translation_id` (string): Bible translation ID (default: "bsb")

**Response:**
```json
{
  "response": "John 3:16 is one of the most well-known verses...",
  "session_id": "session-user123-20260113120000",
  "retrieved_resources": [
    {
      "type": "verse",
      "content": "For God so loved the world...",
      "reference": "John 3:16",
      "score": 1.0,
      "metadata": {
        "book": "John",
        "chapter": 3,
        "verse": 16,
        "translation": "bsb",
        "language": "en"
      }
    }
  ],
  "model_used": "gpt-4o-mini",
  "tokens_used": 565,
  "cost_usd": 0.00013695
}
```

**Response Fields:**
- `response` (string): Natural language response from the assistant
- `session_id` (string): Session identifier for this conversation
- `retrieved_resources` (array): Resources retrieved via RAG
- `model_used` (string): LLM model used (gpt-4o or gpt-4o-mini)
- `tokens_used` (integer): Total tokens consumed
- `cost_usd` (float): Cost in USD for this request

---

## 🔍 Other Endpoints

### GET /health

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-13T12:00:00Z",
  "version": "2.0.0"
}
```

### POST /chat/clear

**Request:**
```bash
curl -X POST "http://localhost:8000/chat/clear?user_id=user123&session_id=session-abc"
```

**Response:**
```json
{
  "status": "success",
  "message": "Conversation history cleared"
}
```

### GET /chat/sessions/{user_id}

**Request:**
```bash
curl http://localhost:8000/chat/sessions/user123
```

**Response:**
```json
{
  "user_id": "user123",
  "sessions": {
    "session-abc": {
      "message_count": 10,
      "first_timestamp": "2026-01-13T10:00:00",
      "last_timestamp": "2026-01-13T12:00:00"
    }
  }
}
```

### GET /chat/history/{user_id}

**Request:**
```bash
curl "http://localhost:8000/chat/history/user123?session_id=session-abc&limit=10"
```

**Response:**
```json
{
  "user_id": "user123",
  "session_id": "session-abc",
  "history": [
    {
      "role": "user",
      "content": "What does John 3:16 mean?"
    },
    {
      "role": "assistant",
      "content": "John 3:16 is one of the most well-known verses..."
    }
  ],
  "count": 2
}
```

---

## 📊 Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error: message is required"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "Error processing message: [error details]"
}
```

---

## 🧪 Testing Examples

### cURL Examples

**Simple verse request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me John 3:16",
    "user_id": "test_user",
    "language": "en"
  }'
```

**Complex question:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does Romans 8:28 mean and how should I translate it?",
    "user_id": "translator_001",
    "language": "en",
    "translation_id": "bsb"
  }'
```

**With session continuity:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you explain more about that?",
    "user_id": "test_user",
    "session_id": "session-123",
    "language": "en"
  }'
```

### Python Example

```python
import requests

# Make chat request
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "What does John 3:16 mean?",
        "user_id": "user123",
        "language": "en"
    }
)

data = response.json()
print(f"Response: {data['response']}")
print(f"Cost: ${data['cost_usd']:.6f}")
print(f"Model: {data['model_used']}")
```

### JavaScript Example

```javascript
// Make chat request
fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'What does John 3:16 mean?',
    user_id: 'user123',
    language: 'en'
  })
})
.then(response => response.json())
.then(data => {
  console.log('Response:', data.response);
  console.log('Cost:', data.cost_usd);
  console.log('Model:', data.model_used);
});
```

---

## 🚀 Quick Reference

### Most Common Use Cases

**1. Simple verse lookup:**
```bash
POST /chat
{"message": "Show me Romans 8:28", "user_id": "user1", "language": "en"}
```

**2. Question about passage:**
```bash
POST /chat
{"message": "What does this verse mean?", "user_id": "user1", "language": "en"}
```

**3. Translation help:**
```bash
POST /chat
{"message": "How should I translate 'grace' in Ephesians 2:8?", "user_id": "translator1", "language": "en"}
```

**4. Check server health:**
```bash
GET /health
```

---

## 📚 Interactive Documentation

For interactive API testing and complete documentation, visit:

**Swagger UI:** http://localhost:8000/docs
- Interactive interface to test endpoints
- Try out requests directly in the browser
- See request/response schemas

**ReDoc:** http://localhost:8000/redoc
- Clean, readable documentation
- Better for reference and reading

---

## 🎯 Summary

### Key Points

✅ **New endpoint:** `/chat` (preferred)
✅ **Old endpoint:** `/api/chat` (still works for compatibility)
✅ **No breaking changes:** Both endpoints return the same response format
✅ **New features:** Cost tracking, model selection, session management
✅ **Better performance:** 2-3x faster than v1
✅ **Lower cost:** Up to 30x cheaper per query

### Migration Checklist

- [ ] Test your application with new endpoint `/chat`
- [ ] Verify response format matches expectations
- [ ] Update client code to use `/chat` (optional but recommended)
- [ ] Remove `/api` prefix from endpoint URLs
- [ ] Update any documentation or examples
- [ ] Consider using new features (session management, cost tracking)

**No rush to migrate - both endpoints work!** 🎉