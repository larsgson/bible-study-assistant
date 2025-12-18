# Hosting Options for Bible Study Assistant Demo

## Overview

This document evaluates hosting platforms for deploying the Bible Study Assistant web API as a free or low-cost demo.

## System Requirements

- **Runtime:** Python 3.12+
- **Memory:** ~512MB-1GB (ChromaDB + FastAPI)
- **Storage:** ~20MB (Bible data + dependencies ~200MB)
- **External APIs:** OpenAI API (costs money per request)
- **Processing Time:** 10-14 seconds per query
- **Persistence Needs:** 
  - User state (JSON files)
  - Cache storage
  - ChromaDB vector database

## ⚠️ Critical Consideration: OpenAI API Costs

**The biggest challenge for a public demo is not hosting - it's OpenAI API costs!**

Every user query costs approximately:
- Input tokens: ~$0.002-0.01 per query
- Output tokens: ~$0.005-0.02 per query
- **Total: ~$0.01-0.03 per query**

A public demo without rate limiting could cost **hundreds of dollars per day** if abused.

**Recommended Mitigations:**
1. Set strict API rate limits (1-5 queries per user per hour)
2. Require user registration/authentication
3. Set OpenAI API spending limits ($10/day)
4. Monitor usage closely
5. Consider demo-only mode with canned responses

**See [COST_MITIGATION.md](COST_MITIGATION.md) for detailed implementation guides** including password protection, usage tokens, budget enforcement, and more.

---

## Hosting Platform Comparison

### 🥇 **Recommended: Fly.io** (Best Free Option)

**Free Tier:**
- 3 VMs with shared CPU (256MB RAM each)
- 3GB persistent volume storage
- No credit card required for free tier
- Doesn't sleep (always available)

**Pros:**
✅ Already configured (fly.toml exists)
✅ Persistent storage included
✅ No cold starts
✅ Generous free tier
✅ Docker-based (Dockerfile exists)
✅ Good for Python apps
✅ Environment variable management

**Cons:**
❌ 256MB RAM might be tight (need to monitor)
❌ Shared CPU performance
❌ Complex if scaling beyond free tier

**Setup Difficulty:** Medium (flyctl CLI required)

**Best For:** Production-ready demo with persistence

---

### 🥈 **Alternative: Render** (Easiest Setup)

**Free Tier:**
- 512MB RAM
- Sleeps after 15 minutes of inactivity
- 750 hours/month
- No persistent disk (free tier)

**Pros:**
✅ Very easy setup (GitHub integration)
✅ More RAM than Fly.io (512MB)
✅ Automatic deployments from Git
✅ Free SSL
✅ Environment variable management

**Cons:**
❌ Cold starts (15+ seconds to wake up)
❌ No persistent storage on free tier
❌ Sleeps when inactive (bad UX for demo)
❌ User state/cache lost on restart

**Setup Difficulty:** Easy (web-based)

**Best For:** Quick proof-of-concept without persistence

**Note:** Without persistent disk, ChromaDB and user state won't persist across restarts.

---

## Quick Comparison

| Feature | Fly.io | Render |
|---------|--------|--------|
| **Free RAM** | 256MB | 512MB |
| **Cold Starts** | No ❤️ | Yes 😢 |
| **Persistent Storage** | 3GB ✅ | No ❌ |
| **Setup Difficulty** | Medium | Easy |
| **Always On** | Yes | No (sleeps) |
| **Recommended For** | Demo with persistence | Quick POC |

---

## Cost Breakdown (Monthly)

| Platform | Hosting | OpenAI API (est) | Total |
|----------|---------|------------------|-------|
| **Fly.io (free)** | $0 | $10-50 | $10-50 |
| **Render (free)** | $0 | $10-50 | $10-50 |
| **Fly.io (paid)** | $10 | $10-50 | $20-60 |

**Note:** OpenAI costs dominate. With 100 queries/day at $0.02 each = $60/month.

---

## Deployment Guide: Fly.io

Since you already have `fly.toml` configured:

### Step 1: Install Fly CLI

```bash
# macOS
brew install flyctl

# Linux/WSL
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### Step 2: Login

```bash
flyctl auth login
```

### Step 3: Create App (if not exists)

```bash
flyctl apps create bt-servant
```

### Step 4: Create Persistent Volume

```bash
flyctl volumes create data --size 3 --region iad
```

### Step 5: Set Secrets

```bash
flyctl secrets set OPENAI_API_KEY=sk-...
flyctl secrets set LOG_PSEUDONYM_SECRET=$(openssl rand -hex 32)
```

### Step 6: Deploy

```bash
flyctl deploy
```

### Step 7: Monitor

```bash
flyctl logs
flyctl status
flyctl dashboard
```

### Step 8: Access

Your app will be available at: `https://bt-servant.fly.dev`

---

## Deployment Guide: Render

### Step 1: Push to GitHub

```bash
git push origin feature/web-chat-api
```

### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub

### Step 3: Create New Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select branch: `feature/web-chat-api`

### Step 4: Configure Service

- **Name:** bible-study-assistant
- **Environment:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn bt_servant_engine.api_factory:create_app --factory --host 0.0.0.0 --port $PORT`

### Step 5: Add Environment Variables

In Render dashboard, add:
```
OPENAI_API_KEY=sk-...
DATA_DIR=/app/data
BT_SERVANT_LOG_LEVEL=info
LOG_PSEUDONYM_SECRET=<random-secret>
```

### Step 6: Deploy

Click "Create Web Service" - Render will automatically deploy.

### Step 7: Access

Your app will be available at: `https://bible-study-assistant.onrender.com`

**Note:** First request will take 15+ seconds due to cold start after sleep.

---

## Required Environment Variables

For both platforms, you need:

```bash
OPENAI_API_KEY=sk-...                    # Required: OpenAI API key
DATA_DIR=/app/data                        # Optional: defaults to ./data
BT_SERVANT_LOG_LEVEL=info                # Optional: defaults to info
LOG_PSEUDONYM_SECRET=<random-hex>        # Required: for PII pseudonymization

# Not needed for web API (WhatsApp removed):
META_VERIFY_TOKEN=not_needed
META_WHATSAPP_TOKEN=not_needed
META_PHONE_NUMBER_ID=not_needed
META_APP_SECRET=not_needed
```

---

## Security Considerations

### 1. Rate Limiting (Critical!)

Without rate limiting, your OpenAI API costs could spiral out of control.

**Implementation with slowapi:**

Add to `requirements.txt`:
```
slowapi==0.1.9
```

Add to `bt_servant_engine/apps/api/app.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def create_app(services: ServiceContainer | None = None) -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    # ... rest of setup
```

Add to `bt_servant_engine/apps/api/routes/chat.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/", response_model=ChatResponse)
@limiter.limit("5/hour")  # 5 requests per hour per IP
async def chat_endpoint(...):
    # ... existing code
```

### 2. OpenAI API Limits

Set spending limits in OpenAI dashboard:
1. Go to https://platform.openai.com/account/limits
2. Set "Monthly budget" to $10 or $50
3. Enable "Email notification" at 75% and 100%

**For comprehensive cost protection strategies**, see **[COST_MITIGATION.md](COST_MITIGATION.md)** which includes:
- Password protection options
- Usage tokens/vouchers
- Daily budget enforcement
- Demo mode with canned responses
- Hybrid approaches

### 3. Input Validation

Already implemented in `ChatRequest` model:
- Maximum message length via `min_length=1`
- Pydantic validation for all inputs

### 4. Monitoring

Set up alerts for:
- High OpenAI API costs (>$10/day)
- Error rates (check `/health` endpoint)
- Response times (monitor logs)
- Memory usage (platform dashboards)

---

## Performance Optimization

### 1. Caching

Already implemented in `services/cache_manager.py`:
- Passage summaries cached by verse hash
- Intent classifications cached
- Reduces OpenAI API costs significantly

### 2. ChromaDB Persistence

For Fly.io (with persistent volume):
```python
# Already configured to use DATA_DIR
chroma_client = chromadb.PersistentClient(path=f"{DATA_DIR}/chromadb")
```

For Render (no persistence on free tier):
```python
# Falls back to in-memory (rebuilds on restart)
chroma_client = chromadb.Client()
```

### 3. Response Compression

Add to `bt_servant_engine/apps/api/app.py`:
```python
from fastapi.middleware.gzip import GZipMiddleware

def create_app(services: ServiceContainer | None = None) -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    # ... rest of setup
```

---

## Recommendation Summary

**For a reliable, always-on demo:**

🎯 **Use Fly.io**

**Reasons:**
1. Already configured (fly.toml exists)
2. Persistent storage included (ChromaDB, user state, caches persist)
3. No cold starts (10-14s queries are already slow, don't add more)
4. Free tier is sufficient for demo
5. Easy to upgrade if needed

**Steps:**
1. Add rate limiting (5 queries/hour per IP)
2. Set OpenAI spending limit ($10/day)
3. Deploy to Fly.io with commands above
4. Monitor usage for first week
5. Adjust limits based on usage

**Expected costs:** $10-30/month (mostly OpenAI API)

---

**For a quick proof-of-concept:**

🎯 **Use Render**

**Reasons:**
1. Easiest setup (GitHub integration)
2. No CLI required (web-based)
3. Automatic deployments on push
4. Good for testing before committing to infrastructure

**Trade-offs:**
- Cold starts (15+ seconds to wake)
- No persistence (state lost on restart)
- Sleeps after 15 minutes inactive

---

## Troubleshooting

### Fly.io

**App won't start:**
```bash
flyctl logs
# Check for errors in deployment
```

**Out of memory:**
```bash
# Upgrade to paid tier with more RAM
flyctl scale memory 1024
```

**Volume issues:**
```bash
flyctl volumes list
flyctl volumes delete <volume-id>
flyctl volumes create data --size 3
```

### Render

**Service keeps sleeping:**
- Upgrade to paid tier ($7/month for always-on)
- Or accept cold starts for free demo

**Build fails:**
```bash
# Check build logs in Render dashboard
# Verify requirements.txt is up to date
# Ensure Python 3.12 is specified
```

**Environment variables not set:**
- Go to dashboard → Environment tab
- Verify all required variables are present
- Redeploy after changes

---

## Next Steps

1. **Choose platform** (Fly.io recommended)
2. **Add rate limiting** (critical for cost control!)
3. **Set OpenAI API spending limits** in dashboard
4. **Deploy using guides above**
5. **Test with sample questions** from web interface
6. **Monitor costs** for first week
7. **Adjust rate limits** based on usage patterns
8. **Consider authentication** if abuse occurs

---

## Questions Before Deploying

Consider:

1. **Who is the audience?** (public, specific users, demo only)
2. **Expected traffic?** (10 users/day? 100? 1000?)
3. **Budget?** (truly free, or $10-50/month acceptable?)
4. **Persistence needed?** (user history, caching important?)
5. **Uptime requirements?** (cold starts acceptable?)

**Recommendation Matrix:**

| Your Need | Choose |
|-----------|--------|
| Quick POC | Render |
| Reliable demo with persistence | Fly.io |
| Lowest cost with cold starts OK | Render |
| Best UX (no cold starts) | Fly.io |
| Easiest setup | Render |
| Production-ready | Fly.io |

---

**Ready to deploy?** The Dockerfile and fly.toml are already configured. Just follow the Fly.io deployment guide above!

**Don't forget:** Review [COST_MITIGATION.md](COST_MITIGATION.md) for essential cost protection strategies before making your deployment public.