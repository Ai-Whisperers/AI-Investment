---
title: API Cheatsheet
category: Quick Reference
priority: 1
status: stable
last-updated: 2025-01-19
owner: backend-team
---

# 📘 API Quick Reference Cheatsheet

## 🔐 Authentication
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

# Use Token
export TOKEN="eyJ..."
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/auth/me
```

## 📊 Portfolio Management
```bash
# Get Index Values
GET /api/v1/index/values?start_date=2024-01-01&limit=100

# Get Current Portfolio
GET /api/v1/index/current

# Simulate Investment
POST /api/v1/index/simulate
{
  "amount": 10000,
  "start_date": "2024-01-01",
  "currency": "USD"
}

# Get Performance Metrics
GET /api/v1/index/performance?period=1Y
```

## 📈 Market Data
```bash
# Get Benchmark
GET /api/v1/benchmark/sp500?start_date=2024-01-01

# Compare Performance
GET /api/v1/benchmark/comparison

# Refresh Market Data
POST /api/v1/background/refresh-market-data
{
  "symbols": ["AAPL", "MSFT"],
  "force": true
}
```

## ⚙️ Strategy Configuration
```bash
# Get Current Strategy
GET /api/v1/strategy/config

# Update Strategy
PUT /api/v1/strategy/config
{
  "rebalance_frequency": "MONTHLY",
  "risk_level": "MODERATE",
  "momentum_weight": 0.4
}

# Trigger Rebalance
POST /api/v1/strategy/rebalance?force=true
```

## 📰 News & Sentiment
```bash
# Get News Articles
GET /api/v1/news/articles?symbols=AAPL,MSFT&limit=10

# Get Sentiment Analysis
GET /api/v1/news/sentiment?symbol=AAPL&period=7D
```

## 🔧 System Operations
```bash
# Health Check
GET /health

# System Status
GET /api/v1/diagnostics/system-health

# Database Status
GET /api/v1/diagnostics/database-status

# Cache Status
GET /api/v1/diagnostics/cache-status
```

## 🎯 Response Formats

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2025-01-19T12:00:00Z"
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Description",
  "error_code": "ERROR_CODE",
  "detail": { ... }
}
```

### Pagination
```json
{
  "data": [...],
  "count": 100,
  "total": 1250,
  "has_more": true
}
```

## 🚀 JavaScript/TypeScript Client
```typescript
// Setup
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

// Get Portfolio
const portfolio = await api.get('/index/current');

// Update Strategy
const result = await api.put('/strategy/config', {
  rebalance_frequency: 'WEEKLY'
});
```

## 🐍 Python Client
```python
import requests

# Setup
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Get Portfolio
response = requests.get(
    'http://localhost:8000/api/v1/index/current',
    headers=headers
)

# Update Strategy
response = requests.put(
    'http://localhost:8000/api/v1/strategy/config',
    json={'rebalance_frequency': 'WEEKLY'},
    headers=headers
)
```

## 📊 Rate Limits
| User Type | Limit | Window |
|-----------|-------|--------|
| Anonymous | 60 | 1 hour |
| Authenticated | 100 | 1 minute |
| Admin | 200 | 1 minute |

## 🔗 Useful Links
- [Full API Docs](http://localhost:8000/docs)
- [OpenAPI Spec](http://localhost:8000/openapi.json)
- [Authentication Guide](../authentication/README.md)
- [Error Codes](../error-codes.md)

---
*Pro tip: Use Postman/Insomnia with our [collection](../postman-collection.json)*