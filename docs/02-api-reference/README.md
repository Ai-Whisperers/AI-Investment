# API Reference

## Overview
Complete API documentation for Waardhaven AutoIndex platform with 150+ endpoints.

## Base Configuration
- **Production**: `https://waardhaven-api.onrender.com`
- **Local**: `http://localhost:8000`
- **Version**: v1 (`/api/v1/`)
- **Auth**: Bearer token (JWT) + Google OAuth

## Quick Navigation

### 📄 Complete References
- **[Full API Reference V2](COMPLETE_API_REFERENCE_V2.md)** - All 150+ endpoints
- **[API Cheatsheet](quick-cards/api-cheatsheet.md)** - Quick reference
- **[Authentication Guide](authentication/README.md)** - Auth implementation

### By Category
- **Authentication** (`/auth/*`) - Login, register, Google OAuth
- **Portfolio** (`/portfolio/*`) - Portfolio management
- **Investment** (`/investment/*`) - Analysis & recommendations
- **Signals** (`/signals/*`, `/momentum/*`) - 38+ signal endpoints
- **News** (`/news/*`) - Multi-source aggregation
- **Monitoring** (`/monitoring/*`) - System health & metrics
- **Diagnostics** (`/diagnostics/*`) - System status

## API Structure

```
/api/v1/
├── /auth/          # Authentication (7 endpoints)
│   ├── /register
│   ├── /login
│   ├── /google      # OAuth redirect
│   └── /google/callback
├── /index/         # Portfolio operations (25 endpoints)
├── /investment/    # Investment analysis (20+ endpoints)
├── /signals/       # Signal detection (38 endpoints)
├── /news/          # News aggregation (10 endpoints)
├── /monitoring/    # System monitoring (15 endpoints)
├── /analysis/      # Technical/fundamental (15 endpoints)
├── /benchmark/     # Market comparison
├── /strategy/      # Strategy config
├── /background/    # Async tasks
├── /tasks/         # Task management
└── /diagnostics/   # System health
```

## Common Patterns

### Request Headers
```http
Authorization: Bearer <token>
Content-Type: application/json
```

### Response Format
```json
{
  "status": "success",
  "data": {},
  "timestamp": "2025-01-19T12:00:00Z"
}
```

### Error Format
```json
{
  "status": "error",
  "message": "Description",
  "error_code": "ERROR_CODE",
  "detail": {}
}
```

## Key Features
- **150+ Endpoints**: Comprehensive API coverage
- **Google OAuth**: Complete authentication flow
- **Real-time Data**: TwelveData and MarketAux integration
- **Signal Detection**: 38 endpoints for extreme alpha
- **News Aggregation**: Multi-source with sentiment analysis
- **Investment Engine**: Technical & fundamental analysis
- **Monitoring**: System health and performance metrics

## Quick Links
- [OpenAPI Spec](https://waardhaven-api.onrender.com/openapi.json)
- [Swagger UI](https://waardhaven-api.onrender.com/docs)
- [ReDoc](https://waardhaven-api.onrender.com/redoc)

---
[← Main Documentation](../README.md)