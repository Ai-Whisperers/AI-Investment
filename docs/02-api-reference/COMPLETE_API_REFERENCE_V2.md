# Waardhaven AutoIndex - Complete API Reference v2.0
*Last Updated: 2025-01-24*

## 📡 API Overview

**Base URL**: `https://api.waardhaven-autoindex.com/api/v1`  
**Authentication**: JWT Bearer Token  
**Content-Type**: `application/json`  
**Total Endpoints**: 150+

## 🔐 Authentication Endpoints

### POST `/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

### POST `/auth/login`
Authenticate and receive JWT tokens.

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### GET `/auth/me`
Get current user information.

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

### POST `/auth/refresh`
Refresh access token.

### POST `/auth/logout`
Logout and invalidate tokens.

### GET `/auth/google`
Initiate Google OAuth flow.

### POST `/auth/google/callback`
Handle Google OAuth callback.

---

## 🚀 Extreme Alpha Detection Endpoints

### GET `/extreme/signals/live`
Get live high-confidence signals for immediate action.

**Query Parameters:**
- `confidence_min` (float): Minimum confidence threshold (default: 0.7)
- `signal_type` (string): Filter by signal type

**Response:** `200 OK`
```json
[
  {
    "ticker": "GME",
    "action": "STRONG_BUY",
    "confidence": 0.92,
    "expected_return": 0.45,
    "timeframe": "48_hours",
    "signal_type": "extreme",
    "sources": ["reddit_wsb", "4chan_biz"],
    "pattern_stack": ["volume_spike", "momentum_surge", "short_squeeze"],
    "created_at": "2025-01-24T10:00:00Z"
  }
]
```

### POST `/extreme/detect/alpha`
Detect alpha events using multi-layer pattern recognition.

**Request Body:**
```json
{
  "ticker": "AMC",
  "current_mentions": 5000,
  "avg_mentions": 500,
  "institutional_sentiment": 0.3,
  "retail_sentiment": 0.9
}
```

### GET `/extreme/meme/velocity/{ticker}`
Get meme velocity metrics for a ticker.

**Response:** `200 OK`
```json
{
  "ticker": "GME",
  "velocity": 5.2,
  "acceleration": 2.8,
  "virality_score": 85,
  "expected_move": "150%",
  "timeframe": "1 week",
  "platforms": ["reddit_wsb", "tiktok", "twitter"],
  "mention_count": 10000,
  "sentiment": 0.85
}
```

### GET `/extreme/meme/trending`
Get top trending meme stocks by velocity.

**Query Parameters:**
- `limit` (int): Number of results (default: 10)

### GET `/extreme/backtest/validate`
Run backtest to validate >30% return capability.

**Query Parameters:**
- `starting_capital` (float): Starting capital (default: 100000)

**Response:** `200 OK`
```json
{
  "starting_capital": 100000,
  "ending_capital": 245000,
  "total_return": "145%",
  "annualized_return": "42%",
  "win_rate": "73%",
  "sharpe_ratio": 2.1,
  "max_drawdown": "14%"
}
```

### GET `/extreme/squeeze/candidates`
Get potential short squeeze candidates.

### POST `/extreme/collect/signals`
Manually trigger signal collection.

### GET `/extreme/opportunities/extreme`
Get extreme opportunities with >50% expected returns.

### GET `/extreme/asymmetry/early`
Get early signals with 48-72 hour lead time.

### GET `/extreme/portfolio/recommendations`
Get portfolio allocation recommendations for maximum alpha.

---

## 📊 Investment Analysis Endpoints

### GET `/investment/analyze`
Get comprehensive investment analysis for a ticker.

**Query Parameters:**
- `ticker` (string): Stock ticker symbol
- `include_technical` (bool): Include technical analysis
- `include_fundamental` (bool): Include fundamental analysis

**Response:** `200 OK`
```json
{
  "ticker": "AAPL",
  "recommendation": "BUY",
  "confidence": 0.78,
  "signals": {
    "technical": 0.65,
    "fundamental": 0.82,
    "sentiment": 0.74,
    "momentum": 0.71
  },
  "target_price": 195.50,
  "stop_loss": 165.00,
  "expected_return": 0.22
}
```

### GET `/investment/screen`
Screen for investment opportunities.

### POST `/investment/backtest`
Backtest an investment strategy.

### GET `/investment/recommendations`
Get personalized investment recommendations.

### GET `/investment/risk-assessment`
Assess portfolio risk.

### GET `/investment/opportunities`
Find investment opportunities based on criteria.

---

## 📈 Technical Analysis Endpoints

### GET `/analysis/technical/{ticker}`
Get technical indicators for a ticker.

**Response:** `200 OK`
```json
{
  "ticker": "TSLA",
  "indicators": {
    "rsi": 65.4,
    "macd": {
      "macd": 12.5,
      "signal": 10.2,
      "histogram": 2.3
    },
    "bollinger_bands": {
      "upper": 285.0,
      "middle": 270.0,
      "lower": 255.0
    },
    "sma_50": 268.5,
    "sma_200": 245.0
  },
  "signals": {
    "trend": "bullish",
    "momentum": "strong",
    "overbought": false
  }
}
```

### GET `/analysis/fundamental/{ticker}`
Get fundamental analysis for a ticker.

### GET `/analysis/sentiment/{ticker}`
Get sentiment analysis from news and social media.

### GET `/analysis/support-resistance/{ticker}`
Get support and resistance levels.

### GET `/analysis/pattern/{ticker}`
Detect chart patterns.

### POST `/analysis/custom`
Run custom analysis with specific parameters.

### GET `/analysis/correlation`
Analyze correlation between assets.

### GET `/analysis/sector/{sector}`
Analyze sector performance and trends.

---

## 🔔 Signal Detection Endpoints

### GET `/signals/agro-robotics`
Get agriculture robotics investment signals.

### GET `/signals/regulatory`
Get regulatory change signals.

### GET `/signals/supply-chain`
Get supply chain disruption signals.

### GET `/signals/insider`
Detect insider trading patterns.

### GET `/signals/momentum`
Get momentum signals.

### GET `/signals/reversal`
Get reversal signals.

### GET `/signals/breakout`
Get breakout signals.

### GET `/signals/volume`
Get unusual volume signals.

### GET `/signals/options`
Get unusual options activity.

### GET `/signals/social`
Get social sentiment signals.

### GET `/signals/news`
Get news-based signals.

### GET `/signals/cross-asset`
Get cross-asset correlation signals.

### GET `/signals/macro`
Get macroeconomic signals.

### GET `/signals/seasonal`
Get seasonal pattern signals.

---

## 🏃 Momentum Tracking Endpoints

### GET `/momentum/stocks`
Get momentum stocks.

### GET `/momentum/sectors`
Get sector momentum.

### GET `/momentum/indicators`
Get momentum indicators.

### GET `/momentum/score/{ticker}`
Get momentum score for a ticker.

### GET `/momentum/accelerating`
Get stocks with accelerating momentum.

### GET `/momentum/decelerating`
Get stocks with decelerating momentum.

### GET `/momentum/rotation`
Detect sector rotation.

### GET `/momentum/breadth`
Get market breadth indicators.

### GET `/momentum/strength`
Get relative strength rankings.

### GET `/momentum/divergence`
Detect momentum divergences.

### GET `/momentum/oscillators`
Get momentum oscillator readings.

### GET `/momentum/flow`
Get money flow indicators.

### GET `/momentum/volume`
Get volume momentum.

### GET `/momentum/sentiment`
Get sentiment momentum.

### GET `/momentum/institutional`
Get institutional momentum.

---

## 🔄 Integrated Signals Endpoints

### GET `/integrated/real-time`
Get real-time integrated signals.

### GET `/integrated/fusion`
Get multi-source signal fusion.

### GET `/integrated/confidence`
Get high-confidence integrated signals.

### GET `/integrated/alerts`
Get signal alerts.

### GET `/integrated/summary`
Get signal summary dashboard.

### GET `/integrated/trends`
Get trending signals across sources.

### GET `/integrated/anomalies`
Detect signal anomalies.

### GET `/integrated/correlations`
Get signal correlations.

### GET `/integrated/predictions`
Get signal-based predictions.

---

## 💼 Portfolio Management Endpoints

### GET `/portfolio/holdings`
Get current portfolio holdings.

### POST `/portfolio/optimize`
Optimize portfolio allocation.

### GET `/portfolio/performance`
Get portfolio performance metrics.

### POST `/portfolio/rebalance`
Rebalance portfolio.

### GET `/portfolio/risk`
Get portfolio risk metrics.

### GET `/portfolio/allocation`
Get current allocation.

### POST `/portfolio/simulate`
Simulate portfolio changes.

### GET `/portfolio/history`
Get portfolio history.

---

## 📊 Asset Management Endpoints

### GET `/assets/list`
Get list of available assets.

### GET `/assets/{symbol}`
Get asset details.

### POST `/assets/classify`
Classify assets by criteria.

### GET `/assets/screener`
Screen assets by filters.

### GET `/assets/compare`
Compare multiple assets.

### GET `/assets/correlation`
Get asset correlations.

### GET `/assets/fundamentals/{symbol}`
Get asset fundamentals.

---

## 📰 News Endpoints

### GET `/news/latest`
Get latest news.

### GET `/news/sentiment`
Get news sentiment analysis.

### GET `/news/trending`
Get trending news topics.

### GET `/news/alerts`
Get news alerts.

### GET `/news/{ticker}`
Get news for specific ticker.

---

## 📈 Strategy Endpoints

### GET `/strategy/list`
Get available strategies.

### POST `/strategy/create`
Create custom strategy.

### GET `/strategy/{id}/performance`
Get strategy performance.

### POST `/strategy/backtest`
Backtest a strategy.

### PUT `/strategy/{id}`
Update strategy parameters.

### DELETE `/strategy/{id}`
Delete a strategy.

---

## 🎯 Benchmark Endpoints

### GET `/benchmark/sp500`
Get S&P 500 comparison.

### GET `/benchmark/custom`
Compare against custom benchmark.

### GET `/benchmark/metrics`
Get benchmark metrics.

### GET `/benchmark/correlation`
Get correlation with benchmarks.

---

## 🩺 System Endpoints

### GET `/diagnostics/health`
Get system health status.

### GET `/diagnostics/cache`
Get cache status.

### GET `/diagnostics/database`
Get database status.

### GET `/diagnostics/api`
Get API performance metrics.

### GET `/diagnostics/errors`
Get recent errors.

### GET `/diagnostics/usage`
Get usage statistics.

---

## 🔄 Background Tasks Endpoints

### POST `/tasks/create`
Create background task.

### GET `/tasks/{id}/status`
Get task status.

### GET `/tasks/list`
List running tasks.

### DELETE `/tasks/{id}`
Cancel a task.

---

## 🛠️ Manual Operations Endpoints

### POST `/manual/refresh`
Manually trigger data refresh.

### POST `/manual/recalculate`
Recalculate metrics.

### POST `/manual/cleanup`
Run cleanup operations.

---

## 📊 Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

## 🔒 Rate Limiting

- **Default**: 100 requests per minute
- **Authenticated**: 500 requests per minute
- **Premium**: 2000 requests per minute

## 🔄 Pagination

Most list endpoints support pagination:

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
- `sort` (string): Sort field
- `order` (string): Sort order (asc/desc)

**Response Headers:**
- `X-Total-Count`: Total number of items
- `X-Page`: Current page
- `X-Per-Page`: Items per page

## 🔍 Filtering

List endpoints support filtering:

**Query Parameters:**
- `filter[field]`: Filter by field value
- `filter[field][operator]`: Use operator (gt, lt, gte, lte, ne, in)

**Example:**
```
GET /api/v1/signals/live?filter[confidence][gte]=0.8&filter[ticker][in]=GME,AMC
```

## 📦 Batch Operations

Some endpoints support batch operations:

### POST `/batch`
Execute multiple API calls in one request.

**Request Body:**
```json
{
  "requests": [
    {
      "method": "GET",
      "url": "/extreme/signals/live"
    },
    {
      "method": "GET",
      "url": "/momentum/trending"
    }
  ]
}
```

## 🔔 WebSocket Endpoints

### WS `/ws/signals`
Real-time signal stream.

### WS `/ws/prices`
Real-time price updates.

### WS `/ws/news`
Real-time news feed.

## 📝 API Versioning

The API uses URL versioning:
- Current version: `/api/v1/`
- Legacy support: `/api/v0/` (deprecated)

## 🚀 Quick Start Example

```python
import requests

# 1. Register
response = requests.post(
    "https://api.waardhaven-autoindex.com/api/v1/auth/register",
    json={
        "email": "user@example.com",
        "password": "SecurePassword123!",
        "full_name": "John Doe"
    }
)

# 2. Login
response = requests.post(
    "https://api.waardhaven-autoindex.com/api/v1/auth/login",
    data={
        "username": "user@example.com",
        "password": "SecurePassword123!"
    }
)
token = response.json()["access_token"]

# 3. Get signals
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "https://api.waardhaven-autoindex.com/api/v1/extreme/signals/live",
    headers=headers
)
signals = response.json()

# 4. Get recommendations
response = requests.get(
    "https://api.waardhaven-autoindex.com/api/v1/extreme/portfolio/recommendations",
    headers=headers,
    params={"capital": 100000}
)
recommendations = response.json()
```

## 📚 SDKs

Official SDKs available:
- Python: `pip install waardhaven-autoindex`
- JavaScript: `npm install @waardhaven/autoindex`
- Go: `go get github.com/waardhaven/autoindex-go`

## 🆘 Support

- **Documentation**: https://docs.waardhaven-autoindex.com
- **API Status**: https://status.waardhaven-autoindex.com
- **Support Email**: support@waardhaven-autoindex.com
- **Discord**: https://discord.gg/waardhaven

---

*This API reference covers all 150+ endpoints of the Waardhaven AutoIndex platform. For detailed examples and integration guides, please refer to the full documentation.*