# Cost Mitigation Strategies for Fly.io Deployment

This guide provides practical strategies to control OpenAI API costs when deploying the Bible Study Assistant on Fly.io or similar platforms.

---

## 🚨 The Cost Problem

**Without protection, costs can spiral quickly:**
- Each query: ~$0.01-0.03
- 100 queries/day: ~$2/day = $60/month
- 1000 queries/day: ~$20/day = $600/month
- **Public abuse**: Could cost hundreds in hours

**Primary defense: Multiple layers of protection**

---

## 🔐 Strategy 1: Simple Password Protection (Recommended for Demos)

Add a simple password requirement before the chat interface loads.

### Implementation

Create `static/password.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bible Study Assistant - Access</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        .access-container {
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 400px;
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 20px; }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e6ed;
            border-radius: 8px;
            font-size: 16px;
            margin-bottom: 20px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            font-weight: 600;
        }
        .error { color: #c33; margin-top: 10px; display: none; }
    </style>
</head>
<body>
    <div class="access-container">
        <h1>📖 Bible Study Assistant</h1>
        <p>Enter access code to continue</p>
        <input type="password" id="passwordInput" placeholder="Access code">
        <button onclick="checkPassword()">Access</button>
        <p class="error" id="error">Incorrect access code</p>
    </div>
    <script>
        const ACCESS_CODE = 'demo2025'; // Change this!
        
        function checkPassword() {
            const input = document.getElementById('passwordInput').value;
            if (input === ACCESS_CODE) {
                sessionStorage.setItem('authenticated', 'true');
                window.location.href = '/static/index.html';
            } else {
                document.getElementById('error').style.display = 'block';
            }
        }
        
        document.getElementById('passwordInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') checkPassword();
        });
    </script>
</body>
</html>
```

Update `static/index.html` - add at top of `<script>` section:

```javascript
// Check authentication
if (!sessionStorage.getItem('authenticated')) {
    window.location.href = '/static/password.html';
}
```

Update `bt_servant_engine/apps/api/app.py` root redirect:

```python
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/password.html")
```

**Pros:** Simple, no backend changes needed  
**Cons:** Password is in JavaScript (visible in source), not cryptographically secure  
**Best for:** Controlled demos with known users

---

## 🔐 Strategy 2: HTTP Basic Authentication (More Secure)

Use Fly.io secrets and HTTP Basic Auth.

### Implementation

Add to `bt_servant_engine/apps/api/app.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def verify_access(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials."""
    correct_username = secrets.compare_digest(
        credentials.username, config.DEMO_USERNAME or "demo"
    )
    correct_password = secrets.compare_digest(
        credentials.password, config.DEMO_PASSWORD or "changeme"
    )
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
```

Add to `bt_servant_engine/core/config.py`:

```python
DEMO_USERNAME: str = Field(default="demo", description="Demo username")
DEMO_PASSWORD: str = Field(default="changeme", description="Demo password")
```

Apply to chat endpoint in `bt_servant_engine/apps/api/routes/chat.py`:

```python
@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    services: ServiceContainer = Depends(get_service_container),
    username: str = Depends(verify_access),  # Add this
) -> ChatResponse:
    # ... existing code
```

Set on Fly.io:

```bash
flyctl secrets set DEMO_USERNAME=mysecretuser
flyctl secrets set DEMO_PASSWORD=mysecretpass123
```

**Pros:** Secure, browser handles auth, proper HTTP standard  
**Cons:** Browser password dialog not pretty, credentials travel with every request  
**Best for:** Internal demos, trusted users

---

## 🎟️ Strategy 3: Usage Tokens/Vouchers

Give users limited-use tokens.

### Implementation

Add to `data/tokens.json`:

```json
{
  "demo-token-001": {"queries_remaining": 10, "created": "2025-01-15"},
  "demo-token-002": {"queries_remaining": 5, "created": "2025-01-15"}
}
```

Create `bt_servant_engine/services/token_manager.py`:

```python
import json
from pathlib import Path
from typing import Optional

class TokenManager:
    def __init__(self, token_file: str = "data/tokens.json"):
        self.token_file = Path(token_file)
        self._load_tokens()
    
    def _load_tokens(self):
        if self.token_file.exists():
            with open(self.token_file, 'r') as f:
                self.tokens = json.load(f)
        else:
            self.tokens = {}
    
    def _save_tokens(self):
        with open(self.token_file, 'w') as f:
            json.dump(self.tokens, f, indent=2)
    
    def validate_and_consume(self, token: str) -> bool:
        """Check if token is valid and has queries remaining."""
        if token not in self.tokens:
            return False
        
        if self.tokens[token]["queries_remaining"] <= 0:
            return False
        
        self.tokens[token]["queries_remaining"] -= 1
        self._save_tokens()
        return True
    
    def get_remaining(self, token: str) -> Optional[int]:
        """Get remaining queries for a token."""
        if token not in self.tokens:
            return None
        return self.tokens[token]["queries_remaining"]
```

Update chat endpoint:

```python
from bt_servant_engine.services.token_manager import TokenManager

token_manager = TokenManager()

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    token: str = Header(None, alias="X-Access-Token"),
    services: ServiceContainer = Depends(get_service_container),
) -> ChatResponse:
    if not token or not token_manager.validate_and_consume(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired access token"
        )
    
    # ... rest of code
```

**Pros:** Fine-grained control, easy to distribute, trackable  
**Cons:** Requires backend changes, token management overhead  
**Best for:** Conference demos, limited beta access

---

## 🚦 Strategy 4: Rate Limiting (Essential for All Deployments)

Limit requests per IP/user/timeframe.

### Implementation with slowapi

Already documented in `HOSTING_OPTIONS.md`, but here's the complete setup:

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
    
    # Add rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # ... rest of setup
```

Add to chat endpoint:

```python
@router.post("/", response_model=ChatResponse)
@limiter.limit("5/hour")  # 5 requests per hour per IP
async def chat_endpoint(
    request: ChatRequest,
    services: ServiceContainer = Depends(get_service_container),
) -> ChatResponse:
    # ... existing code
```

**Recommended limits:**
- **Aggressive:** 3/hour (demo)
- **Moderate:** 10/hour (beta)
- **Generous:** 30/hour (production)

**Pros:** Essential baseline protection, prevents abuse  
**Cons:** Can frustrate legitimate users if too strict  
**Best for:** EVERY public deployment

---

## 💰 Strategy 5: Cost Budget Enforcement

Auto-shutdown when budget exceeded.

### Implementation

Create `bt_servant_engine/services/cost_tracker.py`:

```python
from datetime import datetime, timedelta
from pathlib import Path
import json

class CostTracker:
    def __init__(self, daily_budget: float = 10.0):
        self.daily_budget = daily_budget
        self.cost_file = Path("data/daily_costs.json")
        self._load_costs()
    
    def _load_costs(self):
        if self.cost_file.exists():
            with open(self.cost_file, 'r') as f:
                self.costs = json.load(f)
        else:
            self.costs = {}
    
    def _save_costs(self):
        with open(self.cost_file, 'w') as f:
            json.dump(self.costs, f, indent=2)
    
    def add_cost(self, amount: float):
        """Add cost for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.costs:
            self.costs[today] = 0.0
        self.costs[today] += amount
        self._save_costs()
    
    def get_today_cost(self) -> float:
        """Get total cost for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.costs.get(today, 0.0)
    
    def budget_exceeded(self) -> bool:
        """Check if daily budget exceeded."""
        return self.get_today_cost() >= self.daily_budget
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget for today."""
        return max(0, self.daily_budget - self.get_today_cost())
```

Add to chat endpoint:

```python
from bt_servant_engine.services.cost_tracker import CostTracker

cost_tracker = CostTracker(daily_budget=10.0)  # $10/day limit

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    services: ServiceContainer = Depends(get_service_container),
) -> ChatResponse:
    # Check budget first
    if cost_tracker.budget_exceeded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Daily budget exceeded. Please try again tomorrow."
        )
    
    # ... process request
    
    # Estimate and track cost (rough estimate)
    estimated_cost = 0.02  # ~$0.02 per query
    cost_tracker.add_cost(estimated_cost)
    
    return response
```

**Pros:** Hard limit prevents runaway costs  
**Cons:** Service unavailable when budget hit  
**Best for:** Strict budget constraints

---

## 📊 Strategy 6: Usage Dashboard & Monitoring

Track and visualize usage patterns.

### Implementation

Add admin endpoint in `bt_servant_engine/apps/api/routes/admin_usage.py`:

```python
from fastapi import APIRouter, Depends
from bt_servant_engine.apps.api.dependencies import require_healthcheck_token
from bt_servant_engine.services.cost_tracker import CostTracker
from bt_servant_engine.services.token_manager import TokenManager

router = APIRouter(prefix="/admin/usage", tags=["admin"])

@router.get("/today")
async def get_today_usage(_: None = Depends(require_healthcheck_token)):
    """Get today's usage statistics."""
    tracker = CostTracker()
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "cost": tracker.get_today_cost(),
        "budget": tracker.daily_budget,
        "remaining": tracker.get_remaining_budget(),
        "percentage_used": (tracker.get_today_cost() / tracker.daily_budget) * 100
    }

@router.get("/week")
async def get_week_usage(_: None = Depends(require_healthcheck_token)):
    """Get this week's usage."""
    tracker = CostTracker()
    # Implement week aggregation
    pass
```

**Pros:** Visibility into usage patterns  
**Cons:** Requires admin token, manual monitoring  
**Best for:** Active cost management

---

## 🎮 Strategy 7: Demo Mode (Canned Responses)

Provide free tier with canned responses for common questions.

### Implementation

Create `data/demo_responses.json`:

```json
{
  "summarize titus 1": {
    "response": "Titus 1 begins with Paul's greeting...",
    "cached": true
  },
  "show john 3:16": {
    "response": "For God so loved the world...",
    "cached": true
  }
}
```

Add demo mode check:

```python
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

if DEMO_MODE:
    # Check for canned response
    canned = get_canned_response(request.message.lower())
    if canned:
        return ChatResponse(
            responses=[ChatMessageResponse(content=canned, type="text")],
            # ... metadata
        )

# Otherwise use real OpenAI
```

**Pros:** Zero cost for demos, instant responses  
**Cons:** Limited to predefined questions  
**Best for:** Public demos, trade shows

---

## 🔄 Strategy 8: Hybrid Approach (Recommended)

Combine multiple strategies for best protection.

### Recommended Stack

**Layer 1: Rate Limiting**
- 5 queries/hour per IP (base protection)

**Layer 2: Simple Password**
- Password protection on demo (share with users)

**Layer 3: Daily Budget**
- $10/day hard limit with auto-shutdown

**Layer 4: Monitoring**
- Daily email alerts at 50% and 80% budget

**Layer 5: OpenAI Dashboard Limit**
- Set $50/month hard limit in OpenAI dashboard

### Configuration

```bash
# Fly.io secrets
flyctl secrets set OPENAI_API_KEY=sk-...
flyctl secrets set DEMO_PASSWORD=MySecret123
flyctl secrets set DAILY_BUDGET=10.0
flyctl secrets set ALERT_EMAIL=your@email.com
```

---

## 📈 Cost Estimation

### Calculate Your Budget

**Per Query Costs:**
- Simple retrieval: ~$0.01
- Passage summary: ~$0.02
- Complex RAG: ~$0.03

**Monthly Estimates:**
- 5 queries/day: ~$3/month
- 20 queries/day: ~$12/month
- 100 queries/day: ~$60/month
- 500 queries/day: ~$300/month

**Fly.io is FREE, OpenAI is the cost!**

---

## ✅ Implementation Checklist

For a secure demo deployment:

- [ ] Add password protection (Strategy 1 or 2)
- [ ] Implement rate limiting (Strategy 4) - 5/hour
- [ ] Set daily budget limit (Strategy 5) - $10/day
- [ ] Set OpenAI API hard limit - $50/month
- [ ] Add usage monitoring (Strategy 6)
- [ ] Share password only with intended users
- [ ] Monitor costs daily for first week
- [ ] Adjust limits based on actual usage

---

## 🚨 Emergency: Costs Too High?

**Immediate actions:**

1. **Pause the app:**
   ```bash
   flyctl scale count 0
   ```

2. **Check OpenAI usage:**
   - https://platform.openai.com/usage

3. **Revoke compromised credentials:**
   - Generate new DEMO_PASSWORD
   - Rotate OpenAI API key if exposed

4. **Add stricter limits:**
   - Reduce rate limit to 3/hour
   - Lower daily budget to $5
   - Require tokens (Strategy 3)

5. **Resume with protection:**
   ```bash
   flyctl scale count 1
   ```

---

## 💡 Best Practices

1. **Start restrictive, loosen later**
   - Begin with 3/hour limit
   - Increase based on legitimate usage

2. **Monitor first week closely**
   - Check costs daily
   - Adjust limits as needed

3. **Use multiple layers**
   - Don't rely on single protection
   - Defense in depth

4. **Communicate limits**
   - Tell users about rate limits
   - Set expectations

5. **Keep password private**
   - Don't post publicly
   - Share only with intended users

6. **Use Fly.io for free hosting**
   - Hosting is free
   - Only pay for OpenAI API

---

## 🔗 Related Documentation

- [HOSTING_OPTIONS.md](HOSTING_OPTIONS.md) - Deployment guide
- [OpenAI Usage Dashboard](https://platform.openai.com/usage) - Track API costs
- [Fly.io Pricing](https://fly.io/docs/about/pricing/) - Hosting costs

---

**Recommendation for Demo:** Use Strategy 1 (Simple Password) + Strategy 4 (Rate Limiting 5/hour) + OpenAI API limit ($10/month). This provides good protection with minimal complexity.

**Cost estimate with this setup:** $0-10/month depending on usage.